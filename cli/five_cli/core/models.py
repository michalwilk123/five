from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Literal
from urllib.parse import parse_qsl, urlencode


@dataclasses.dataclass
class Message:
    role: Literal['user', 'assistant']
    content: str | None
    arguments: dict | None
    results: dict | None
    type: Literal['text', 'tool_use', 'tool_result']


@dataclasses.dataclass
class Conversation:
    user_prompt: str
    messages: list[Message]
    temperature: float
    model_name: str


@dataclasses.dataclass
class TaskChangePatch:
    id: str
    type: Literal['user', 'assistant'] # todo: this should be a part of CompletedTask
    # content: str

    def encode(self) -> str:
        params = {'id': self.id, 'type': self.type}
        return urlencode(params)

    @staticmethod
    def decode(message: str) -> TaskChangePatch:
        params = dict(parse_qsl(message.strip()))
        return TaskChangePatch(id=params['id'], type=params['type'])


@dataclasses.dataclass
class CompletedTask:
    references: list[str]
    conversation: Conversation
    changes: TaskChangePatch
    id: int = 0
    timestamp: str = dataclasses.field(default_factory=lambda: datetime.now().isoformat())
