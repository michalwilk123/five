from __future__ import annotations

import dataclasses
import pathlib
from typing import Callable, Literal

from .constructs import FlangConstruct, FlangProjectConstruct


@dataclasses.dataclass
class FlangMatchObject:
    identifier: str

    @property
    def first_child(self) -> FlangMatchObject:
        assert isinstance(self.content, list) and len(self.content) > 0
        child = self.content[0]
        return child


@dataclasses.dataclass
class FlangAbstractMatchObject(FlangMatchObject):
    content: list[FlangTextMatchObject] | list[FlangAbstractMatchObject]
    filename: str | None


# dataclass, not typing.TypedDict because we need methods
@dataclasses.dataclass
class FlangTextMatchObject(FlangMatchObject):
    content: str | list[FlangTextMatchObject]
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def __len__(self) -> int:
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    def get_construct(self, project_construct: FlangProjectConstruct) -> FlangConstruct:
        return project_construct.find_symbol(self.identifier)

    def get_combined_text(self) -> str:
        assert (
            self.metadata.get("filename") is None
            or pathlib.Path(self.metadata["filename"]).is_dir() is False
        )

        if isinstance(self.content, list):
            return "".join(it.get_combined_text() for it in self.content)

        return self.content

    def get_raw_content(self) -> str | list[str]:
        if (
            self.metadata.get("filename")
            and pathlib.Path(self.metadata["filename"]).is_dir()
        ):
            assert isinstance(self.content, list)

            return [f.metadata["filename"] for f in self.content]

        return self.get_combined_text()

    def to_representation(self):
        if isinstance(self.content, list):
            return (
                self.identifier,
                [
                    child.to_representation()
                    for child in self.content
                    if child.identifier is not None
                ],
            )
        return (self.identifier, self.content)

    @classmethod
    def from_representation(cls, representation: tuple):
        raise NotImplementedError

    def evaluate_match_tree(
        self,
        evaluator_function: Callable[[FlangTextMatchObject], None],
        traversal_order: Literal["parent", "child"] = "child",
    ) -> None:
        if traversal_order == "parent":
            evaluator_function(self)

        if isinstance(self.content, list):
            for item in self.content:
                FlangTextMatchObject.evaluate_match_tree(
                    item, evaluator_function, traversal_order
                )

        if traversal_order == "child":
            evaluator_function(self)
