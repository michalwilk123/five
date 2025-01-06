import collections
import re
from typing import Any

from flang.structures import Event, EventStorage, FlangAST, FlangRoot, TemplateTree
from flang.utils.attributes import EVENT_PATTERN, EVENT_PRIORITY_PATTERN_STR

# EventDictionary keys represents absolute paths to events from template_tree
EventDictionary = dict[str, Event]
ParsedEventStringInfo = collections.namedtuple(
    "ParsedEventStringInfo", "priority trigger"
)


def create_event_from_node(template_tree: TemplateTree) -> Event:
    if source := template_tree.get_attrib("source"):
        path, function_name = source.split(":")
        return Event.from_path(
            template_tree.location,
            path,
            function_name,
            _kwargs=template_tree.attributes.copy(),
        )

    text_content = template_tree.get_attrib("value", template_tree.text)
    return Event.from_source_code(
        template_tree.location, text_content, _kwargs=template_tree.attributes.copy()
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


def initialize_functions_for_events(template_tree: TemplateTree) -> dict[str, str]:
    event_dict = {}

    if template_tree.type == "event":
        event_dict[template_tree.location] = create_event_from_node(template_tree)

    if isinstance(template_tree.children, list):
        for child in template_tree.children:
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


def normalize_event_dictionary(
    template_tree: TemplateTree, event_dict: dict[str, str]
) -> str:
    normalized = {}

    for key, location in event_dict.items():
        normalized[key] = template_tree.normalize_path(location)

    return normalized


def prepare_kwargs_for_event(
    flang_tree: FlangAST, template_tree: TemplateTree
) -> dict[str, Any]:
    # NOTE: Maybe should use better name?
    flang_tree_kwargs = {
        f"local_{f}": value for f, value in flang_tree.to_shallow_dict().items()
    }
    template_tree_kwargs = {
        f"global_{f}": value for f, value in template_tree.to_shallow_dict().items()
    }
    prepared_kwargs = {
        **flang_tree_kwargs,
        **template_tree_kwargs,
        "local_parent": flang_tree.parent,
        "global_parent": template_tree.parent,
    }

    return prepared_kwargs


def add_triggers(
    flang_tree: FlangAST,
    template_tree: TemplateTree,
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
) -> None:
    template = template_tree.search_down_full_path(flang_tree.template_id)

    if function_path := template.get_attrib("generate_events_fn"):
        kwargs_for_event = prepare_kwargs_for_event(flang_tree, template_tree)
        callback = global_events_dict[function_path]
        event_dict = callback(**kwargs_for_event)
        event_dict = normalize_event_dictionary(template, event_dict)

        add_mapping_to_event_storage(
            event_storage, global_events_dict, event_dict, kwargs_for_event
        )

    event_dict = {
        key: location
        for key, location in template.attributes.items()
        if EVENT_PATTERN.match(key)
    }

    if event_dict:
        kwargs_for_event = prepare_kwargs_for_event(flang_tree, template_tree)
        event_dict = normalize_event_dictionary(template, event_dict)
        add_mapping_to_event_storage(
            event_storage, global_events_dict, event_dict, kwargs_for_event
        )


def initialize_event_triggers_for_flang_tree(
    flang_tree: FlangAST,
    template_tree: TemplateTree,
    event_storage: EventStorage,
    global_events_dict: EventDictionary,
) -> EventStorage:
    if not isinstance(flang_tree, FlangRoot):
        add_triggers(flang_tree, template_tree, event_storage, global_events_dict)

    if flang_tree.children is not None:
        for child in flang_tree.children:
            initialize_event_triggers_for_flang_tree(
                child, template_tree, event_storage, global_events_dict
            )


def create_event_store(flang_tree: FlangAST, template_tree: TemplateTree) -> EventStorage:
    global_events_dict = initialize_functions_for_events(template_tree)
    event_storage = EventStorage()
    initialize_event_triggers_for_flang_tree(
        flang_tree, template_tree, event_storage, global_events_dict
    )
    return event_storage
