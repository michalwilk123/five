from __future__ import annotations

import atexit
import dataclasses
import io
import pathlib
import re
import typing
from collections.abc import Sequence
from functools import cached_property

from flang.helpers import BUILTIN_PATTERNS, convert_to_bool


@dataclasses.dataclass
class FlangConstruct:
    construct_name: str
    attributes: dict
    children: list[FlangConstruct]
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
    def visible(self, value: bool):
        self.attributes["visible"] = value

    @cached_property
    def pattern(self):
        return re.compile(self.text.format(**BUILTIN_PATTERNS))

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
class FlangTextMatchObject:
    symbol: str
    content: str | list[FlangTextMatchObject]
    visible_in_spec: bool = False

    def __len__(self):
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    def get_construct(self, flang_object: FlangObject) -> FlangConstruct:
        return flang_object.find_symbol(self.symbol)

    def get_raw_content(self):
        return (
            "".join(it.get_raw_content() for it in self.content)
            if isinstance(self.content, list)
            else self.content
        )

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
class FlangFileMatchObject:
    symbol: str
    filename: str
    content: FlangTextMatchObject | list[FlangFileMatchObject]
    visible_in_spec: bool = False

    def __len__(self):
        raise Exception("Cannot determine the length of file-like object")


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
    def from_path(cls, path: str):
        path_object = pathlib.Path(path)

        assert path_object.exists()

        if path_object.is_dir():
            content = [cls.from_path(child_path) for child_path in path_object.iterdir()]
        else:
            content = open(path_object)

        return cls(content=content, path=path_object)

    def write(self): ...


sanity_check = True


class FlangInputReader:
    def __init__(
        self,
        data: str | io.StringIO | list[IntermediateFileObject],
        cursor: int | list | None = None,
        previous: FlangInputReader | None = None,
    ) -> None:
        self._data = io.StringIO(data) if isinstance(data, str) else data

        if cursor is None:
            self._cursor = 0 if isinstance(data, (str, io.StringIO)) else []
        else:
            self._cursor = cursor.copy() if isinstance(cursor, list) else cursor

        self._previous = previous

    @staticmethod
    def compare(in_1: FlangInputReader, in_2: FlangInputReader):
        return 0

    def read(self, size=None):
        match self._data:
            case io.StringIO():
                self._data.seek(self._cursor)  # look-up correct scope of input stream
                data = self._data.read() if size is None else self._data.read(size)
                self._data.seek(self._cursor)  # do not modify the state
                return data
            case list():
                return [self._data[i] for i in self._cursor]

    def consume_data(self, data: FlangTextMatchObject | FlangFileMatchObject) -> None:
        match data:
            case FlangTextMatchObject():
                if sanity_check:
                    consumed_data = self.read(len(data))
                    assert consumed_data == data.get_raw_content()
                self._cursor += len(data)
            case FlangFileMatchObject():
                if sanity_check:
                    assert all(item in self._data for item in data.content)

                self._cursor += [
                    i for i, item in enumerate(self._data) if item in data.content
                ]

                if sanity_check:
                    assert len(self._cursor) == len(set(self._cursor))
            case _:
                raise Exception(f"Unknown data consumed: {type(data)}: {data}")

    @property
    def previous(self):
        assert self._previous is not None
        return self._previous

    def copy(self) -> FlangInputReader:
        new_version = FlangInputReader(self._data, cursor=self._cursor, previous=self)
        return new_version
