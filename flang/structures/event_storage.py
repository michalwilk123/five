import dataclasses
from collections import namedtuple
from copy import copy
from typing import Callable, TypeVar

from flang.utils.common import (
    create_callable_from_pathname,
    create_callable_from_raw_code,
)

T = TypeVar("T")


@dataclasses.dataclass
class Event:
    location: str
    callback: Callable = dataclasses.field(repr=False)
    kwargs: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def from_source_code(
        cls: T,
        location: str,
        source_code: str,
        _kwargs: dict | None = None,
    ) -> T:
        _kwargs = _kwargs or {}
        function = create_callable_from_raw_code(source_code)
        return cls(location=location, callback=function, kwargs=_kwargs)

    @classmethod
    def from_path(
        cls: T,
        location: str,
        path: str,
        function_name: str,
        _kwargs: dict | None = None,
    ) -> T:
        _kwargs = _kwargs or {}
        function = create_callable_from_pathname(path, function_name)
        return cls(location=location, callback=function, kwargs=_kwargs)

    def run(self, context: dict):
        return self.callback(context, **self.kwargs)


AnnotatedEvent = namedtuple("AnnotatedEvent", "event trigger priority")


@dataclasses.dataclass
class EventStorage:
    storage: list[AnnotatedEvent] = dataclasses.field(default_factory=list, init=False)

    def add_event(
        self,
        trigger: str,
        priority: int,
        event: Event,
        additional_event_kwargs: dict | None = None,
    ):
        additional_event_kwargs = additional_event_kwargs or {}
        event = copy(event)
        event.kwargs = {
            **event.kwargs,
            **additional_event_kwargs,
        }

        # NOTE: should be using bisect.insort / bisect.bisect
        self.storage.append(
            AnnotatedEvent(event=event, trigger=trigger, priority=priority)
        )

    def execute_iter(self, trigger: str):
        prepared_events = sorted(
            (event for event in self.storage if event.trigger == trigger),
            key=lambda it: it.priority,
            reverse=True,
        )
        context = {}

        for item in prepared_events:
            context = {**context}
            result = item.event.run(context)

            if result is not None:
                context = result

            yield context

    def execute_all(self, trigger: str, initial_context: dict | None = None):
        context = {} if initial_context is None else initial_context

        for new_context in self.execute_iter(trigger):
            context = new_context  # TODO: There should be maybe some logging?

        return context
