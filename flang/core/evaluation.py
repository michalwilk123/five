import collections
import re
from typing import Any

from flang.structures import (
    BaseUserAST,
    Event,
    EventStorage,
    FlangAST,
    UserASTAbstractNode,
)
from flang.utils.attributes import EVENT_PATTERN, EVENT_PRIORITY_PATTERN_STR

EventDictionary = dict[
    str, Event
]  # EventDictionary keys represents absolute paths to events from flang_ast
ParsedEventStringInfo = collections.namedtuple(
    "ParsedEventStringInfo", "priority trigger"
)


def create_event_from_node(flang_ast: FlangAST) -> Event:
    if source := flang_ast.get_attrib("source"):
        path, function_name = source.split(":")
        return Event.from_path(
            flang_ast.location, path, function_name, _kwargs=flang_ast.attributes.copy()
        )

    text_content = flang_ast.get_attrib("value", flang_ast.text)
    return Event.from_source_code(
        flang_ast.location, text_content, _kwargs=flang_ast.attributes.copy()
    )


def get_callback_from_path(path: str, events_dict: EventDictionary) -> Event:
    assert path in events_dict
    event = events_dict[path]
    return event


def parse_event_info(event_name_string: str) -> ParsedEventStringInfo:
    try:
        _, priority, trigger = re.split(EVENT_PRIORITY_PATTERN_STR, event_name_string)
        priority = int(re.search(r"\d+", priority).group())
    except (ValueError, AttributeError) as e:
        raise RuntimeError(
            f"Cannot match {event_name_string} with {EVENT_PRIORITY_PATTERN_STR}"
        ) from e

    return ParsedEventStringInfo(trigger=trigger, priority=priority)


def initialize_functions_for_events(flang_ast: FlangAST) -> dict[str, str]:
    event_dict = {}

    if flang_ast.type == "event":
        event_dict[flang_ast.location] = create_event_from_node(flang_ast)

    if isinstance(flang_ast.children, list):
        for child in flang_ast.children:
            sub_dict = initialize_functions_for_events(child)
            event_dict.update(sub_dict)

    return event_dict


def add_mapping_to_event_storage(
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
    event_dict: dict[str, str],
    event_kwargs: dict[str, Any],
) -> None:
    for name, event_function_location in event_dict.items():
        info = parse_event_info(name)
        event = global_events_dict[event_function_location]
        event_storage.add_event(info.trigger, info.priority, event, event_kwargs)


def normalize_event_dictionary(flang_ast: FlangAST, event_dict: dict[str, str]) -> str:
    normalized = {}

    for key, location in event_dict.items():
        normalized[key] = flang_ast.normalize_path(location)

    return normalized


def prepare_kwargs_for_event(
    user_ast: BaseUserAST, flang_ast: FlangAST
) -> dict[str, Any]:
    # NOTE: Maybe should use better name?
    user_ast_kwargs = {
        f"local_{f}": value for f, value in user_ast.to_shallow_dict().items()
    }
    flang_ast_kwargs = {
        f"global_{f}": value for f, value in flang_ast.to_shallow_dict().items()
    }
    prepared_kwargs = {
        **user_ast_kwargs,
        **flang_ast_kwargs,
        "local_parent": user_ast.parent,
        "global_parent": flang_ast.parent,
    }

    return prepared_kwargs


def add_triggers(
    user_ast: BaseUserAST,
    flang_ast: FlangAST,
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
) -> None:
    flang_ast_node = flang_ast.search_down_full_path(user_ast.flang_ast_path)

    if function_path := flang_ast_node.get_attrib("generate_events_fn"):
        kwargs_for_event = prepare_kwargs_for_event(user_ast, flang_ast)
        callback = global_events_dict[function_path]
        event_dict = callback(**kwargs_for_event)
        event_dict = normalize_event_dictionary(flang_ast_node, event_dict)

        add_mapping_to_event_storage(
            event_storage, global_events_dict, event_dict, kwargs_for_event
        )

    event_dict = {
        key: location
        for key, location in flang_ast_node.attributes.items()
        if EVENT_PATTERN.match(key)
    }

    if event_dict:
        kwargs_for_event = prepare_kwargs_for_event(user_ast, flang_ast)
        event_dict = normalize_event_dictionary(flang_ast_node, event_dict)
        add_mapping_to_event_storage(
            event_storage, global_events_dict, event_dict, kwargs_for_event
        )


def initialize_event_triggers_for_user_ast(
    user_ast: BaseUserAST,
    flang_ast: FlangAST,
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
) -> EventStorage:
    if not isinstance(user_ast, UserASTAbstractNode):
        add_triggers(user_ast, flang_ast, event_storage, global_events_dict)

    if user_ast.children is not None:
        for child in user_ast.children:
            initialize_event_triggers_for_user_ast(
                child, flang_ast, event_storage, global_events_dict
            )


def create_event_store(user_ast: BaseUserAST, flang_ast: FlangAST) -> EventStorage:
    global_events_dict = initialize_functions_for_events(flang_ast)
    event_storage = EventStorage()
    initialize_event_triggers_for_user_ast(
        user_ast, flang_ast, event_storage, global_events_dict
    )
    return event_storage
