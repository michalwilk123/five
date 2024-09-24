from __future__ import annotations

import dataclasses
from collections import defaultdict

# from .constructs import FlangProjectRuntime
from typing import Callable, Generator

FlangEvent = Callable[[], None]


@dataclasses.dataclass
class FlangLink:
    source_symbol: str
    target_symbol: str
    relation_name: str

    # children: list[FlangLinkNode] = dataclasses.field(default_factory=list)
    # is_leaf: bool = True

    # def search_for_child(self, symbol: str) -> FlangLinkNode | None:
    #     if self.vertex is not None and self.vertex == symbol:
    #         return self

    #     if self.children:
    #         for child in self.children:
    #             if (node := child.search_for_child(symbol)) is not None:
    #                 return node

    # def get_symbols(self, ensure_tree: bool = False) -> list[str]:
    #     if self.vertex is None:
    #         symbols = []
    #     else:
    #         symbols = [self.vertex]

    #     if self.children:
    #         for child in self.children:
    #             symbols += child.get_symbols(ensure_tree=ensure_tree)

    #         if ensure_tree and len(symbols) != len(set(symbols)):
    #             raise RuntimeError("")

    #     return symbols

    # def add_relation(self, parent_symbol: str, child_symbol: str):
    #     parent_node = self.search_for_child(parent_symbol)

    #     if parent_node is None:
    #         raise UnknownParentException(
    #             f"Could not find parent: {parent_node} for child: {child_symbol}"
    #         )

    #     child_node = self.search_for_child(child_symbol)

    #     if child_node is None:
    #         child_node = FlangLinkNode(parent=parent_symbol, vertex=child_symbol)

    #     parent_node.children.append(child_node)

    # def add_parent_node(self, parent_symbol: str):
    #     assert (
    #         self.search_for_child(parent_symbol) is None
    #     ), f"Node: {parent_symbol} already exists! {self}"

    #     self.children.append(
    #         FlangLinkNode(parent=None, vertex=parent_symbol, is_leaf=False)
    #     )
    
    # def add_node(self, link_symbol:str, ):
    #     ...


class FlangEventQueue:
    def __init__(self) -> None:
        self.function_bank: dict[int, list[FlangEvent]] = defaultdict(list)

    def iterate_events(self) -> Generator[FlangEvent]:
        sorted_keys = sorted(self.function_bank.keys())

        for i in sorted_keys:
            for event in self.function_bank[i]:
                yield event
