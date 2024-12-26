from __future__ import annotations

import dataclasses
from typing import ClassVar, Self, TypeVar

from flang.utils.common import convert_to_bool

from .searchable_tree import SearchableTree

T = TypeVar("T")


@dataclasses.dataclass
class FlangAST(SearchableTree):
    type: str
    attributes: dict
    text: str | None

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        return convert_to_bool(self.attributes.get(key, default))

    def create_alias(self, alias_name: str) -> None:
        self.root._root_create_alias(alias_name, self.location)

    def _root_create_alias(self, alias_name: str, location: str) -> None:
        if not hasattr(self, "_meta"):
            self._meta: dict[str, str] = {}

        self._meta[alias_name] = location

    def normalize_path(self: T, target_path: str) -> str:
        if target_path.startswith("@"):
            alias_name = target_path.removeprefix("@")
            return self.root._meta[alias_name]

        if self.is_relative_path(target_path):
            return self.translate_relative_path(target_path)

        return target_path


@dataclasses.dataclass
class BaseUserAST(SearchableTree):
    DUPLICATE_NODE_BRACKETS: ClassVar[tuple[str, str]] = ("(", ")")
    flang_ast_path: str

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError

    def diff(self, other: BaseUserAST):
        if self.name != other.name:
            print(f"NAME DIFFERENT: {self.name=} {other.name=}")
            return False

        if self.flang_ast_path != other.flang_ast_path:
            print(f"PATH DIFFERENT: {self.flang_ast_path=} {other.flang_ast_path=}")
            return False

        if self.children:
            if not other.children:
                return False

            return all(
                child1.diff(child2)
                for child1, child2 in zip(self.children, other.children)
            )

        return True


@dataclasses.dataclass
class UserBranch(BaseUserAST):
    filename: str | None = None

    def size(self) -> int:
        return sum(child.size() for child in self.children) if self.children else 0

    def diff(self, other: UserBranch):
        if self.filename != other.filename:
            print(f"FILENAME DIFFERENT: {self.filename=} {other.filename=}")
            return False

        return super().diff(other)


@dataclasses.dataclass
class UserLeaf(BaseUserAST):
    children: None = dataclasses.field(default=None, init=False)
    content: str

    def size(self) -> int:
        return len(self.content)

    def diff(self, other: UserBranch):
        if self.content != other.content:
            print(f"CONTENT DIFFERENT: {self.content=} {other.content=}")
            return False

        return super().diff(other)


@dataclasses.dataclass
class UserRoot(UserBranch):
    name: str = dataclasses.field(default="", init=False, repr=False)
    flang_ast_path: str = dataclasses.field(default="", init=False, repr=False)
    PATH_SEPARATOR: ClassVar[str] = ""

    @property
    def root(self) -> SearchableTree:
        return self.children[0]

    def full_search(self, path: str) -> Self | None:
        if not path:
            return self

        return self.children[0].search_down_full_path(path)


@dataclasses.dataclass
class FlangASTRoot(FlangAST):
    type: str = dataclasses.field(default="", init=False, repr=False)
    name: str = dataclasses.field(default="", init=False, repr=False)
    text: None = dataclasses.field(default=None, init=False, repr=False)
    attributes: dict = dataclasses.field(default_factory=dict, init=False, repr=False)
    PATH_SEPARATOR: ClassVar[str] = ""

    @property
    def root(self) -> SearchableTree:
        return self.children[0]

    def full_search(self, path: str) -> Self | None:
        if not path:
            return self

        return self.children[0].search_down_full_path(path)
