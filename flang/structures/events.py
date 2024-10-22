from __future__ import annotations

import dataclasses
from collections import ChainMap


@dataclasses.dataclass
class ScopeTree:
    symbol: str
    parent: ScopeTree | None
    children: list[ScopeTree] | None = None
    _cache: dict[str, ScopeTree] = dataclasses.field(
        default_factory=dict, init=False, repr=False
    )

    def to_dict(self) -> dict:
        return {
            self.symbol: (
                dict(ChainMap(*(child.to_dict() for child in self.children)))
                if isinstance(self.children, list)
                else None
            )
        }

    def add_nodes_from_dict(
        self, source_dictionary: dict, parent: ScopeTree | None
    ) -> None:
        if parent is None:
            parent = self

        for symbol, children in source_dictionary.items():
            node = self.add_node(parent.symbol, symbol)
            if children:
                self.add_nodes_from_dict(children, parent=node)

    @classmethod
    def from_dict(cls, source_dictionary: dict) -> ScopeTree:
        root_symbol = next(iter(source_dictionary.keys()))
        tree = cls(root_symbol, parent=None)
        tree.add_nodes_from_dict(source_dictionary[root_symbol], None)
        return tree

    def contains(self, node_id: str, scope_end_node_id: str | None = None) -> bool:
        if not self.get_(node_id):
            return False

        if scope_end_node_id:
            assert (
                scope_end_node := self.get_(scope_end_node_id)
            ), f"Unknown end of scope node: {scope_end_node_id}"
            if scope_end_node.get_(node_id):
                return False

        return True

    def get_(self, node_id: str) -> ScopeTree | None:
        if self.symbol == node_id:
            return self

        return self._cache.get(node_id)

    def add_node(self, parent_id: str, node_id: str) -> ScopeTree:
        if parent_id == self.symbol:
            assert node_id not in self._cache, "Cannot add same node multiple times"
            new_node = ScopeTree(node_id, parent=self)

            if self.children is None:
                self.children = []

            self.children.append(new_node)
        elif parent_id in self._cache:
            parent = self._cache[parent_id]
            new_node = parent.add_node(parent_id, node_id)
        else:
            raise RuntimeError(f"{parent_id=} {node_id=}")

        current = self

        while current is not None:
            current._cache[node_id] = new_node
            current = current.parent

        return new_node
