import os
import zipfile
import io
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# --- Криптографические константы ---
SALT_SIZE = 16
TAG_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256-bit key for AES
PBKDF2_ITERATIONS = 390000


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Генерирует криптографический ключ из пароля и соли.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    return kdf.derive(password.encode('utf-8'))


def create_backup(file_paths: list, base_dir: str, backup_dir: str, password: str) -> str:
    """
    Создает зашифрованный ZIP-архив с указанными файлами.

    :param file_paths: Список путей к файлам для бэкапа.
    :param base_dir: Базовый каталог, от которого будут сохраняться пути в архиве.
    :param backup_dir: Каталог для сохранения файла бэкапа.
    :param password: Пароль администратора для шифрования.
    :return: Имя созданного файла бэкапа.
    """
    # 1. Создаем ZIP-архив в памяти
    zip_in_memory = io.BytesIO()
    with zipfile.ZipFile(zip_in_memory, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in file_paths:
            # Сохраняем относительный путь, чтобы избежать проблем при восстановлении
            archive_path = os.path.relpath(file_path, base_dir)
            zf.write(file_path, arcname=archive_path)

    zip_data = zip_in_memory.getvalue()

    # 2. Шифруем данные
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)

    encrypted_data = aesgcm.encrypt(nonce, zip_data, None)  # associated_data = None

    # 3. Сохраняем в файл (соль + nonce + зашифрованные данные)
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = f"backup_{timestamp}.enc"
    backup_filepath = os.path.join(backup_dir, backup_filename)

    with open(backup_filepath, 'wb') as f:
        f.write(salt)
        f.write(nonce)
        f.write(encrypted_data) # tag автоматически добавляется в конец

    return backup_filename


def restore_from_backup(backup_path: str, password: str, target_dir: str) -> dict:
    """
    Восстанавливает файлы из зашифрованного бэкапа.

    :param backup_path: Путь к файлу бэкапа.
    :param password: Пароль для расшифровки.
    :param target_dir: Директория для восстановления файлов.
    :return: Словарь с результатом операции.
    """
    try:
        # 1. Читаем зашифрованный файл
        with open(backup_path, 'rb') as f:
            salt = f.read(SALT_SIZE)
            nonce = f.read(NONCE_SIZE)
            encrypted_data = f.read() # Остальное - данные + tag

        # 2. Расшифровываем
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)

        decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)

        # 3. Распаковываем ZIP из памяти
        zip_in_memory = io.BytesIO(decrypted_data)

        # Проверка, что все пути внутри целевого каталога (безопасность!)
        abs_target_dir = os.path.abspath(target_dir)
        with zipfile.ZipFile(zip_in_memory, 'r') as zf:
            for member in zf.infolist():
                restored_path = os.path.abspath(os.path.join(abs_target_dir, member.filename))
                if not restored_path.startswith(abs_target_dir):
                    raise ValueError(f"Attempted to extract file outside target directory: {member.filename}")
            # Если все в порядке, распаковываем
            zf.extractall(abs_target_dir)

        return {"success": True, "message": f"Restored successfully from {os.path.basename(backup_path)}."}

    except FileNotFoundError:
        return {"error": "Backup file not found."}
    except ValueError as e:
        # Это может быть ошибка аутентификации (неверный пароль) или ошибка пути
        return {"error": f"Failed to decrypt or restore. Check password or backup file integrity. Details: {e}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred during restore: {e}"}