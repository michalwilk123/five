from __future__ import annotations

import dataclasses
import datetime
from typing import Any, NamedTuple

from .ast import TemplateTree
from .specification import Specification


@dataclasses.dataclass
class Operation:
    signature: str
    timestamp: str = dataclasses.field(
        default_factory=lambda: datetime.datetime.now().isoformat(), init=False
    )
    arguments: dict[str, Any]

    def serialize(self) -> int:
        return (
            self.signature,
            self.timestamp,
            frozenset((k, v) for k, v in self.arguments.items()),
        )

    def get_hash(self):
        return str(hash(self.serialize()))


@dataclasses.dataclass
class OperationLog:
    log: list[Operation] = dataclasses.field(default_factory=list)
    head: int = dataclasses.field(default=0)

    def get_log(self):
        assert self.head < len(self.log) or self.head == len(self.log) == 0
        return self.log[self.head :]

    def append(self, *operations: Operation):
        self.log = list(operations) + self.log

    def get_hash(self):
        log = self.get_log()
        return log[0] if log else ""


class OperationState(NamedTuple):
    log: OperationLog
    template_tree: TemplateTree
    specification: Specification
