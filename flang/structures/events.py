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

    @classmethod
    def _from_dict(
        cls, source_dictionary: dict, parent: ScopeTree | None
    ) -> list[ScopeTree]:
        nodes = []

        for symbol, children in source_dictionary.items():
            node = cls(symbol, parent=parent)
            if children:
                children_nodes = cls._from_dict(children, parent=node)
                node.children = children_nodes

            nodes.append(node)
        return nodes

    @classmethod
    def from_dict(cls, source_dictionary: dict) -> ScopeTree:
        tree = cls._from_dict(source_dictionary, None)
        assert len(tree) == 1
        return tree[0]
    
    def in_(self, parent_id:str, node_id:str, scope_end_node_id:str | None=None) -> bool:
        assert (parent := self.get_(parent_id)), f"Unknown parent node: {parent_id}"
        assert self.get_(node_id), f"Unknown node to search: {node_id}"

        if not parent.get_(node_id):
            False

        if scope_end_node_id:
            assert (scope_end_node := self.get_(scope_end_node_id)), f"Unknown end of scope node: {scope_end_node_id}"
            if scope_end_node.get_(node_id):
                return False
        
        return True
    
    def get_(self, node_id: str) -> ScopeTree | None:
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
