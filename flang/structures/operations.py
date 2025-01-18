from __future__ import annotations

import dataclasses
from typing import Any, Callable


def dict_hash(d):
    if isinstance(d, dict):
        return hash(frozenset((k, dict_hash(v)) for k, v in d.items()))
    return hash(d)


@dataclasses.dataclass
class Operation:
    signature: str
    arguments: dict[str, Any]
    _hash: str | None

    def serialize(self) -> int:
        return (self.signature, frozenset((k, v) for k, v in self.arguments.items()))

    def get_hash(self):
        return self._hash or str(hash(self.serialize()))

    def execute(self, function: Callable):
        return function(**self.arguments)

    # def execute(self) -> Operation:
    #     reversable = _OPERATION_COLLECTION[self.signature](**self.arguments)

    #     assert isinstance(reversable, Operation)
    #     return reversable


@dataclasses.dataclass
class OperationLog:
    log: list[Operation] = dataclasses.field(default_factory=list)
    head: int = dataclasses.field(default=0)

    def get_log(self):
        assert self.head < len(self.log)

        return self.log[self.head :]

    def append(self, *operations: Operation):
        self.log = list(operations) + self.log

    def get_hash(): ...
