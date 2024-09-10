from __future__ import annotations

import dataclasses
import fnmatch
import io
import pathlib
import re
from collections import defaultdict
from typing import Callable, Generator, Literal

from flang.exceptions import SymbolNotFoundError, UnknownParentException
from flang.helpers import BUILTIN_PATTERNS, convert_to_bool

FlangEvent = Callable[[], None]


@dataclasses.dataclass
class FlangConstruct:
    name: str
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


@dataclasses.dataclass
class FlangProjectConstruct:
    path: str
    root: str = ""
    symbol_table: dict[str, FlangConstruct] = dataclasses.field(default_factory=dict)
    symbol_occurence_counter: dict[str, int] = dataclasses.field(default_factory=dict)

    def find_symbol(self, symbol: str) -> FlangConstruct:
        return self.symbol_table[symbol]

    def add_symbol(self, symbol: str, constr: FlangConstruct, override=False):
        if symbol in self.symbol_table and not override:
            raise RuntimeError(f"Symbol {symbol} already exists!")
        self.symbol_table[symbol] = constr

    def generate_unique_symbol(self, element_identifier: str, parent_location: str):
        location = (
            f"{parent_location}.{element_identifier}"
            if parent_location
            else f"{self.path}:{element_identifier}"
        )

        if location not in self.symbol_table:
            self.symbol_occurence_counter[location] = 0
            return location

        self.symbol_occurence_counter[location] += 1
        location += f"@{self.symbol_occurence_counter[location]}"

        return location

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

        raise RuntimeError(f"Unknown path to constuct: {reference_path}")


# dataclass, not typing.TypedDict because we need methods
@dataclasses.dataclass
class FlangMatchObject:
    symbol: str
    construct: str
    content: str | list[FlangMatchObject]
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def __len__(self) -> int:
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    def get_construct(self, project_construct: FlangProjectConstruct) -> FlangConstruct:
        return project_construct.find_symbol(self.symbol)

    def get_combined_text(self) -> str:
        assert (
            self.metadata.get("filename") is None
            or pathlib.Path(self.metadata["filename"]).is_dir() is False
        )

        if isinstance(self.content, list):
            return "".join(it.get_combined_text() for it in self.content)

        return self.content

    def get_raw_content(self) -> str | list[str]:
        if (
            self.metadata.get("filename")
            and pathlib.Path(self.metadata["filename"]).is_dir()
        ):
            assert isinstance(self.content, list)

            return [f.metadata["filename"] for f in self.content]

        return self.get_combined_text()

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

    @classmethod
    def from_representation(cls, representation: tuple):
        raise NotImplementedError

    @staticmethod
    def evaluate_match_tree(
        match_object: FlangMatchObject,
        evaluator_function: Callable[[FlangMatchObject], None],
        traversal_order: Literal["parent", "child"] = "child",
    ) -> None:
        if traversal_order == "parent":
            evaluator_function(match_object)

        if isinstance(match_object.content, list):
            for item in match_object.content:
                FlangMatchObject.evaluate_match_tree(
                    item, evaluator_function, traversal_order
                )

        if traversal_order == "child":
            evaluator_function(match_object)


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
    def get_first_matched_file(
        list_of_files: list[IntermediateFileObject], pattern: str, variant: str
    ) -> IntermediateFileObject | None:
        assert variant in ("filename", "glob", "regex")

        if variant == "glob":
            pattern = fnmatch.translate(pattern)

        def _is_pathname_matched(file_object):
            if variant == "filename":
                return file_object.path.name == pattern

            return re.match(pattern, file_object.path.name)

        try:
            return next(filter(_is_pathname_matched, list_of_files))
        except StopIteration:
            return None


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
        self._cursor: list[int] | int
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

    def read(self, size=None) -> str | list[IntermediateFileObject]:
        match self._data:
            case io.StringIO():
                assert isinstance(self._cursor, int)

                self._data.seek(self._cursor)  # look-up correct scope of input stream
                data = self._data.read() if size is None else self._data.read(size)
                self._data.seek(self._cursor)  # do not modify the state
                return data
            case list():
                assert isinstance(self._cursor, list)

                return [self._data[i] for i in self._cursor]

    def read_ensure_files(self): ...

    def consume_data(self, data: FlangMatchObject) -> None:
        if isinstance(self._data, list) and isinstance(self._cursor, list):
            filenames = [f.path.name for f in self._data]

            if sanity_check:
                assert data.metadata["filename"] in filenames

            self._cursor.remove(filenames.index(data.metadata["filename"]))

            if sanity_check:
                assert len(self._cursor) == len(set(self._cursor))
        elif isinstance(self._data, io.StringIO) and isinstance(self._cursor, int):
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


@dataclasses.dataclass
class FlangLinkNode:
    vertex: str | None
    parent: str | None
    children: list[FlangLinkNode] = dataclasses.field(default_factory=list)
    is_leaf: bool = True

    def search_for_child(self, symbol: str) -> FlangLinkNode | None:
        if self.vertex is not None and self.vertex == symbol:
            return self

        if self.children:
            for child in self.children:
                if (node := child.search_for_child(symbol)) is not None:
                    return node

    def get_symbols(self, ensure_tree: bool = False) -> list[str]:
        if self.vertex is None:
            symbols = []
        else:
            symbols = [self.vertex]

        if self.children:
            for child in self.children:
                symbols += child.get_symbols(ensure_tree=ensure_tree)

            if ensure_tree and len(symbols) != len(set(symbols)):
                raise RuntimeError("")

        return symbols


class FlangLinkGraph:
    def __init__(self) -> None:
        self.link_forest = FlangLinkNode(vertex=None, parent=None, children=[])

    def add_relation(self, parent_symbol: str, child_symbol: str):
        parent_node = self.link_forest.search_for_child(parent_symbol)

        if parent_node is None:
            raise UnknownParentException(
                f"Could not find parent: {parent_node} for child: {child_symbol}"
            )

        child_node = self.link_forest.search_for_child(child_symbol)

        if child_node is None:
            child_node = FlangLinkNode(parent=parent_symbol, vertex=child_symbol)

        parent_node.children.append(child_node)

    def add_parent(self, parent_symbol: str):
        assert (
            self.link_forest.search_for_child(parent_symbol) is None
        ), f"Node: {parent_symbol} already exists! {self.link_forest}"

        self.link_forest.children.append(
            FlangLinkNode(parent=None, vertex=parent_symbol, is_leaf=False)
        )


class FlangEventQueue:
    def __init__(self) -> None:
        self.function_bank: dict[int, list[FlangEvent]] = defaultdict(list)

    def iterate_events(self) -> Generator[FlangEvent]:
        sorted_keys = sorted(self.function_bank.keys())

        for i in sorted_keys:
            for event in self.function_bank[i]:
                yield event
