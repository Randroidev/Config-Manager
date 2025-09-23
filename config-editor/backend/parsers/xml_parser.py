import xml.etree.ElementTree as ET
from .base_parser import BaseParser

class XmlParser(BaseParser):
    def _etree_to_dict(self, t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = {}
            for dc in map(self._etree_to_dict, children):
                for k, v in dc.items():
                    if k in dd:
                        if not isinstance(dd[k], list):
                            dd[k] = [dd[k]]
                        dd[k].append(v)
                    else:
                        dd[k] = v
            d = {t.tag: dd}
        if t.attrib:
            d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
        if t.text and t.text.strip():
            if children or t.attrib:
                d[t.tag]['#text'] = t.text
            else:
                d[t.tag] = t.text
        return d

    def _dict_to_etree(self, d):
        def build_node(tag, data):
            elem = ET.Element(tag)
            if isinstance(data, dict):
                for key, val in data.items():
                    if key.startswith('@'):
                        elem.set(key[1:], str(val))
                    elif key == '#text':
                        elem.text = str(val)
                    elif isinstance(val, list):
                        for item in val:
                            elem.append(build_node(key, item))
                    else:
                        elem.append(build_node(key, val))
            else:
                elem.text = str(data)
            return elem

        if len(d) != 1:
            raise ValueError("Input dictionary for XML conversion must have a single root element.")

        root_tag = list(d.keys())[0]
        root_data = d[root_tag]
        return build_node(root_tag, root_data)

    def read(self, file_path: str) -> dict:
        """Reads an XML file and converts it to a dictionary."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._etree_to_dict(root)
        except ET.ParseError as e:
            raise ValueError(f"Error parsing XML file: {e}")

    def write(self, file_path: str, data: dict):
        """Writes a dictionary to an XML file."""
        try:
            root = self._dict_to_etree(data)
            tree = ET.ElementTree(root)
            # This makes the output more human-readable
            ET.indent(tree, space="\t", level=0)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            raise ValueError(f"Error writing XML file: {repr(e)}")
