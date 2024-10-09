from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Literal
from .common import SearchableTree

from flang.utils.common import convert_to_bool


@dataclasses.dataclass
class NewFlangConstruct(SearchableTree):
    type: str
    attributes: dict
    text: str | None

    def get_attrib(self, key: str, default=None):
        return self.attributes.get(key, default)

    def get_bool_attrib(self, key: str, default=False):
        return convert_to_bool(self.attributes.get(key, default))

class FlangFileMatchMixin:
    ...

class FlangComplexMatchMixin:
    ...

@dataclasses.dataclass
class BaseFlangMatchObject(SearchableTree):
    identifier: str
    # TODO: This should have reference to the construct file

    @property
    def first_child(self) -> BaseFlangMatchObject:
        assert isinstance(self.content, list) and len(self.content) > 0
        child = self.content[0]
        return child

    def get_raw_content(self) -> str | list[str]:
        raise NotImplementedError

    @staticmethod
    def get_construct_name_from_spec_name(identifier: str) -> str:
        return re.sub(r"\[\d+\]$", "", identifier)

    @property
    def construct_name(self) -> str:
        return self.get_construct_name_from_spec_name(self.identifier)

    def size(self):
        raise NotImplementedError

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


@dataclasses.dataclass
class FlangDirectoryMatchObject(BaseFlangMatchObject):
    identifier: str
    content: list[FlangFlatFileMatchObject]
    filename: str

    def size(self) -> int:
        # len does not make sense
        return sum(map(len, self.content))

    def get_raw_content(self) -> str | list[str]:
        assert pathlib.Path(self.filename).is_dir()
        return [f.filename for f in self.content]


@dataclasses.dataclass
class FlangTextMatchObject(BaseFlangMatchObject):
    identifier: str
    content: str

    def size(self) -> int:
        return len(self.content)

    def get_raw_content(self) -> str:
        return self.content


@dataclasses.dataclass
class FlangComplexMatchObject(BaseFlangMatchObject):
    identifier: str
    content: list[BaseFlangMatchObject]

    def size(self) -> int:
        return sum(map(len, self.content))

    def get_raw_content(self) -> str:
        return "".join(it.get_raw_content() for it in self.content)


@dataclasses.dataclass
class FlangFlatFileMatchObject(FlangComplexMatchObject):
    filename: str


# kw_only=True is added because we override the old field and add a default value
@dataclasses.dataclass(kw_only=True)
class FlangAbstractMatchObject(BaseFlangMatchObject):
    content: list[BaseFlangMatchObject]
    identifier: Literal["__abstract_match__"] = "__abstract_match__"


FlangFileMatch = FlangDirectoryMatchObject | FlangFlatFileMatchObject
RootFlangMatchObject = FlangFileMatch | FlangAbstractMatchObject
