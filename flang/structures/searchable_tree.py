from __future__ import annotations

import dataclasses
import re
from typing import Any, ClassVar, Self

from flang.utils.exceptions import (
    DuplicateNodeInsertionError,
    ExactSameNodeInsertionError,
)


@dataclasses.dataclass(kw_only=True)
class BasicTree:
    children: list[type[BasicTree]] | None = None
    PATH_SEPARATOR: ClassVar[str] = "."
    DUPLICATE_NODE_BRACKETS: ClassVar[tuple[str, str]] = ("[", "]")

    def __post_init__(self):
        self.parent = None

        if self.children is None:
            return

        for child in self.children:
            child.parent = self  # type: ignore

    @classmethod
    def _get_fields_to_exclude(cls):
        return tuple(
            field.name
            for field in dataclasses.fields(cls)
            if field.metadata.get("include_in_dict", True)
        )

    @classmethod
    def dict_factory(cls, obj: list[tuple[str, Any]]) -> dict:
        return {
            field_name: field_value
            for (field_name, field_value) in obj
            if field_name in cls._get_fields_to_exclude()
        }

    @property
    def first_child(self) -> type[BasicTree]:
        assert isinstance(self.children, list) and len(self.children) > 0
        child = self.children[0]
        return child

    def to_dict(self) -> dict:
        return dataclasses.asdict(self, dict_factory=self.dict_factory)

    def to_shallow_dict(self) -> dict[str, Any]:
        tuple_obj = [(f.name, getattr(self, f.name)) for f in dataclasses.fields(self)]
        return self.dict_factory(tuple_obj)

    def set_children(self, children: list[SearchableTree]) -> SearchableTree:
        if children:
            for child in children:
                self.add_node(child)

        return self

    @classmethod
    def from_dict(cls, source: dict):
        copied_source = source.copy()

        # could be more complicated if this would be useful
        if isinstance(children := copied_source.pop("children", None), list):
            children = [cls.from_dict(child_dict) for child_dict in children]

        return cls(**copied_source).set_children(children)

    def replace(self, **kwargs):
        new_obj = dataclasses.replace(self, **kwargs)
        new_obj.parent = self.parent
        return new_obj


@dataclasses.dataclass(kw_only=True)
class SearchableTree(BasicTree):
    children: list[type[SearchableTree]] | None = dataclasses.field(
        default=None, init=False
    )
    name: str
    index: int = dataclasses.field(default=0)

    @classmethod
    def pack(cls, index: int, name: str) -> str:
        if index == 0:
            return name

        return (
            name
            + cls.DUPLICATE_NODE_BRACKETS[0]
            + str(index)
            + cls.DUPLICATE_NODE_BRACKETS[1]
        )

    @classmethod
    def unpack(cls, node_id: str) -> tuple[int, str]:
        suff = node_id.split(cls.DUPLICATE_NODE_BRACKETS[0])[-1]
        name = node_id.removesuffix(cls.DUPLICATE_NODE_BRACKETS[0] + suff)
        node_id = int(suff.removesuffix(cls.DUPLICATE_NODE_BRACKETS[1]))
        return node_id, name

    def get_id(self) -> str:
        return self.pack(self.index, self.name)

    def get_(self, id: str) -> Self | None:
        # Shallow search for only current children
        if self.children is None:
            return None

        for child in self.children:
            if child.get_id() == id:
                return child

        return None

    def is_relative_path(self, path: str) -> bool:
        return path.startswith(self.PATH_SEPARATOR)

    def translate_relative_path(self, path: str) -> str:
        stripped_path = path
        number_of_levels = 0

        while stripped_path != (
            new_path := stripped_path.removeprefix(self.PATH_SEPARATOR)
        ):
            stripped_path = new_path
            number_of_levels += 1

        node = self.go_upwards(number_of_levels)

        if node is None:
            return stripped_path

        return self.join_paths(node.location, stripped_path)

    def relative_search(self, path: str) -> type[SearchableTree] | None:
        translated = self.translate_relative_path(path)
        assert translated is not None

        return self.full_search(translated)

    def go_upwards(self, number_of_steps: int) -> SearchableTree | None:
        node = self

        for _ in range(number_of_steps):
            assert node is not None
            node = node.parent

        return node

    def search_down(self, path: str) -> Self | None:
        path_names = path.split(self.PATH_SEPARATOR)
        node = self

        for id in path_names:
            if not (node := node.get_(id)):
                return None

        return node

    def search_down_full_path(
        self, path: str, allow_same_level: bool = True
    ) -> Self | None:
        location = self.location

        if location == path:
            return self if allow_same_level else None

        if not path.startswith(location):
            return None

        return self.search_down(path.removeprefix(location + self.PATH_SEPARATOR))

    def full_search(self, path: str) -> Self | None:
        return self.root.search_down_full_path(path)

    @property  # should be cached property
    def location(self) -> str:
        if self.parent is None:
            return self.get_id()

        parent_location = self.parent.location
        return self.parent.join_paths(parent_location, self.get_id())

    @property
    def root(self) -> SearchableTree:
        return self if self.parent is None else self.parent.root

    def get_next_node_index(self, name: str) -> tuple[int, str]:
        if not self.children:
            return 0

        last_node_index = max(
            (item.index for item in self.children if item.name == name), default=None
        )

        if last_node_index is None:
            return 0

        return last_node_index + 1

    @classmethod
    def join_paths(cls, *chunks: str):
        return cls.PATH_SEPARATOR.join(chunks)

    def add_node(
        self,
        node: SearchableTree,
        allow_duplicates: bool = True,
    ) -> SearchableTree:
        if self.children is None:
            self.children = []

        duplicate = self.get_(node.get_id())

        if duplicate is not None:
            if not allow_duplicates:
                raise DuplicateNodeInsertionError
            if duplicate is node:
                raise ExactSameNodeInsertionError

            node.index = self.get_next_node_index(node.name)

        node.parent = self
        self.children.append(node)

        return node

    def resolve_path(self, target_path: str, current_path: str) -> SearchableTree | None:
        # TODO: Maybe should create something like `self` that translates directly to "{self.name}."
        if self.is_relative_path(target_path):
            relative_node = self.full_search(current_path)
            assert relative_node is not None

            return relative_node.relative_search(target_path)
        return self.full_search(target_path)


@dataclasses.dataclass
class SearchableTreeRoot(SearchableTree):
    name: str = dataclasses.field(default="", init=False, repr=False)
    PATH_SEPARATOR: ClassVar[str] = ""

    @property
    def root(self) -> Self:
        return self.children[0] if self.children else self

    def full_search(self, path: str) -> Self | None:
        if not path:
            return self

        return self.root.search_down_full_path(path)
