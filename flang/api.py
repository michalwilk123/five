from types import SimpleNamespace

from flang.structures import FlangAST
from flang.utils.attributes import get_possible_construct_attributes
from flang.utils.common import kebab_to_snake_case


def build_construct_api(construct: FlangAST) -> object:
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
