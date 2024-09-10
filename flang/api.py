from types import SimpleNamespace

from flang.helpers import kebab_to_snake_case
from flang.structures import FlangConstruct
from flang.utils import get_possible_construct_attributes


def build_construct_api(construct: FlangConstruct) -> object:
    callable_items = ["text", "location", "name", "children"]

    api_object = SimpleNamespace(
        {
            attr: construct.attributes.get(attr)
            for attr in map(
                kebab_to_snake_case, get_possible_construct_attributes(construct)
            )
        }
    )

    for callable_item in callable_items:
        setattr(api_object, callable_item, lambda: api_object)

    return api_object
