import configparser
from io import StringIO
from .base_parser import BaseParser

class IniParser(BaseParser):
    """
    Парсер для файлов формата INI, CONF, CFG.
    Использует `configparser` и добавляет логику для автоопределения типов.
    """

    def parse(self):
        """
        Парсит INI-файл в словарь словарей.
        """
        config = configparser.ConfigParser(interpolation=None)
        # ConfigParser требует, чтобы у файла был хотя бы один раздел.
        # Если его нет, он вызовет исключение. Мы обернем контент в
        # фиктивный раздел, если это необходимо.
        content_to_parse = self.file_content
        if not content_to_parse.strip().startswith('['):
             content_to_parse = "[DUMMY_SECTION]\n" + content_to_parse

        config.read_string(content_to_parse)

        output_dict = {}
        for section in config.sections():
            output_dict[section] = {}
            for key, value in config.items(section):
                output_dict[section][key] = self._auto_type_value(value)

        return output_dict

    def to_string(self):
        """
        Преобразует словарь обратно в INI-формат.
        """
        if self.data is None:
            return ""

        config = configparser.ConfigParser(interpolation=None)
        config.read_dict(self.data)

        string_io = StringIO()
        config.write(string_io)

        # Удаляем фиктивный раздел, если он был
        output_string = string_io.getvalue()
        if "[DUMMY_SECTION]\n" in output_string:
            output_string = output_string.replace("[DUMMY_SECTION]\n", "", 1)

        return output_string

    def _auto_type_value(self, value):
        """
        Пытается преобразовать строковое значение в число или булево.
        """
        if value.lower() in ['true', 'yes', 'on']:
            return True
        if value.lower() in ['false', 'no', 'off']:
            return False

        # Проверка на целое число
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return int(value)

        # Проверка на число с плавающей точкой
        try:
            return float(value)
        except (ValueError, TypeError):
            pass

        # Если ничего не подошло, возвращаем как строку
        return value