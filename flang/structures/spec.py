from __future__ import annotations

import dataclasses
import pathlib
import re
from typing import Literal

from flang.utils.common import convert_to_bool


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
    content: ...

    @property
    def first_child(self) -> FlangMatchObject:
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

    def __len__(self):
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
class FlangDirectoryMatchObject(FlangMatchObject):
    identifier: str
    content: list[FlangFlatFileMatchObject]
    filename: str

    def __len__(self) -> int:
        return sum(map(len, self.content))

    def get_raw_content(self) -> str | list[str]:
        assert pathlib.Path(self.filename).is_dir()
        return [f.filename for f in self.content]


@dataclasses.dataclass
class FlangTextMatchObject(FlangMatchObject):
    identifier: str
    content: str

    def __len__(self) -> int:
        return len(self.content)

    def get_raw_content(self) -> str:
        return self.content


@dataclasses.dataclass
class FlangComplexMatchObject(FlangMatchObject):
    identifier: str
    content: list[FlangTextMatchObject | FlangComplexMatchObject]

    def __len__(self) -> int:
        return sum(map(len, self.content))

    def get_raw_content(self) -> str:
        return "".join(it.get_raw_content() for it in self.content)


@dataclasses.dataclass
class FlangFlatFileMatchObject(FlangComplexMatchObject):
    filename: str


# kw_only=True is added because we override the old field and add a default value
@dataclasses.dataclass(kw_only=True)
class FlangAbstractMatchObject(FlangMatchObject):
    content: list[FlangMatchObject]
    identifier: Literal["__abstract_match__"] = "__abstract_match__"


FlangFileMatch = FlangDirectoryMatchObject | FlangFlatFileMatchObject
RootFlangMatchObject = FlangFileMatch | FlangAbstractMatchObject
