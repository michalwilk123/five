import re
import xml.etree.ElementTree as ET

from flang.structures import FlangAST
from flang.utils.attributes import get_possible_construct_attributes
from flang.utils.exceptions import UnknownAttributeException


def get_file_from_path(location: str):
    return location.split(":")[0]


def validate_attributes_for_xml_element(
    element: ET.Element,
):
    possible_attributes = get_possible_construct_attributes(element.tag)
    not_validated_attributes = []

    for key in element.attrib:
        correct = False

        for attr in possible_attributes:
            if isinstance(attr, re.Pattern) and attr.match(key):
                correct = True
                break
            elif attr == key:
                correct = True
                break

        if not correct:
            not_validated_attributes.append(key)

    if not_validated_attributes:
        raise UnknownAttributeException(
            "Construct: {} has unknown attributes: {}".format(
                element.tag, not_validated_attributes
            )
        )


def _build_tree(
    element: ET.Element,
    validate_attributes: bool,
) -> FlangAST:
    node_name = element.attrib.get("name", element.tag)

    if validate_attributes:
        validate_attributes_for_xml_element(element)

    children = [
        _build_tree(child_element, validate_attributes) for child_element in element
    ]
    construct = FlangAST(
        name=node_name,
        type=element.tag,
        attributes=element.attrib or {},
        children=children,
        text=element.text or element.attrib.get("value"),
    )
    return construct


def parse_text(text: str, validate_attributes: bool = False) -> FlangAST:
    processed_xml = ET.fromstring(text)
    return _build_tree(processed_xml, validate_attributes)


def parse_file(filepath: str):
    with open(filepath) as f:
        return parse_text(f.read(), filepath)
