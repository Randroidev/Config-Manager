#!/usr/bin/env python3

import os
import sys
import json
import stat

def check_permissions(path):
    """Проверяет права доступа к файлу или директории."""
    try:
        s = os.stat(path)
        return {
            "readable": os.access(path, os.R_OK),
            "writable": os.access(path, os.W_OK),
            "executable": os.access(path, os.X_OK),
            "is_dir": stat.S_ISDIR(s.st_mode),
        }
    except FileNotFoundError:
        return None

def list_files(base_path):
    """
    Рекурсивно сканирует директорию и возвращает дерево файлов и папок
    с информацией о правах доступа.
    """
    if not os.path.isdir(base_path):
        return {"error": f"Path is not a valid directory: {base_path}"}

    tree = []
    try:
        for entry in os.scandir(base_path):
            perms = check_permissions(entry.path)
            node = {
                "name": entry.name,
                "path": entry.path,
                "permissions": perms,
            }
            if entry.is_dir(follow_symlinks=False):
                node["type"] = "directory"
                node["children"] = list_files(entry.path) # Рекурсивный вызов
            else:
                node["type"] = "file"
            tree.append(node)
        # Сортировка: сначала папки, потом файлы, все по алфавиту
        tree.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))
        return tree
    except OSError as e:
        return {"error": f"Cannot access path {base_path}: {e}"}

def read_file(path):
    """Читает содержимое файла."""
    if not os.path.exists(path) or os.path.isdir(path):
        return {"error": f"File not found or is a directory: {path}"}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return {"content": f.read()}
    except Exception as e:
        return {"error": f"Could not read file: {e}"}

def write_file(path, content):
    """Записывает содержимое в файл."""
    if os.path.isdir(path):
        return {"error": f"Path is a directory, cannot write: {path}"}
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "message": f"File saved successfully: {path}"}
    except Exception as e:
        return {"error": f"Could not write to file: {e}"}

def main():
    """Главная функция для обработки команд."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided."}), file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    # Отключаем вывод print в stderr, чтобы не засорять ошибки JSON
    sys.stderr = open(os.devnull, 'w')

    try:
        if command == "list":
            if len(sys.argv) != 3:
                result = {"error": "List command requires a path argument."}
            else:
                path = sys.argv[2]
                result = list_files(path)

        elif command == "read":
            if len(sys.argv) != 3:
                result = {"error": "Read command requires a path argument."}
            else:
                path = sys.argv[2]
                result = read_file(path)

        elif command == "write":
            if len(sys.argv) != 4:
                result = {"error": "Write command requires a path and content argument."}
            else:
                path = sys.argv[2]
                content = sys.argv[3]
                result = write_file(path, content)

        else:
            result = {"error": f"Unknown command: {command}"}

        print(json.dumps(result))
        if "error" in result:
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": f"An unexpected error occurred: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()