from __future__ import annotations

import dataclasses
import re
from typing import TypeVar

from flang.utils.exceptions import (
    DuplicateNodeInsertionError,
    ExactSameNodeInsertionError,
)

T = TypeVar("T")


@dataclasses.dataclass(kw_only=True)
class BasicTree:
    children: list[BasicTree] | None = None
    path_separator: str = dataclasses.field(
        compare=False,
        repr=False,
        init=False,
        default=".",
        metadata={"include_in_dict": False},
    )
    index_for_duplicates_container: str = dataclasses.field(
        compare=False,
        repr=False,
        init=False,
        default="[{}]",
        metadata={"include_in_dict": False},
    )

    def __post_init__(self):
        self.parent = None

        if self.children is None:
            return

        for child in self.children:
            child.parent = self

    @classmethod
    def dict_factory(cls, obj):
        fields_to_exclude = tuple(
            field.name
            for field in dataclasses.fields(cls)
            if field.metadata.get("include_in_dict", True)
        )

        return {
            field_name: field_value
            for (field_name, field_value) in obj
            if field_name in fields_to_exclude
        }

    @property
    def first_child(self: T) -> T:
        assert isinstance(self.children, list) and len(self.children) > 0
        child = self.children[0]
        return child

    def to_dict(self) -> dict:
        return dataclasses.asdict(self, dict_factory=self.dict_factory)

    @classmethod
    def from_dict(cls: T, source: dict) -> T:
        copied_source = source.copy()

        # could be more complicated if this would be useful
        if isinstance(children := copied_source.pop("children", None), list):
            children = [cls.from_dict(child_dict) for child_dict in children]

        return cls(**copied_source, children=children)

    def replace(self: T, **kwargs) -> T:
        new_obj = dataclasses.replace(self, **kwargs)
        new_obj.parent = self.parent
        return new_obj


@dataclasses.dataclass(kw_only=True)
class SearchableTree(BasicTree):
    name: str
    children: list[SearchableTree] | None = None

    def get_(self: T, name: str) -> T | None:
        # Shallow search for only current children
        if self.children is None:
            return None

        for child in self.children:
            if child.name == name:
                return child

        return None

    def is_relative_path(self, path: str) -> bool:
        return path.startswith(self.path_separator)

    def relative_search(self: T, path: str) -> T | None:
        stripped_path = path
        number_of_levels = 0

        while stripped_path != (
            new_path := stripped_path.removeprefix(self.path_separator)
        ):
            stripped_path = new_path
            number_of_levels += 1

        node = self.go_upwards(number_of_levels)

        if node is None:
            return self.full_search(stripped_path)

        return node.search_down(stripped_path)

    def go_upwards(self: T, number_of_steps: int) -> T | None:
        node = self

        for _ in range(number_of_steps):
            assert node is not None
            node = node.parent

        return node

    def search_down(self: T, path: str) -> T | None:
        path_names = path.split(self.path_separator)
        node = self

        for name in path_names:
            node = node.get_(name)

            if node is None:
                return None

        return node

    def search_down_full_path(
        self: T, path: str, allow_same_level: bool = True
    ) -> T | None:
        location = self.location

        if location == path:
            return self if allow_same_level else None

        if not path.startswith(location):
            return None

        return self.search_down(path.removeprefix(location + self.path_separator))

    def full_search(self: T, path: str) -> T | None:
        return self.root.search_down_full_path(path)

    @property  # should be cached property
    def location(self) -> str:
        if self.parent is None:
            return self.name

        parent_location = self.parent.location
        return f"{parent_location}{self.path_separator}{self.name}"

    @property
    def root(self: T) -> T:
        return self if self.parent is None else self.parent.root

    def add_node(
        self: T,
        node: SearchableTree,
        allow_duplicates=True,
    ) -> T:
        if not isinstance(self.children, list):
            self.children = []

        duplicate = self.get_(node.name)

        if duplicate is not None:
            if not allow_duplicates:
                raise DuplicateNodeInsertionError
            if duplicate is node:
                raise ExactSameNodeInsertionError

            pattern = node.index_for_duplicates_container.format(r"\d")
            duplicates = filter(
                lambda el: el.name.startswith(node.name) and node.name != el.name,
                self.children,
            )
            most_recent_duplicate_index = max(
                (
                    int(re.search(pattern, it.name.removeprefix(node.name)).group())
                    for it in duplicates
                ),
                default=0,
            )

            most_recent_duplicate_index += 1
            updated_name = f"{node.name}{node.index_for_duplicates_container.format(most_recent_duplicate_index)}"
            node.name = updated_name

        node.parent = self
        self.children.append(node)
        return node

    def resolve_path(self: T, target_path: str, current_path: str) -> T | None:
        # TODO: Maybe should create something like `self` that translates directly to "{self.name}."
        if self.is_relative_path(target_path):
            relative_node = self.full_search(current_path)

            assert relative_node is not None

            return relative_node.relative_search(target_path)
        return self.full_search(target_path)
