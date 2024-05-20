from __future__ import annotations
import xml.etree.ElementTree as ET
import dataclasses
from utils.helpers import (
    create_unique_symbol,
    convert_to_bool,
    emit_function,
    BUILTIN_PATTERNS,
)
import os
import re


@dataclasses.dataclass
class FlangConstruct:
    construct_name: str
    attributes: dict
    children: list[str]
    text: str | None
    location: str

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        value = self.attributes.get(key)

        if value is None:
            return default
        return convert_to_bool(value)

    @property
    def pattern(self):
        if hasattr(self, "__pattern"):
            return self.__pattern

        self.__pattern = re.compile(self.text.format(**BUILTIN_PATTERNS))
        return self.__pattern

    @property
    def name(self) -> str | None:
        return self.attributes.get("name")


@dataclasses.dataclass
class FlangObject:
    path: str
    root: str = ""
    symbol_table: dict[str, FlangConstruct] = dataclasses.field(default_factory=dict)

    def find_symbol(self, symbol: str):
        return self.symbol_table[symbol]

    def add_symbol(self, symbol: str, constr: FlangConstruct, override=False):
        if symbol in self.symbol_table and not override:
            raise RuntimeError(f"Symbol {symbol} already exists!")
        self.symbol_table[symbol] = constr

    def iterate_children(self, symbol: str):
        constr = self.find_symbol(symbol)

        for child in constr.children:
            child_constr = self.find_symbol(child)

            if not child_constr.get_bool_attrib("visible", True):
                continue

            yield child_constr

    @property
    def root_construct(self):
        return self.find_symbol(self.root)


@dataclasses.dataclass
class FlangMatchObject:
    symbol: str | None
    content: str | list[FlangMatchObject]
    visible_in_spec: bool = False

    def __len__(self):
        if isinstance(self.content, list):
            return sum(len(child) for child in self.content)
        return len(self.content)

    def to_representation(self):
        if isinstance(self.content, list):
            return (
                self.symbol,
                [
                    child.to_representation()
                    for child in self.content
                    if child.symbol is not None
                ],
            )
        return (self.symbol, self.content)


class MatchNotFound(Exception):
    ...


class FlangTextProcessor:
    def __init__(self, flang_object: FlangObject, stop_on_error: bool = False) -> any:
        self.root = flang_object.root_construct
        self.object = flang_object
        self.stop_on_error = stop_on_error

    def match(
        self, construct: FlangConstruct, text: str, start_position=0
    ) -> FlangMatchObject:
        visible_in_spec = bool(construct.name)
        match_object = None

        match construct.construct_name:
            case "component":
                children = []

                new_position = start_position
                for child in self.object.iterate_children(construct.location):
                    try:
                        while True:
                            match_object = self.match(child, text, new_position)
                            new_position += len(match_object)
                            children.append(match_object)

                            if not child.get_bool_attrib("multi"):
                                break
                    except MatchNotFound as e:
                        construct_optional = child.get_bool_attrib("optional")
                        cannot_find_more_matches = (
                            child.get_bool_attrib("multi")
                            and children
                            and children[-1].symbol == child.location
                        )

                        if construct_optional or cannot_find_more_matches:
                            continue
                        raise e

                return FlangMatchObject(
                    symbol=construct.location,
                    content=children,
                    visible_in_spec=visible_in_spec,
                )
            case "choice":
                children = []
                for child in self.object.iterate_children(construct.location):
                    try:
                        children.append(self.match(child, text, start_position))
                    except MatchNotFound:
                        continue

                if not children:
                    raise MatchNotFound

                return max(children, key=len)
            case "regex":
                matched_text = construct.pattern.match(text, start_position)
                if not matched_text:
                    raise MatchNotFound

                return FlangMatchObject(
                    symbol=construct.location,
                    content=matched_text.group(),
                    visible_in_spec=visible_in_spec,
                )
            case "text":
                if not text.startswith(construct.text, start_position):
                    raise MatchNotFound

                return FlangMatchObject(
                    symbol=construct.location,
                    content=construct.text,
                    visible_in_spec=visible_in_spec,
                )
            case "event":
                name = construct.get_attrib("name", None) or create_unique_symbol(
                    "_flang_function"
                )
                args = construct.get_attrib("args", "").split(",")
                body = construct.text
                emit_function(name, args, body)
            case _:
                raise RuntimeError(f"No such construct {construct.construct_name}")
        

    def _args_builder(self, args):
        return []

    def generate(self, spec: FlangMatchObject) -> str:
        construct = self.object.find_symbol(spec.symbol)

        match construct.construct_name:
            case "component":
                return "".join(self.generate(child_match) for child_match in spec.content)
            case "choice":
                raise RuntimeError
            case "regex":
                return spec.content
            case "text":
                return spec.content

        raise RuntimeError

    def backward(self, spec: FlangMatchObject) -> str:
        return self.generate(spec)

    def forward(self, sample: str) -> FlangMatchObject:
        return self.match(self.root, sample)


class SymbolNotFound(Exception):
    ...


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
            except SymbolNotFound:
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
                raise SymbolNotFound from e
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


DUMMY_TEST_TEMPLATE_CHOICE_1 = """
<component name="import">
<choice>
<component name="first-choice">
<text name="text">AAA</text>
</component>
<component name="second-choice">
<regex name="regex">{vname}</regex>
</component>
<text name="wrong">
THIS IS WRONG
</text>
</choice>
</component>
"""

DUMMY_TEST_TEMPLATE_USE = """
<component name="import">
<component name="foo" visible="false">
<text>AAA</text>
</component>
<component name="bar">
<use ref="..foo"/>
</component>
</component>
"""

DUMMY_TEST_TEMPLATE_MULTI = r"""
<component name="import">
<component name="header" multi="true">
<text multi="true">AAA</text>
<regex>\s</regex>
</component>
<component name="variable" multi="true">
<text value="variable: "/><regex name="name" value="{vname}"/><regex value=";\n?"/>
</component>
</component>
"""

DUMMY_TEST_TEMPLATE_EVENT = """
<component name="code">
<component name="import">
<text value="import "/><regex value="{vname}"/><text value="\\n"/>
</component>
<component name="function-call" on-create=".">
<event args="tree">
print("hello world")
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</component>
</component>
"""

SAMPLE_CHOICE = "AAAAAA"
SPEC_EVENT = None

SAMPLE_MULTI = """\
AAAAAAAAAAAA
AAA
AAAAAA
variable: somevalue;
variable: someothervalue;\
"""

DUMMY_TEST_TEMPLATE_EVENT = """
<component name="code">
<component name="import">
<text value="import "/><regex value="{vname}"/><text value="\\n"/>
</component>
<component name="function-call" on-create=".">
<event args="tree">
print("hello world")
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</component>
</component>
"""


def main():
    parser = FlangXMLParser()
    # flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_CHOICE_1)
    # print(flang_object)
    # processor = FlangTextProcessor(flang_object)
    # match_obj = processor.backward(SAMPLE_CHOICE)
    # print()
    # print(match_obj)
    # generated = processor.forward(match_obj)
    # print()
    # print(generated)

    # flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_EVENT)
    # processor = FlangTextProcessor(flang_object)
    # print(processor.forward)
    # generated = processor.forward(SPEC_EVENT)
    # print(generated)

    # print()
    # parser.clear()
    flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_MULTI)
    processor = FlangTextProcessor(flang_object)
    match_obj = processor.forward(SAMPLE_MULTI)
    print(match_obj)
    generated = processor.backward(match_obj)
    print(generated)


if __name__ == "__main__":
    main()
