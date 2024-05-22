import collections
import functools
import itertools
from typing import Callable, Iterable

BUILTIN_PATTERNS = {
    "vname": r"[A-Za-z]\w+",
    "number": r"-?(([1-9]+\d*)|0)(\.\d*)?",
    "string": r"((?:\\)\"[^\"]*(?:\\)\")|((?:\\)'[^\']*(?:\\)')",
}

global_anonymous_name_counter = collections.defaultdict(lambda: 0)
global_emitted_functions = []


def interlace(*iterables):
    for items_to_yield in itertools.zip_longest(*iterables):
        for item in items_to_yield:
            if item is not None:
                yield item


def create_unique_symbol(symbol: str) -> str:
    global global_anonymous_name_counter
    assert isinstance(symbol, str)

    generated_symbol = f"{symbol}@{global_anonymous_name_counter[symbol]}"
    global_anonymous_name_counter[symbol] += 1

    return generated_symbol


def convert_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    return value.lower() in ("t", "true", "1")


def compose(item: any, functions_to_apply: Iterable[Callable[[any], any]]):
    """
    Reverse of the `reduce` function takes an item and a iterable of
    functions and applies them sequentially to the item and the result of each
    function
    """
    return functools.reduce(
        lambda previous_result, f: f(previous_result), functions_to_apply, item
    )


def emit_function(name: str, args: list[str], body: str):
    global global_emitted_functions

    source = """
    """
