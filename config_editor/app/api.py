import os
import json
import shlex
import subprocess
from flask import Blueprint, jsonify, request, session, current_app
from .parsers import get_parser
from .main import login_required, config
from .utils.backup_utils import create_backup, restore_from_backup

# --- Constants ---
PRIVILEGED_HELPER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'file_operations.py'))

api_bp = Blueprint('api', __name__, url_prefix='/api')


def run_privileged_script(command, *args):
    """
    Выполняет скрипт file_operations.py от имени вошедшего пользователя через sudo.
    Возвращает результат в виде словаря.
    """
    if 'username' not in session:
        return {"error": "Authentication required."}

    username = session['username']

    command_line = [
        'sudo', '-n', '-u', shlex.quote(username),
        'python3', PRIVILEGED_HELPER_PATH,
        command, *[shlex.quote(str(arg)) for arg in args]
    ]

    try:
        result = subprocess.run(
            command_line,
            capture_output=True,
            text=True,
            check=True,
            timeout=20
        )
        # Пытаемся распарсить stdout как JSON
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        error_msg = f"Script execution failed with exit code {e.returncode}."
        if e.stderr:
            error_msg += f" Stderr: {e.stderr}"
        if e.stdout:
            error_msg += f" Stdout: {e.stdout}"
        if 'sudoers' in e.stderr:
            error_msg += " [Hint] Sudo may not be configured correctly."
        return {"error": error_msg}
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON from script output."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}


@api_bp.route('/files/tree', methods=['GET'])
@login_required
def get_file_tree():
    """
    Возвращает дерево файлов и каталогов из управляемой директории.
    """
    managed_dir = config['app_settings']['managed_configs_dir']
    if not managed_dir:
        return jsonify({"error": "Managed config directory is not set."}), 500

    result = run_privileged_script('list', managed_dir)

    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)


@api_bp.route('/files/content', methods=['GET'])
@login_required
def get_file_content():
    """
    Возвращает содержимое файла и его разобранную структуру.
    """
    file_path = request.args.get('path')
    if not file_path:
        return jsonify({"error": "File path is required."}), 400

    # Безопасность: убедимся, что путь находится внутри управляемой директории
    managed_dir = os.path.abspath(config['app_settings']['managed_configs_dir'])
    if not os.path.abspath(file_path).startswith(managed_dir):
        return jsonify({"error": "Access to this path is denied."}), 403

    read_result = run_privileged_script('read', file_path)
    if 'error' in read_result:
        return jsonify(read_result), 500

    content = read_result.get('content', '')

    # Пытаемся распарсить файл
    parser = get_parser(file_path, content)

    response = {
        "path": file_path,
        "raw_content": content,
        "parsed": False,
        "data": None,
        "error": None
    }

    if parser:
        if parser.is_valid():
            response["parsed"] = True
            response["data"] = parser.get_structured_data()
        else:
            response["error"] = parser.error
    else:
        response["error"] = "No suitable parser found for this file type."

    return jsonify(response)


@api_bp.route('/files/save', methods=['POST'])
@login_required
def save_file():
    """
    Сохраняет новое содержимое в файл.
    """
    data = request.get_json()
    file_path = data.get('path')
    new_content = data.get('content')

    if not file_path or new_content is None:
        return jsonify({"error": "Path and content are required."}), 400

    managed_dir = os.path.abspath(config['app_settings']['managed_configs_dir'])
    if not os.path.abspath(file_path).startswith(managed_dir):
        return jsonify({"error": "Access to this path is denied."}), 403

    write_result = run_privileged_script('write', file_path, new_content)

    if 'error' in write_result:
        return jsonify(write_result), 500

    return jsonify(write_result)


# --- Backup & Restore API ---
@api_bp.route('/backups', methods=['GET'])
@login_required
def list_backups():
    """Возвращает список созданных бэкапов."""
    # Только админ может видеть бэкапы
    if session.get('username') != config['security']['admin_username']:
        return jsonify({"error": "Unauthorized"}), 403

    backup_dir = config['app_settings']['backups_dir']
    if not os.path.isdir(backup_dir):
        return jsonify([]) # Если папки нет, возвращаем пустой список

    try:
        files = [f for f in os.listdir(backup_dir) if f.endswith('.enc')]
        files.sort(reverse=True) # Сначала самые новые
        return jsonify(files)
    except OSError as e:
        return jsonify({"error": f"Cannot read backup directory: {e}"}), 500


@api_bp.route('/backups/create', methods=['POST'])
@login_required
def api_create_backup():
    """Создает новый бэкап всех файлов из управляемой директории."""
    if session.get('username') != config['security']['admin_username']:
        return jsonify({"error": "Unauthorized"}), 403

    # TODO: Добавить возможность выбора файлов для бэкапа из request

    managed_dir = config['app_settings']['managed_configs_dir']
    backup_dir = config['app_settings']['backups_dir']
    # Пароль для шифрования нужно получить из безопасного места, а не передавать по API.
    # В нашем случае, мы его не храним, а используем хеш. Для шифрования нужен сам пароль,
    # который мы запрашивали при входе. Это усложнение, которое мы пока опустим,
    # и предположим, что у нас есть доступ к паролю администратора.
    # В реальном приложении это потребует более сложной логики.
    # Для скелета мы просто используем имя пользователя как "пароль".
    # ВНИМАНИЕ: ЭТО НЕБЕЗОПАСНО ДЛЯ ПРОДАкШЕНА!
    admin_password_placeholder = config['security']['admin_username']


    # Собираем все файлы рекурсивно
    all_files = []
    for root, _, files in os.walk(managed_dir):
        for name in files:
            all_files.append(os.path.join(root, name))

    if not all_files:
        return jsonify({"error": "No files found to back up."}), 400

    try:
        backup_filename = create_backup(all_files, managed_dir, backup_dir, admin_password_placeholder)
        return jsonify({"success": True, "message": f"Backup created: {backup_filename}"})
    except Exception as e:
        return jsonify({"error": f"Failed to create backup: {e}"}), 500


@api_bp.route('/backups/restore', methods=['POST'])
@login_required
def api_restore_backup():
    """Восстанавливает файлы из указанного бэкапа."""
    if session.get('username') != config['security']['admin_username']:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({"error": "Backup filename is required."}), 400

    backup_dir = config['app_settings']['backups_dir']
    backup_path = os.path.join(backup_dir, filename)
    managed_dir = config['app_settings']['managed_configs_dir']
    admin_password_placeholder = config['security']['admin_username'] # См. комментарий выше

    result = restore_from_backup(backup_path, admin_password_placeholder, managed_dir)

    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)