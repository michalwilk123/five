import abc
from .dataclasses import (
    IntermediateFlangTreeElement,
    FlangObject,
    BaseFlangConstruct,
)
from typing import TypeVar
import dataclasses

T = TypeVar("T")


class TextToIntermediateTreeParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, text: str) -> IntermediateFlangTreeElement:
        ...


class SingleFileParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, intermediate_tree: IntermediateFlangTreeElement) -> FlangObject:
        ...

    @abc.abstractmethod
    def get_constructs_classes(self) -> dict[str, BaseFlangConstruct]:
        ...


class FlangProcessor(abc.ABC):
    @abc.abstractmethod
    def __init__(self, flang_object: FlangObject):
        ...

    @abc.abstractmethod
    def forward(self, *args: any, **kwargs: any) -> any:
        ...

    @abc.abstractmethod
    def backward(self, *args: any, **kwargs: any) -> any:
        ...

    @property
    @abc.abstractmethod
    def forward_type(self) -> type:
        ...

    @property
    @abc.abstractmethod
    def backward_type(self) -> type:
        ...
