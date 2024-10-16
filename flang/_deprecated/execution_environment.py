"""
Tried to implement universal and language agnostic version of this:

An Activation Record is a region of memory allocated during a procedure
call to store control information, parameter values, local variables,
and other necessary data specific to that procedure invocation.
"""

from __future__ import annotations

import dataclasses

from .searchable_tree import SearchableTree

"""
I    I         ROOTS (root is also an INTERNAL NODE, unless it is leaf)
|   /| 
|  I I         INTERNAL NODES
|  | |\  
O  O OO        EXTERNAL NODES (or leaves)

In flang, the believe is that links between declarations and refrences
can be described as a forest
"""


@dataclasses.dataclass
class ReferenceTree(SearchableTree):
    identifier: str
    symbol_name: str
    type: str = ""
    override: bool = True
    path_separator: str = dataclasses.field(
        compare=False,
        repr=False,
        init=False,
        default="->",
        metadata={"include_in_dict": False},
    )

    def __post_init__(self):
        super().__post_init__()
        if self.type == "":
            if self.parent is None:
                raise RuntimeError

            self.type = self.parent.type

    def get_node(self, needle: str) -> ReferenceTree | None:
        if self.identifier == needle:
            return self

        for child in self.children:
            if found_node := child.get_node(needle):
                return found_node

        return None


@dataclasses.dataclass
class SymbolDefinition:
    symbol_name: str
    type: str
    override: bool = True
    # scope: str
    # scope_end: str | None = None


@dataclasses.dataclass
class ExecutionEnvironment:
    # Forest f refrence trees
    definitions: list[SymbolDefinition]

    def declare(self, definition: SymbolDefinition): ...

    def refer(self): ...
