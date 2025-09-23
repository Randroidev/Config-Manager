import os
from .ini_parser import IniParser
from .json_parser import JsonParser
from .xml_parser import XmlParser
from .yaml_parser import YamlParser

# Mapping of file extensions to parser classes
PARSER_MAPPING = {
    '.ini': IniParser,
    '.cfg': IniParser,
    '.conf': IniParser,
    '.config': IniParser,
    '.json': JsonParser,
    '.xml': XmlParser,
    '.yml': YamlParser,
    '.yaml': YamlParser,
}

def get_parser(file_path):
    """
    Factory function to get the appropriate parser for a file.
    """
    _, extension = os.path.splitext(file_path)
    parser_class = PARSER_MAPPING.get(extension.lower())
    if parser_class:
        return parser_class()
    else:
        raise ValueError(f"No parser found for file extension: {extension}")
