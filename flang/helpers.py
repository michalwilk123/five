import functools
import itertools

import flang.regex_lib as r

BUILTIN_PATTERNS = {
    "vname": r.VNAME,
    "number": r.NUMBER,
    "string": r.STRING,
    "c_function_call": r.C_FUNCTION_CALL,
    "xml_open_tag": r.XML_OPEN_TAG,
    "xml_close_tag": r.XML_CLOSE_TAG,
    "xml_single_tag": r.XML_SINGLE_TAG,
    "lt": "<",
    "rt": ">",
}
NAMED_BUILTIN_PATTERNS = {
    key: f"(?P<{key}>({value}))" for key, value in BUILTIN_PATTERNS.items()
}

global_emitted_functions = []


def interlace(*iterables):
    for items_to_yield in itertools.zip_longest(*iterables):
        for item in items_to_yield:
            if item is not None:
                yield item


def convert_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    return value.lower() in ("t", "true", "1")


# TODO unused
def compose(item, functions_to_apply):
    """
    Reverse of the `reduce` function takes an item and a iterable of
    functions and applies them sequentially to the item and the result of each
    function
    """
    return functools.reduce(
        lambda previous_result, f: f(previous_result), functions_to_apply, item
    )


def kebab_to_snake_case(name: str):
    return name.replace("-", "_")


def emit_function(name: str, args: list[str], body: str):
    global global_emitted_functions

    source = """
    """
