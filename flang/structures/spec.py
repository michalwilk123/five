from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Literal

from flang.utils.common import convert_to_bool

from .searchable_tree import SearchableTree


@dataclasses.dataclass
class FlangAST(SearchableTree):
    type: str
    attributes: dict
    text: str | None

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        return convert_to_bool(self.attributes.get(key, default))


@dataclasses.dataclass
class BaseUserAST(SearchableTree):
    flang_ast_path: str

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    @staticmethod
    def get_flang_ast_name_from_spec_name(identifier: str) -> str:
        return re.sub(r"\[\d+\]$", "", identifier)

    @property
    def flang_ast_name(self) -> str:
        return self.get_flang_ast_name_from_spec_name(self.identifier)

    def size(self):
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
class UserASTAbstractNode(BaseUserAST, UserASTComplexMixin):
    flang_ast_path: str = dataclasses.field(
        init=False, repr=False, compare=False, default=ABSTRACT_IDENTIFIER
    )
    name: str = dataclasses.field(
        init=False, repr=False, compare=False, default=ABSTRACT_IDENTIFIER
    )


FlangFileMatch = UserASTFileMixin
UserASTRootNode = UserASTFileMixin | UserASTAbstractNode
