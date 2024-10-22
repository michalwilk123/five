from __future__ import annotations

import dataclasses
import pathlib
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

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError


@dataclasses.dataclass
class UserASTFileMixin:
    filename: str


@dataclasses.dataclass
class UserASTComplexMixin:
    children: list[BaseUserAST]

    def size(self) -> int:
        return sum(item.size() for item in self.children)

    def get_raw_content(self) -> str:
        return "".join(it.get_raw_content() for it in self.children)

    @property
    def shallow_dict(self) -> dict[str]:
        raise NotImplementedError


@dataclasses.dataclass
class UserASTDirectoryNode(UserASTFileMixin, UserASTComplexMixin, BaseUserAST):

    def get_raw_content(self) -> str | list[str]:
        assert pathlib.Path(self.filename).is_dir()
        return [f.filename for f in self.children]


@dataclasses.dataclass(kw_only=True)
class UserASTTextNode(BaseUserAST):
    content: str
    children: None = dataclasses.field(init=False, repr=False, compare=False)

    def size(self) -> int:
        return len(self.content)

    def get_raw_content(self) -> str:
        return self.content


@dataclasses.dataclass
class UserASTComplexNode(UserASTComplexMixin, BaseUserAST):
    pass


@dataclasses.dataclass
class UserASTFlatFileNode(UserASTFileMixin, UserASTComplexMixin, BaseUserAST):
    pass


ABSTRACT_IDENTIFIER = "<ABSTRACT-ROOT>"


# kw_only=True is added because we override the old field and add a default value
@dataclasses.dataclass(kw_only=True)
class UserASTRootContainerNode(BaseUserAST, UserASTComplexMixin):
    flang_ast_path: str = dataclasses.field(
        init=False, repr=False, compare=False, default=ABSTRACT_IDENTIFIER
    )
    name: str = dataclasses.field(
        init=False, repr=False, compare=False, default=ABSTRACT_IDENTIFIER
    )
    generate_patch: bool = dataclasses.field(
        init=False, repr=False, compare=False, default=False
    )


FlangFileMatch = UserASTFileMixin
UserASTRootNode = UserASTFileMixin | UserASTRootContainerNode
