import json
from .base_parser import BaseParser

class JsonParser(BaseParser):
    """Парсер для файлов формата JSON."""

    def parse(self):
        """
        Парсит JSON-строку в Python-объект (словарь или список).
        """
        if not self.file_content.strip():
            # Если файл пустой, считаем его пустым словарем
            return {}
        return json.loads(self.file_content)

    def to_string(self):
        """
        Преобразует Python-объект обратно в форматированную JSON-строку.
        """
        if self.data is None:
            return ""
        return json.dumps(self.data, indent=4, ensure_ascii=False)