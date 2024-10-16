from __future__ import annotations

import dataclasses
import re
from typing import Any, Self

from flang.utils.exceptions import (
    DuplicateNodeInsertionError,
    ExactSameNodeInsertionError,
)


@dataclasses.dataclass(kw_only=True)
class BasicTree:
    children: list[type[BasicTree]] | None = None
    path_separator: str = dataclasses.field(
        compare=False,
        repr=False,
        init=False,
        default=".",
        metadata={"include_in_dict": False},
    )
    pattern_for_duplicate_node: str = dataclasses.field(
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

    @classmethod
    def from_dict(cls, source: dict):
        copied_source = source.copy()

        # could be more complicated if this would be useful
        if isinstance(children := copied_source.pop("children", None), list):
            children = [cls.from_dict(child_dict) for child_dict in children]

        return cls(**copied_source, children=children)

    def replace(self, **kwargs):
        new_obj = dataclasses.replace(self, **kwargs)
        new_obj.parent = self.parent
        return new_obj


@dataclasses.dataclass(kw_only=True)
class SearchableTree(BasicTree):
    name: str
    children: list[type[SearchableTree]] | None = None

    def get_(self, name: str) -> type[SearchableTree] | None:
        # Shallow search for only current children
        if self.children is None:
            return None

        for child in self.children:
            if child.name == name:
                return child

        return None

    def is_relative_path(self, path: str) -> bool:
        return path.startswith(self.path_separator)

    def translate_relative_path(self, path: str) -> str:
        stripped_path = path
        number_of_levels = 0

        while stripped_path != (
            new_path := stripped_path.removeprefix(self.path_separator)
        ):
            stripped_path = new_path
            number_of_levels += 1

        node = self.go_upwards(number_of_levels)

        if node is None:
            return stripped_path

        return node.location + self.path_separator + stripped_path

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

    def search_down(self, path: str) -> type[SearchableTree] | None:
        path_names = path.split(self.path_separator)
        node = self

        for name in path_names:
            poo = node.get_(name)

            if node is None:
                return None

        return node

    def search_down_full_path(
        self, path: str, allow_same_level: bool = True
    ) -> type[SearchableTree] | None:
        location = self.location

        if location == path:
            return self if allow_same_level else None

        if not path.startswith(location):
            return None

        return self.search_down(path.removeprefix(location + self.path_separator))

    def full_search(self, path: str) -> type[SearchableTree] | None:
        return self.root.search_down_full_path(path)

    @property  # should be cached property
    def location(self) -> str:
        if self.parent is None:
            return self.name

        parent_location = self.parent.location
        return f"{parent_location}{self.path_separator}{self.name}"

    @property
    def root(self) -> SearchableTree:
        return self if self.parent is None else self.parent.root

    def add_node(
        self,
        node: type[SearchableTree],
        allow_duplicates=True,
    ) -> SearchableTree:
        if not isinstance(self.children, list):
            self.children = []

        duplicate = self.get_(node.name)

        if duplicate is not None:
            if not allow_duplicates:
                raise DuplicateNodeInsertionError
            if duplicate is node:
                raise ExactSameNodeInsertionError

            pattern = node.pattern_for_duplicate_node.format(r"\d")
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
            updated_name = f"{node.name}{node.pattern_for_duplicate_node.format(most_recent_duplicate_index)}"
            node.name = updated_name

        node.parent = self
        self.children.append(node)
        return node

    def resolve_path(
        self, target_path: str, current_path: str
    ) -> type[SearchableTree] | None:
        # TODO: Maybe should create something like `self` that translates directly to "{self.name}."
        if self.is_relative_path(target_path):
            relative_node = self.full_search(current_path)
            assert relative_node is not None

            return relative_node.relative_search(target_path)
        return self.full_search(target_path)
