import yaml
from .base_parser import BaseParser

class YamlParser(BaseParser):
    """Парсер для файлов формата YAML."""

    def parse(self):
        """
        Парсит YAML-строку в Python-объект.
        """
        if not self.file_content.strip():
            return {}
        # safe_load используется для безопасности, чтобы избежать выполнения кода
        return yaml.safe_load(self.file_content)

    def to_string(self):
        """
        Преобразует Python-объект обратно в YAML-строку.
        """
        if self.data is None:
            return ""
        # `sort_keys=False` сохраняет порядок ключей, что важно для конфигурационных файлов.
        # `allow_unicode=True` для корректной работы с не-ASCII символами.
        return yaml.dump(self.data, sort_keys=False, allow_unicode=True, indent=2)