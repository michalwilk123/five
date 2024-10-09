from __future__ import annotations

import dataclasses
import re


class ExactSameNodeInsertionError(Exception):
    pass


class DuplicateNodeInsertionError(Exception):
    pass


@dataclasses.dataclass(kw_only=True)
class SearchableTree:
    name: str
    children: list[SearchableTree] | None = None
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

    def get_(self, name: str) -> SearchableTree | None:
        """
        Shallow search for only current children
        """
        if self.children is None:
            return None

        for child in self.children:
            if child.name == name:
                return child

        return None

    def is_relative_path(self, path: str) -> bool:
        return path.startswith(self.path_separator)

    def relative_search(self, path: str) -> SearchableTree | None:
        stripped_path = path
        number_of_levels = 0

        while stripped_path != (
            new_path := stripped_path.removeprefix(self.path_separator)
        ):
            stripped_path = new_path
            number_of_levels += 1

        node = self.go_upwards(number_of_levels)

        return node.search_down(stripped_path)

    def go_upwards(self, number_of_steps: int) -> SearchableTree | None:
        node = self

        for _ in range(number_of_steps):
            node = node.parent

        return node

    def search_down(
        self, path: str, allow_same_level: bool = True
    ) -> SearchableTree | None:
        location = self.location

        if location == path:
            return self if allow_same_level else None

        if not path.startswith(location):
            return None

        path_names = path.removeprefix(location + self.path_separator).split(
            self.path_separator
        )
        node = self

        for name in path_names:
            node = node.get_(name)

            if node is None:
                return None

        return node

    def full_search(self, path) -> SearchableTree | None:
        return self.root.search_down(path)

    def contains(self, node_id: str, till: str | None = None): ...

    @property  # should be cached property
    def location(self) -> str:
        if self.parent is None:
            return self.name

        parent_location = self.parent.location
        return f"{parent_location}{self.path_separator}{self.name}"

    @property
    def root(self):
        return self if self.parent is None else self.parent.root

    def add_node(
        self,
        node: SearchableTree,
        allow_duplicates=True,
        parent: SearchableTree | None = None,
    ) -> SearchableTree:
        if parent:
            return parent.add_node(node, allow_duplicates)

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

    def resolve_path(path): ...

    def to_dict(self) -> dict:
        return dataclasses.asdict(self, dict_factory=self.dict_factory)

    @classmethod
    def from_dict(cls, source: dict) -> SearchableTree:
        copied_source = source.copy()

        # could be more complicated if this would be useful
        if isinstance(children := copied_source.pop("children", None), list):
            children = [cls.from_dict(child_dict) for child_dict in children]

        return cls(**copied_source, children=children)
