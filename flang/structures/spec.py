from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Callable, Literal

# from .runtime import FlangProjectRuntime
from flang.helpers import convert_to_bool


@dataclasses.dataclass
class FlangConstruct:
    name: str
    attributes: dict
    children: list[str]
    text: str | None
    location: str

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        value = self.attributes.get(key)

        if value is None:
            return default
        return convert_to_bool(value)


@dataclasses.dataclass
class FlangMatchObject:
    identifier: str

    @property
    def first_child(self) -> FlangMatchObject:
        assert isinstance(self.content, list) and len(self.content) > 0
        child = self.content[0]
        return child

    def apply_function(
        self,
        evaluator_function: Callable[[FlangMatchObject], None],
        traversal_order: Literal["breadth-first", "depth-first"] = "breadth-first",
    ) -> None:
        if traversal_order == "breadth-first":
            evaluator_function(self)

        if isinstance(self.content, list):
            for item in self.content:
                item.apply_function(
                    evaluator_function, traversal_order
                )

        if traversal_order == "depth-first":
            evaluator_function(self)

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError
    
    @property
    def construct_name(self) -> str:
        return re.sub(r"\[\d+\]$", "", self.identifier)


@dataclasses.dataclass
class FlangAbstractMatchObject(FlangMatchObject):
    content: list[FlangTextMatchObject] | list[FlangAbstractMatchObject]
    filename: str | None

    def __len__(self) -> int:
        return sum(map(len, self.content))

    def get_raw_content(self) -> str | list[str]:
        if pathlib.Path(self.filename).is_dir():
            assert isinstance(self.content, list[FlangAbstractMatchObject])
            return [f.filename for f in self.content]

        assert isinstance(self.content, list[FlangTextMatchObject])

        return "".join(it.get_raw_content() for it in self.content)
        

# dataclass, not typing.TypedDict because we need methods
@dataclasses.dataclass
class FlangTextMatchObject(FlangMatchObject):
    content: str | list[FlangTextMatchObject]
    metadata: dict[str, str] = dataclasses.field(default_factory=dict)

    def __len__(self) -> int:
        if isinstance(self.content, list):
            return sum(map(len, self.content))
        return len(self.content)

    def get_raw_content(self) -> str:
        if isinstance(self.content, list):
            return "".join(it.get_raw_content() for it in self.content)

        return self.content

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
