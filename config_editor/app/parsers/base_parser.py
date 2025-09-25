from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    Абстрактный базовый класс для всех парсеров конфигурационных файлов.
    Определяет общий интерфейс для парсинга, представления и сохранения данных.
    """

    def __init__(self, file_content, file_path=None):
        """
        Инициализирует парсер.

        :param file_content: Строка с содержимым файла для парсинга.
        :param file_path: (Опционально) Путь к файлу, может быть полезен для некоторых парсеров.
        """
        self.file_content = file_content
        self.file_path = file_path
        self.data = None
        self.error = None
        try:
            self.data = self.parse()
        except Exception as e:
            self.error = f"Failed to parse file. Error: {str(e)}"

    @abstractmethod
    def parse(self):
        """
        Парсит `self.file_content` и возвращает структурированное представление данных
        (например, словарь или список словарей).
        В случае ошибки должен выбрасывать исключение.
        """
        pass

    @abstractmethod
    def to_string(self):
        """
        Преобразует `self.data` обратно в строковое представление, готовое для записи в файл.
        """
        pass

    def is_valid(self):
        """
        Возвращает True, если парсинг прошел без ошибок.
        """
        return self.error is None

    def get_structured_data(self):
        """
        Возвращает разобранные данные.
        """
        return self.data