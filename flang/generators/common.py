import random
from typing import Callable

from flang.structures import TemplateTree
from flang.utils.exceptions import ImpossibleOperationError, MissingSpecificationError
from flang.utils.regex import lex_storage

TEXT_CONTENT_KEY = "{}:content"
CHOICE_INDEX_KEY = "{}:choice-index"
CHILDREN_KEY = "{}:children"
FILENAME_KEY = "{}:filename"

MissingSpecificationValueEvent = Callable[[TemplateTree, str], str | int]


def is_constant_cardinality(template: TemplateTree) -> bool:
    return template.get_bool_attrib("hidden") or not (
        "multi" in template.attributes or "optional" in template.attributes
    )


def generate_random_value_for_key(template: TemplateTree, key: str):
    key_suffix = key.split(":")[-1]

    if TEXT_CONTENT_KEY.endswith(key_suffix):
        return lex_storage.generate_example(template.get_attrib("value", template.text))
    elif CHOICE_INDEX_KEY.endswith(key_suffix):
        return random.randrange(len(template.children))
    elif FILENAME_KEY.endswith(key_suffix):
        return lex_storage.generate_example(template.get_attrib("pattern"))
    elif CHILDREN_KEY.endswith(key_suffix):
        number_choice = [1]

        if template.get_bool_attrib("multi"):
            # NOTE: Adding muliple values makes it so the result tree explodes in branches number_choice += [2,3]
            pass

        if template.get_bool_attrib("optional"):
            number_choice += [0]

        return random.choice(number_choice)

    raise ImpossibleOperationError(f"Unknown key suffix: {key_suffix} | ")


def raise_exception_value_for_key(template: TemplateTree, key: str):
    raise MissingSpecificationError(template, key)
