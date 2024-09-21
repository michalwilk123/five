import collections
import os
import xml.etree.ElementTree as ET

from flang.exceptions import UnknownAttributeException

# from flang.helpers import create_unique_symbol
from flang.structures import FlangConstruct, FlangProjectConstruct
from flang.utils import get_possible_construct_attributes


class FlangXMLParser:
    @staticmethod
    def get_file_from_path(location: str):
        return location.split(":")[0]

    def _build_tree(
        self,
        element: ET.Element,
        flang_object: FlangProjectConstruct,
        validate_attributes: bool,
        location: str = "",
    ) -> FlangConstruct:
        location = flang_object.generate_symbol_for_construct(
            element.attrib.get("name") or element.tag, location
        )

        if validate_attributes:
            not_validated_attributes = [
                key
                for key in element.attrib
                if key not in get_possible_construct_attributes(element.tag)
            ]
            if not_validated_attributes:
                raise UnknownAttributeException(
                    "Construct: {} has unknown attributes: {}".format(
                        element.tag, not_validated_attributes
                    )
                )

        children = [
            self._build_tree(
                child,
                flang_object,
                validate_attributes=validate_attributes,
                location=location,
            )
            for child in element
        ]
        construct = FlangConstruct(
            name=element.tag,
            attributes=element.attrib or {},
            children=[
                child.location
                for child in children
                if child.get_bool_attrib("visible", True)
            ],
            text=element.text or element.attrib.get("value"),
            location=location,
        )
        flang_object.add_symbol(location, construct)

        return construct

    def parse_text(
        self, text: str, path: str = "", validate_attributes: bool = False
    ) -> FlangProjectConstruct:
        path = path or os.getcwd()

        processed_xml = ET.fromstring(text)
        flang_object = FlangProjectConstruct(path=path)
        construct = self._build_tree(processed_xml, flang_object, validate_attributes)
        flang_object.root = construct.location

        return flang_object

    def parse_file(self, filepath: str):
        with open(filepath) as f:
            return self.parse_text(f.read(), filepath)
