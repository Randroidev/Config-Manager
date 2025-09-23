from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def read(self, file_path: str) -> dict:
        """Reads and parses the file content into a dictionary."""
        pass

    @abstractmethod
    def write(self, file_path: str, data: dict):
        """Writes the dictionary data back to the file."""
        pass
