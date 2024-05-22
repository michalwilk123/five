from __future__ import annotations

import dataclasses
import re
import typing
import pathlib
import atexit
from collections.abc import Sequence

from flang.helpers import BUILTIN_PATTERNS, convert_to_bool


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
    def visible(self):
        return self.get_bool_attrib("visible", True)
    
    @visible.setter
    def visible(self, value:bool):
        self.attributes["visible"] = value

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

    def find_symbol(self, symbol: str) -> FlangConstruct:
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
    def root_construct(self) -> FlangConstruct:
        return self.find_symbol(self.root)


@dataclasses.dataclass
class FlangStructuredText:
    symbol: str | None
    content: str | list[FlangStructuredText]
    visible_in_spec: bool = False

    def __len__(self):
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    
    def get_construct(self, flang_object: FlangObject) -> FlangConstruct:
        return flang_object.find_symbol(self.symbol)
    
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


@dataclasses.dataclass
class IntermediateFileObject:
    content: typing.IO[str] | Sequence[IntermediateFileObject]
    path: pathlib.Path

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        atexit.register(self.cleanup)

    def cleanup(self):
        if not isinstance(self.content, Sequence) and not self.content.closed:
            self.content.close()

    @classmethod
    def from_path(cls, path:str):
        path_object = pathlib.Path(path)

        assert path_object.exists()

        if path_object.is_dir():
            content = [cls.from_path(child_path) for child_path in path_object.iterdir()]
        else:
            content = open(path_object)
        
        return cls(content=content, path=path_object)

    def write(self):
        ...

