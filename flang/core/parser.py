from __future__ import annotations
from utils.dataclasses import (
    BaseFlangConstruct,
    FlangObject,
    IntermediateFlangTreeElement,
)
from utils.abstracts import (
    TextToIntermediateTreeParser,
    SingleFileParser,
)
import utils.constructs as c
import warnings
import os
from .intermediate import FlangXMLParser
from utils.helpers import create_unique_symbol


class FlangStandardParser(SingleFileParser):
    CONSTRUCTS = {
        constr.name: constr
        for constr in [
            c.FlangComponent,
            c.FlangPredicate,
            c.FlangRawText,
            c.FlangRawRegex,
            c.FlangChoice,
            c.FlangReference,
            c.FlangRule,
        ]
    }

    def get_constructs_classes(self) -> dict[str, BaseFlangConstruct]:
        return super().get_constructs_classes()

    def _generate_construct_path(
        self, parent: str, intermediate_tree: IntermediateFlangTreeElement
    ) -> str:
        symbol = intermediate_tree.attributes.get("name") or create_unique_symbol(
            intermediate_tree.name
        )

        if not parent:
            return symbol

        return f"{parent}.{symbol}"

    def _build_construct(
        self,
        flang_object: FlangObject,
        intermediate_tree: IntermediateFlangTreeElement,
        location="",
    ):
        construct_class = self.CONSTRUCTS[intermediate_tree.name]
        construct_path = self._generate_construct_path(location, intermediate_tree)

        if isinstance(intermediate_tree.value, list):
            children = [
                self._build_construct(flang_object, child, construct_path)
                for child in intermediate_tree.value
            ]
        else:
            children = intermediate_tree.value

        construct_obj = construct_class(
            children_or_value=children,
            attributes=intermediate_tree.attributes,
            location=construct_path,
        )
        assert isinstance(construct_obj, BaseFlangConstruct)

        if not location:
            flang_object.root = construct_path

        flang_object.symbols[construct_path] = construct_obj

        return construct_obj

    def parse(self, intermediate_tree: IntermediateFlangTreeElement) -> FlangObject:
        flang_object = FlangObject()
        self._build_construct(flang_object, intermediate_tree)
        return flang_object


class FlangParser:
    def __init__(self) -> None:
        self.intermediate_parser: TextToIntermediateTreeParser = FlangXMLParser()
        self.single_file_parser_class: SingleFileParser = FlangStandardParser
        self.single_file_parsers: dict = {}
        self.symbol_table = {}

    def parse_text(self, text: str, path: str | None = None, evaluate: bool = True):
        path = path or os.getcwd()
        intermediate_tree = self.intermediate_parser.parse(text)
        assert intermediate_tree.name == "component"  # sanity check

        # self._evaluate_intermediate_tree(intermediate_tree)

        subparser = FlangStandardParser()
        self.single_file_parsers[path] = subparser
        flang_object = subparser.parse(intermediate_tree)
        global_symbols = self.translate_local_symbol_table_to_global(
            flang_object.symbols, path
        )

        assert (
            not self.symbol_table.keys() & global_symbols.keys()
        ), "Symbols are repeating! Possible recursive import"
        self.symbol_table.update(global_symbols)

        for dependency in flang_object.external_dependencies:
            if dependency not in self.symbol_table:
                source, _ = dependency.split(":")
                self.parse_file(source, evaluate=False)

        if evaluate:
            # This is the file we return to user.
            # We should perform optimizations and stuff
            self.perform_optimizations(flang_object)

        return flang_object

    def parse_file(self, filepath: str, evaluate: bool = True):
        with open(filepath) as f:
            return self.parse_text(f.read(), filepath, evaluate)

    def translate_local_symbol_table_to_global(
        self, symbol_table: dict, path: str
    ) -> dict:
        return {f"{path}:{symbol}": value for symbol, value in symbol_table.items()}

    def _evaluate_intermediate_tree(self, intermediate: IntermediateFlangTreeElement):
        ...

    def perform_optimizations(self, root: FlangObject):
        warnings.warn("Optimizations not implemented!")
