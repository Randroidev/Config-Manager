import json
from .base_parser import BaseParser

class JsonParser(BaseParser):
    def read(self, file_path: str) -> dict:
        """Reads a JSON file and returns its content as a dictionary."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file: {e}")
        except FileNotFoundError:
            raise

    def write(self, file_path: str, data: dict):
        """Writes a dictionary to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
