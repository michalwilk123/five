import copy
import os
import xml.etree.ElementTree as ET

from flang.exceptions import SymbolNotFoundError
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

    def _evaluate_construct(self, flang_object: FlangObject, construct: FlangConstruct):
        if construct.construct_name == "use":
            target_location = construct.get_attrib("ref")
            location = construct.location

            try:
                target = self.find_construct_by_path(target_location, location)
                target = copy.deepcopy(target)

                if not target.visible:
                    target.visible = True

            except SymbolNotFoundError:
                self.parse_file(self.get_file_from_path(target_location))

            flang_object.add_symbol(construct.location, target, override=True)

    def generate_symbol(self, element: ET.Element, location: str, path: str):
        symbol = element.attrib.get("name") or element.tag
        symbol = f"{location}.{symbol}" if location else f"{path}:{symbol}"
        if element.attrib.get("name"):
            return symbol
        return create_unique_symbol(symbol)

    def find_construct_by_path(
        self, reference_path: str, current_path: str = ""
    ) -> FlangConstruct:
        is_symbol_external = ":" in reference_path
        is_symbol_relative = reference_path.startswith(".") and not is_symbol_external

        if is_symbol_relative and not current_path:
            raise RuntimeError

        if is_symbol_external:
            try:
                filename = self.get_file_from_path(reference_path)
                flang_object = self.object_dict[filename]
                return flang_object.find_symbol(reference_path)
            except KeyError as e:
                raise SymbolNotFoundError from e
        elif is_symbol_relative:
            path_without_dots = reference_path.lstrip(".")
            backward_steps = len(reference_path) - len(path_without_dots)

            filename, local_path = current_path.split(":")
            target_path = "%s.%s" % (
                ".".join(local_path.split(".")[:-backward_steps]),
                path_without_dots,
            )
            full_target_path = "%s:%s" % (filename, target_path)
            return self.find_construct_by_path(full_target_path)

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
        self._evaluate_construct(flang_object, construct)

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
