from __future__ import annotations

import dataclasses
import fnmatch
import io
import pathlib
import re
from functools import cached_property

from flang.exceptions import SymbolNotFoundError
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

    def find_construct_by_path(
        self, reference_path: str, current_path: str = ""
    ) -> FlangConstruct:
        is_symbol_external = ":" in reference_path
        is_symbol_relative = reference_path.startswith(".") and not is_symbol_external

        if is_symbol_relative and not current_path:
            raise RuntimeError

        if is_symbol_external:
            try:
                return self.find_symbol(reference_path)
            except KeyError as e:
                raise SymbolNotFoundError from e
        elif is_symbol_relative:
            path_without_dots = reference_path.lstrip(".")
            backward_steps = len(reference_path) - len(path_without_dots)

            filename, local_path = current_path.split(":")
            target_path = ".".join(
                local_path.split(".")[:-backward_steps] + [path_without_dots]
            )
            full_target_path = "%s:%s" % (filename, target_path)
            return self.find_construct_by_path(full_target_path)


# dataclass, not typing.TypedDict because we need methods
@dataclasses.dataclass
class FlangMatchObject:
    symbol: str
    construct: str
    content: str | list[FlangMatchObject]
    visible_in_spec: bool = False
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def __len__(self):
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    def get_construct(self, flang_object: FlangObject) -> FlangConstruct:
        return flang_object.find_symbol(self.symbol)

    def get_raw_content(self):
        if (
            self.metadata.get("filename")
            and pathlib.Path(self.metadata.get("filename")).is_dir()
        ):
            return [f.metadata.get("filename") for f in self.content]

        if isinstance(self.content, list):
            return "".join(it.get_raw_content() for it in self.content)

        return self.content

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


# @dataclasses.dataclass
# class FlangFileMatchObject:
#     symbol: str
#     filename: str
#     content: FlangTextMatchObject | list[FlangTextMatchObject] | list[FlangFileMatchObject]
#     visible_in_spec: bool = False

#     def __len__(self):
#         raise Exception("Cannot determine the length of file-like object")


class IntermediateFileObject:
    """
    Class that represents metadata of a file
    """

    def __init__(self, path: str, content: list | None = None) -> None:
        self.path = pathlib.Path(path)
        assert self.path.exists()
        self._content = content

    @property
    def content(self) -> str | list[IntermediateFileObject]:
        if self._content is not None:
            return self._content

        if self.path.is_dir():
            return [IntermediateFileObject(str(file)) for file in self.path.iterdir()]
        else:
            with open(self.path) as f:
                return f.read()

    def get_input_reader(self):
        return FlangInputReader(self.content, metadata={"filename": self.path.name})

    @staticmethod
    def get_matched_files(
        list_of_files: list[IntermediateFileObject], pattern: str, variant: str
    ) -> list[IntermediateFileObject]:
        assert variant in ("filename", "glob", "regex")

        if variant == "glob":
            pattern = fnmatch.translate(pattern)

        if variant == "filename":
            filenames = [item for item in list_of_files if item.path.name == pattern]
        else:
            filenames = [
                item for item in list_of_files if re.match(pattern, item.path.name)
            ]

        return filenames


sanity_check = True


class FlangInputReader:
    def __init__(
        self,
        data: str | io.StringIO | list[IntermediateFileObject],
        cursor: int | list | None = None,
        previous: FlangInputReader | None = None,
        metadata: dict | None = None,
    ) -> None:
        assert isinstance(data, (str, io.StringIO, list))

        # if isinstance(data, IntermediateFileObject):
        #     assert data.path.is_dir()

        self._data = io.StringIO(data) if isinstance(data, str) else data
        self.meta = metadata

        if cursor is None:
            if isinstance(data, (str, io.StringIO)):
                self._cursor = 0
            else:
                self._cursor = list(range(len(data)))
        else:
            self._cursor = cursor.copy() if isinstance(cursor, list) else cursor

        self._previous = previous

    @property
    def is_file(self):
        return isinstance(self._data, list)

    @staticmethod
    def compare(in_1: FlangInputReader, in_2: FlangInputReader):
        import warnings

        warnings.warn("NOT IMPLEMENTED!")
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

    def consume_data(self, data: FlangMatchObject) -> None:
        if isinstance(self._data, list):
            filenames = [f.path.name for f in self._data]

            if sanity_check:
                assert data.metadata["filename"] in filenames

            # for item in data.content:
            #     self._cursor.remove(filenames.index(item.metadata["filename"]))
            self._cursor.remove(filenames.index(data.metadata["filename"]))

            if sanity_check:
                assert len(self._cursor) == len(set(self._cursor))
        elif isinstance(self._data, io.StringIO):
            if sanity_check:
                consumed_data = self.read(len(data))
                assert consumed_data == data.get_raw_content(), data.construct
            self._cursor += len(data)
        else:
            assert 0, "i dont know what to do %s" % self._data

    @property
    def previous(self):
        assert self._previous is not None
        return self._previous

    def copy(self) -> FlangInputReader:
        copied_cursor = (
            self._cursor.copy() if isinstance(self._cursor, list) else self._cursor
        )
        new_version = FlangInputReader(
            self._data, cursor=copied_cursor, previous=self, metadata=self.meta
        )
        return new_version

    @classmethod
    def from_path(cls, path: str):
        return cls(
            [IntermediateFileObject(path)], metadata={"filename": pathlib.Path(path).name}
        )


class FlangTextReader: ...
