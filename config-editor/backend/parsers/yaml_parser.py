import yaml
from .base_parser import BaseParser

class YamlParser(BaseParser):
    def read(self, file_path: str) -> dict:
        """Reads a YAML file and returns its content as a dictionary."""
        try:
            with open(file_path, 'r') as f:
                # safe_load is recommended for security.
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")
        except FileNotFoundError:
            raise

    def write(self, file_path: str, data: dict):
        """Writes a dictionary to a YAML file."""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
