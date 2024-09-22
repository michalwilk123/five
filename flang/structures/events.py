from __future__ import annotations

import dataclasses
from collections import defaultdict
from typing import Callable, Generator

from flang.exceptions import UnknownParentException

FlangEvent = Callable[[], None]


@dataclasses.dataclass
class FlangLinkNode:
    vertex: str | None
    parent: str | None
    children: list[FlangLinkNode] = dataclasses.field(default_factory=list)
    is_leaf: bool = True

    def search_for_child(self, symbol: str) -> FlangLinkNode | None:
        if self.vertex is not None and self.vertex == symbol:
            return self

        if self.children:
            for child in self.children:
                if (node := child.search_for_child(symbol)) is not None:
                    return node

    def get_symbols(self, ensure_tree: bool = False) -> list[str]:
        if self.vertex is None:
            symbols = []
        else:
            symbols = [self.vertex]

        if self.children:
            for child in self.children:
                symbols += child.get_symbols(ensure_tree=ensure_tree)

            if ensure_tree and len(symbols) != len(set(symbols)):
                raise RuntimeError("")

        return symbols


class FlangLinkGraph:
    def __init__(self) -> None:
        self.link_forest = FlangLinkNode(vertex=None, parent=None, children=[])

    def add_relation(self, parent_symbol: str, child_symbol: str):
        parent_node = self.link_forest.search_for_child(parent_symbol)

        if parent_node is None:
            raise UnknownParentException(
                f"Could not find parent: {parent_node} for child: {child_symbol}"
            )

        child_node = self.link_forest.search_for_child(child_symbol)

        if child_node is None:
            child_node = FlangLinkNode(parent=parent_symbol, vertex=child_symbol)

        parent_node.children.append(child_node)

    def add_parent(self, parent_symbol: str):
        assert (
            self.link_forest.search_for_child(parent_symbol) is None
        ), f"Node: {parent_symbol} already exists! {self.link_forest}"

        self.link_forest.children.append(
            FlangLinkNode(parent=None, vertex=parent_symbol, is_leaf=False)
        )


class FlangEventQueue:
    def __init__(self) -> None:
        self.function_bank: dict[int, list[FlangEvent]] = defaultdict(list)

    def iterate_events(self) -> Generator[FlangEvent]:
        sorted_keys = sorted(self.function_bank.keys())

        for i in sorted_keys:
            for event in self.function_bank[i]:
                yield event