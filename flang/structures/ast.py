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
    # reffers_to = default(None)

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        return convert_to_bool(self.attributes.get(key, default))

    def add_node(
        self, node: TemplateTree, allow_duplicates: bool = True
    ) -> SearchableTree:
        if not hasattr(self.root, "alias_record"):
            self.root.alias_record = {}

        old_record = getattr(node, "alias_record", {})

        super().add_node(node, allow_duplicates)

        for inherited_alias_name, inherited_alias_target in old_record.items():
            new_target = self.join_paths(self.location, inherited_alias_target)
            self.root.alias_record[inherited_alias_name] = new_target

        if alias := node.get_attrib("alias"):
            assert (
                alias not in self.root.alias_record
            ), f"Trying to set already existing alias: {alias}"
            self.root.alias_record[alias] = node.location

        return node

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

    DUPLICATE_NODE_BRACKETS: ClassVar[tuple[str, str]] = ("(", ")")
    template_id: str

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError

    def diff(self, other: FlangAST):
        if self.get_id() != other.get_id():
            print(f"NAME DIFFERENT: {self.get_id()=} {other.get_id()=}")
            return False

        if self.template_id != other.template_id:
            print(f"PATH DIFFERENT: {self.template_id=} {other.template_id=}")
            return False

        if self.children:
            if not other.children:
                return False

            if len(self.children) != len(other.children):
                print(
                    f"CHILDREN DIFFERENT: {self.get_id()=} {other.get_id()=}: \n{self.children=} \n{other.children=}"
                )
                print(ast_to_string(self))
                print("======")
                print(ast_to_string(other))
                print(self.location)
                return False

            return all(
                child1.diff(child2)
                for child1, child2 in zip(self.children, other.children)
            )

        return True


def ast_to_string(ast: FlangAST):
    if hasattr(ast, "content"):
        return ast.content
    if ast.children:
        return "".join(ast_to_string(child) for child in ast.children)
    return ""


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


@dataclasses.dataclass
class FlangRoot(SearchableTreeRoot, FlangBranch):
    template_id: str = dataclasses.field(default="", init=False, repr=False)
