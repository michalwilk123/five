import random
from typing import Callable

from flang.core.utils import is_flang_node_hidden
from flang.structures import TemplateTree
from flang.utils.exceptions import ImpossibleOperationError, MissingSpecificationError
from flang.utils.regex import lex_storage

TEXT_CONTENT_KEY = "{}:content"
CHILDREN_KEY = "{}:children"
FILENAME_KEY = "{}:filename"

MissingSpecificationValueEvent = Callable[[TemplateTree, str], str | int | dict[str, int]]

def is_constant_cardinality(template: TemplateTree) -> bool:
    if template.parent and template.parent.type == "choice":
        return False

    return template.get_bool_attrib("hidden") or not (
        "multi" in template.attributes or "optional" in template.attributes
    )


def generate_random_value_for_key(template: TemplateTree, key: str):
    key_suffix = key.split(":")[-1]

    if TEXT_CONTENT_KEY.endswith(key_suffix):
        return lex_storage.generate_example(template.get_attrib("value", template.text))
    elif FILENAME_KEY.endswith(key_suffix):
        return lex_storage.generate_example(template.get_attrib("pattern"))
    elif CHILDREN_KEY.endswith(key_suffix):
        assert template.children

        count_dictionary = {}
        chosen_index = (
            random.randrange(len(template.children)) if template.type == "choice" else -1
        )

        for index, child_template in enumerate(template.children):
            if chosen_index != -1 and index != chosen_index:
                count = 0
            elif is_flang_node_hidden(child_template):
                count = 0
            elif is_constant_cardinality(child_template):
                count = 1
            else:
                number_choice = [1]

                if template.get_bool_attrib("multi"):
                    # NOTE: Adding muliple values makes it so the result tree explodes in branches number_choice += [2,3]
                    pass

                if template.get_bool_attrib("optional"):
                    number_choice += [0]

                count = random.choice(number_choice)

            count_dictionary[child_template.get_id()] = count
        
        return count_dictionary

    raise ImpossibleOperationError(f"Unknown key suffix: {key_suffix}")


def raise_exception_value_for_key(template: TemplateTree, key: str):
    raise MissingSpecificationError(template, key)
