import os
from .base_parser import BaseParser
# Импорты конкретных парсеров
from .ini_parser import IniParser
from .json_parser import JsonParser
from .yaml_parser import YamlParser
# ... и так далее

# Словарь для сопоставления расширений файлов с классами парсеров
PARSER_MAPPING = {
    '.ini': IniParser,
    '.conf': IniParser,
    '.cfg': IniParser,
    '.config': IniParser,
    '.json': JsonParser,
    '.yaml': YamlParser,
    '.yml': YamlParser,
    # '.toml': TomlParser,
    # '.properties': PropertiesParser,
    # '.env': EnvParser,
    # '.xml': XmlParser,
}

def get_parser(file_path, file_content):
    """
    Фабричная функция для получения нужного экземпляра парсера.

    :param file_path: Путь к файлу, чтобы определить расширение.
    :param file_content: Содержимое файла для передачи в парсер.
    :return: Экземпляр соответствующего парсера или None, если парсер не найден.
    """
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    parser_class = PARSER_MAPPING.get(extension)

    if parser_class:
        return parser_class(file_content, file_path)

    return None