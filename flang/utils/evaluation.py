import collections
import re

from flang.structures import (
    BaseUserAST,
    Event,
    EventStorage,
    FlangAST,
    UserASTAbstractNode,
)
from flang.utils.attributes import EVENT_PATTERN, EVENT_PRIORITY_PATTERN_STR

EventDictionary = dict[str, Event]
ParsedEventStringInfo = collections.namedtuple(
    "ParsedEventStringInfo", "priority trigger"
)


def create_event_from_node(flang_ast: FlangAST) -> Event:
    # TODO: Should be able to pass user_ast parameters like value.content or sth like that
    if source := flang_ast.get_attrib("source"):
        path, function_name = source.split(":")
        return Event.from_path(
            flang_ast.location, path, function_name, _kwargs=flang_ast.attributes.copy()
        )

    text_content = flang_ast.get_attrib("value", flang_ast.text)
    return Event.from_source_code(
        flang_ast.location, text_content, _kwargs=flang_ast.attributes.copy()
    )


def get_callback_from_path(path: str, events_dict: EventDictionary):
    assert path in events_dict
    event = events_dict[path]
    return event


def parse_event_info(event_name_string: str) -> ParsedEventStringInfo:
    # try: except ValueError TODO: should be sth like error capture
    _, priority, trigger = re.split(EVENT_PRIORITY_PATTERN_STR, event_name_string)
    priority = int(re.search(r"\d+", priority).group())

    return ParsedEventStringInfo(trigger=trigger, priority=priority)


def create_events_from_flang_ast(flang_ast: FlangAST) -> EventDictionary:
    event_dict = {}

    if flang_ast.type == "event":
        event_dict[flang_ast.location] = create_event_from_node(flang_ast)

    if isinstance(flang_ast.children, list):
        for child in flang_ast.children:
            sub_dict = create_events_from_flang_ast(child)
            event_dict.update(sub_dict)

    return event_dict


def add_mapping_to_event_storage(
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
    ast_node: FlangAST,  # FIXME: This should take only raw attributes. ast_node should be ast_node.location
    event_dict: dict[str, str],
) -> None:
    for name, event_function_location in event_dict.items():
        info = parse_event_info(name)

        if ast_node.is_relative_path(event_function_location):
            event_function_location = ast_node.translate_relative_path(
                event_function_location
            )

        event = global_events_dict[event_function_location]
        event_storage.add_event(info.trigger, info.priority, event)


def add_triggers(
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
    user_ast: BaseUserAST,
    flang_ast: FlangAST,
):
    ast_node = flang_ast.search_down_full_path(user_ast.flang_ast_path)

    if function_path := ast_node.get_attrib("generate_events_fn"):
        callback = global_events_dict[function_path]
        event_dict = callback(**ast_node.attributes)
        add_mapping_to_event_storage(
            event_storage, global_events_dict, ast_node, event_dict
        )

    direct_events = {
        key: location
        for key, location in ast_node.attributes.items()
        if EVENT_PATTERN.match(key)
    }
    add_mapping_to_event_storage(
        event_storage, global_events_dict, ast_node, direct_events
    )


def initialize_event_triggers(
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
    user_ast: BaseUserAST,
    flang_ast: FlangAST,
) -> EventStorage:
    if not isinstance(user_ast, UserASTAbstractNode):
        add_triggers(event_storage, global_events_dict, user_ast, flang_ast)

    if user_ast.children is not None:
        for child in user_ast.children:
            initialize_event_triggers(event_storage, global_events_dict, child, flang_ast)


def create_event_store(user_ast: BaseUserAST, flang_ast: FlangAST) -> EventStorage:
    global_events_dict = create_events_from_flang_ast(flang_ast)
    event_storage = EventStorage()
    initialize_event_triggers(event_storage, global_events_dict, user_ast, flang_ast)
    return event_storage
