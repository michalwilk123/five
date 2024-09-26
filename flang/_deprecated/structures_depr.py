from __future__ import annotations

import abc
import dataclasses
import fnmatch
import io
import pathlib
import re
from collections import defaultdict
from typing import Callable, Generator, Literal

from flang.utils.common import BUILTIN_PATTERNS, convert_to_bool
from flang.utils.exceptions import SymbolNotFoundError, UnknownParentException

FlangEvent = Callable[[], None]


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


class FlangProjectConstruct:  # TODO: Maybe should be called a FlangMatchingRuntime?
    # path: str
    # root: str = ""
    # # linking_graph: FlangLinkGraph = dataclasses.field(default_factory=FlangLinkGraph) # TODO: not needed?
    # # event_queue: FlangEventQueue = dataclasses.field(default_factory=FlangEventQueue)
    # symbol_table: dict[str, FlangConstruct] = dataclasses.field(default_factory=dict)
    # symbol_occurence_counter: dict[str, int] = dataclasses.field(default_factory=dict)
    def __init__(self, path: str) -> None:
        self.path = path
        self.root = ""
        self.symbol_table: dict[str, FlangConstruct] = {}
        self.symbol_occurence_counter: dict[str, int] = {}

    def find_symbol(self, symbol: str) -> FlangConstruct:
        return self.symbol_table[symbol]

    def add_symbol(self, symbol: str, constr: FlangConstruct, override=False):
        if symbol in self.symbol_table and not override:
            raise RuntimeError(f"Symbol {symbol} already exists!")
        self.symbol_table[symbol] = constr

    def generate_symbol_for_match_object(self, construct_symbol: str): ...

    def generate_symbol_for_construct(
        self, element_identifier: str, parent_location: str
    ):
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


@dataclasses.dataclass
class FlangMatchObject:
    identifier: str

    @property
    def first_child(self) -> FlangMatchObject:
        assert isinstance(self.content, list) and len(self.content) > 0
        child = self.content[0]
        return child


@dataclasses.dataclass
class FlangAbstractMatchObject(FlangMatchObject):
    content: list[FlangTextMatchObject] | list[FlangAbstractMatchObject]
    filename: str | None


# dataclass, not typing.TypedDict because we need methods
@dataclasses.dataclass
class FlangTextMatchObject(FlangMatchObject):
    content: str | list[FlangTextMatchObject]
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def __len__(self) -> int:
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    def get_construct(self, project_construct: FlangProjectConstruct) -> FlangConstruct:
        return project_construct.find_symbol(self.identifier)

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
                self.identifier,
                [
                    child.to_representation()
                    for child in self.content
                    if child.identifier is not None
                ],
            )
        return (self.identifier, self.content)

    @classmethod
    def from_representation(cls, representation: tuple):
        raise NotImplementedError

    def evaluate_match_tree(
        self,
        evaluator_function: Callable[[FlangTextMatchObject], None],
        traversal_order: Literal["parent", "child"] = "child",
    ) -> None:
        if traversal_order == "parent":
            evaluator_function(self)

        if isinstance(self.content, list):
            for item in self.content:
                FlangTextMatchObject.evaluate_match_tree(
                    item, evaluator_function, traversal_order
                )

        if traversal_order == "child":
            evaluator_function(self)


class IntermediateFileObject:
    def __init__(self, path: str, content: list | None = None) -> None:
        assert (path := pathlib.Path(path)).exists()

        self.path = path
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

    @property
    def filename(self) -> str:
        return self.path.name

    def get_input_reader(self) -> FlangFileInputReader:
        if self.path.is_dir():
            return FlangFileInputReader(self.content, filename=self.path.name)

        return FlangTextInputReader(self.content)

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


class BaseFlangInputReader(abc.ABC):
    @abc.abstractmethod
    def read(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_key(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def consume_data(self, data: FlangMatchObject) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self) -> FlangTextInputReader:
        return FlangTextInputReader(self._data, cursor=self._cursor, previous=self)

    @property
    def previous(self):
        return self._previous


class FlangTextInputReader(BaseFlangInputReader):
    def __init__(
        self,
        data: str | io.StringIO,
        cursor: int | None = None,
        previous: FlangTextInputReader | None = None,
    ) -> None:
        self._data = io.StringIO(data) if isinstance(data, str) else data
        self._cursor = cursor or 0
        self._previous = previous

    def read(self, size=None) -> str:
        self._data.seek(self._cursor)  # look-up correct scope of input stream
        data = self._data.read() if size is None else self._data.read(size)
        self._data.seek(self._cursor)  # return to the initial state
        return data

    def get_key(self):
        import warnings

        warnings.warn("NOT IMPLEMENTED!")
        return 0

    def consume_data(self, data: FlangTextMatchObject) -> None:
        if sanity_check:
            consumed_data = self.read(len(data))
            assert consumed_data == data.get_raw_content()
        self._cursor += len(data)

    def copy(self) -> FlangTextInputReader:
        return FlangTextInputReader(self._data, cursor=self._cursor, previous=self)


class FlangFileInputReader(BaseFlangInputReader):
    def __init__(
        self,
        data: list[IntermediateFileObject],
        filename: str,
        cursor: list | None = None,
        previous: FlangFileInputReader | None = None,
    ) -> None:
        self._data = data
        self._cursor = list(range(len(data))) if cursor is None else cursor.copy()
        self._previous = previous
        self.filename = filename

    def read(self) -> list[IntermediateFileObject]:
        return [self._data[i] for i in self._cursor]

    def get_key(self):
        import warnings

        warnings.warn("NOT IMPLEMENTED!")
        return 0

    def consume_data(self, match_object: FlangAbstractMatchObject) -> None:
        filenames = [f.path.name for f in self._data]
        self._cursor.remove(filenames.index(match_object.filename))

        if sanity_check:
            assert len(self._cursor) == len(set(self._cursor))

    def copy(self) -> FlangFileInputReader:
        return FlangFileInputReader(
            self._data, filename=self.filename, cursor=self._cursor.copy(), previous=self
        )


class DEPRECATED_FlangInputReader:
    def __init__(
        self,
        data: str | io.StringIO | list[IntermediateFileObject],
        cursor: int | list | None = None,
        previous: DEPRECATED_FlangInputReader | None = None,
        metadata: dict | None = None,
    ) -> None:
        assert isinstance(data, (str, io.StringIO, list))

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
    def compare(in_1: DEPRECATED_FlangInputReader, in_2: DEPRECATED_FlangInputReader):
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

    def consume_data(self, data: FlangTextMatchObject) -> None:
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
                assert consumed_data == data.get_raw_content()
            self._cursor += len(data)
        else:
            assert 0, "i dont know what to do %s" % self._data

    @property
    def previous(self):
        assert self._previous is not None
        return self._previous

    def copy(self) -> DEPRECATED_FlangInputReader:
        copied_cursor = (
            self._cursor.copy() if isinstance(self._cursor, list) else self._cursor
        )
        new_version = DEPRECATED_FlangInputReader(
            self._data, cursor=copied_cursor, previous=self, metadata=self.meta
        )
        return new_version

    @classmethod
    def from_path(cls, path: str):
        return cls(
            [IntermediateFileObject(path)], metadata={"filename": pathlib.Path(path).name}
        )
