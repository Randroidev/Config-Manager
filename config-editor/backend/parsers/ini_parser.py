import configparser
from .base_parser import BaseParser

class IniParser(BaseParser):
    def read(self, file_path: str) -> dict:
        """Reads an INI file and returns its content as a dictionary."""
        config = configparser.ConfigParser()
        try:
            config.read(file_path)
            data = {section: dict(config.items(section)) for section in config.sections()}
            return data
        except configparser.Error as e:
            # Here we can decide how to handle parsing errors.
            # For now, we'll raise an exception that the main app can catch.
            raise ValueError(f"Error parsing INI file: {e}")

    def write(self, file_path: str, data: dict):
        """Writes a dictionary to an INI file."""
        config = configparser.ConfigParser()
        config.read_dict(data)
        with open(file_path, 'w') as configfile:
            config.write(configfile)
