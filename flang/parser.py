import os
import xml.etree.ElementTree as ET

from flang.helpers import create_unique_symbol
from flang.structures import FlangConstruct, FlangObject


class FlangXMLParser:
    def __init__(self) -> None:
        super().__init__()
        self.object_dict: dict[str, FlangObject] = {}

    @staticmethod
    def get_file_from_path(location: str):
        return location.split(":")[0]

    def clear(self):
        self.object_dict: dict[str, FlangObject] = {}

    def generate_symbol(self, element: ET.Element, location: str, path: str):
        symbol = element.attrib.get("name") or element.tag
        symbol = f"{location}.{symbol}" if location else f"{path}:{symbol}"
        if element.attrib.get("name"):
            return symbol
        return create_unique_symbol(symbol)

    def _build_tree(
        self,
        element: ET.Element | str,
        flang_object: FlangObject,
        location: str = "",
    ) -> FlangConstruct:
        symbol = self.generate_symbol(element, location, flang_object.path)

        children = [self._build_tree(child, flang_object, symbol) for child in element]

        construct = FlangConstruct(
            construct_name=element.tag,
            attributes=element.attrib or {},
            children=[
                child.location
                for child in children
                if child.get_bool_attrib("visible", True)
            ],
            text=element.text or element.attrib.get("value"),
            location=symbol,
        )
        flang_object.add_symbol(symbol, construct)

        return construct

    def parse_text(self, text: str, path: str = None) -> FlangObject:
        path = path or os.getcwd()

        processed_xml = ET.fromstring(text)
        self.object_dict[path] = flang_object = FlangObject(path=path)
        construct = self._build_tree(processed_xml, flang_object)
        flang_object.root = construct.location

        return flang_object

    def parse_file(self, filepath: str):
        with open(filepath) as f:
            return self.parse_text(f.read(), filepath)
