from __future__ import annotations

import dataclasses
from typing import ClassVar, TypeVar

from flang.utils.common import convert_to_bool

from .searchable_tree import SearchableTree, SearchableTreeRoot

T = TypeVar("T")


@dataclasses.dataclass
class TemplateTree(SearchableTree):
    type: str
    attributes: dict
    text: str | None
    alias_record: None | dict[str, str] = dataclasses.field(
        default_factory=dict, repr=False
    )

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        return convert_to_bool(self.attributes.get(key, default))

    def inherit_child_aliases(self, node: TemplateTree):
        for inherited_alias_name, inherited_alias_target in node.alias_record.items():
            assert (
                inherited_alias_name not in self.alias_record
            ), f"Trying to inherit already existing alias: {inherited_alias_name} {self.alias_record=}"

            if not inherited_alias_target.startswith(node.get_id()):
                _, *rest_of_path = inherited_alias_target.split(self.PATH_SEPARATOR)
                inherited_alias_target = self.PATH_SEPARATOR.join(
                    (node.get_id(), *rest_of_path)
                )

            self.alias_record[inherited_alias_name] = self.join_paths(
                self.location, inherited_alias_target
            )

    def normalize_path(self: T, target_path: str) -> str:
        if target_path.startswith("@"):
            alias_name = target_path.removeprefix("@")
            assert alias_name in self.root.alias_record, (
                self.root.alias_record,
                alias_name,
            )
            return self.root.alias_record[alias_name]

        if self.is_relative_path(target_path):
            return self.translate_relative_path(target_path)

        return target_path


@dataclasses.dataclass
class FlangAST(SearchableTree):
    """
    Class that is like guardrails for developing flang generation. In future this may be removed and we'd
    only use the specification data structures
    """

    # links: dict[str, dict[str, list[str]]]
    # connection: str
    DUPLICATE_NODE_BRACKETS: ClassVar[tuple[str, str]] = ("(", ")")
    template_id: str

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError


@dataclasses.dataclass
class FlangBranch(FlangAST):
    filename: str | None = None

    def size(self) -> int:
        return sum(child.size() for child in self.children) if self.children else 0

    def diff(self, other: FlangBranch):
        if self.filename != other.filename:
            print(f"FILENAME DIFFERENT: {self.filename=} {other.filename=}")
            return False

        return super().diff(other)


@dataclasses.dataclass
class FlangLeaf(FlangAST):
    children: None = dataclasses.field(default=None, init=False)
    content: str

    def size(self) -> int:
        return len(self.content)

    def diff(self, other: FlangBranch):
        if self.content != other.content:
            print(f"CONTENT DIFFERENT: {self.content=} {other.content=}")
            return False

        return super().diff(other)


@dataclasses.dataclass
class TemplateRoot(SearchableTreeRoot, TemplateTree):
    type: str = dataclasses.field(default="", init=False, repr=False)
    text: None = dataclasses.field(default=None, init=False, repr=False)
    attributes: dict = dataclasses.field(default_factory=dict, init=False, repr=False)
    alias_record: None = dataclasses.field(default=None, init=False, repr=False)


@dataclasses.dataclass
class FlangRoot(SearchableTreeRoot, FlangBranch):
    template_id: str = dataclasses.field(default="", init=False, repr=False)
