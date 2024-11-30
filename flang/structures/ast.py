from __future__ import annotations

import dataclasses
from typing import TypeVar

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
    flang_ast_path: str
    specification: dict[str, str | int] = {}

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError


@dataclasses.dataclass
class UserBranch(BaseUserAST):
    filename: str | None = None

    def size(self) -> int:
        return sum(child.size() for child in self.children)


@dataclasses.dataclass
class UserLeaf(BaseUserAST):
    children: None = dataclasses.field(default=None, init=False)
    content: str

    # @children.setter
    # def _setter(self, _value):
    #     raise Exception

    def size(self) -> int:
        return len(self.content)


@dataclasses.dataclass
class UserRoot(UserBranch):
    name: str = dataclasses.field(default="", init=False, repr=False)
    flang_ast_path: None = dataclasses.field(default=None, init=False, repr=False)
