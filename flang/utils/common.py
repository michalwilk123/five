import functools
import itertools

VNAME = r"[A-Za-z]\w*"
INTEGER = r"[0-9]|([1-9][0-9]+)"
NUMBER = r"-?(([1-9]+\d*)|0)(\.\d*)?"
STRING = r'(?<!\\)(?:\\{2})*"(?:(?<!\\)(?:\\{2})*\\"|[^"])+(?<!\\)(?:\\{2})*"'
C_FUNCTION_CALL = rf"{VNAME}\({VNAME}(,\s*)?\)"
XML_ATTR = rf'{VNAME}="[^"\n]*"'
XML_OPEN_TAG = rf"<{VNAME}(\s*{XML_ATTR})*>"
XML_CLOSE_TAG = rf"</{VNAME}>"
XML_SINGLE_TAG = rf"<{VNAME}(\s*{XML_ATTR})*\s*/>"

BUILTIN_PATTERNS = {
    "vname": VNAME,
    "number": NUMBER,
    "string": STRING,
    "c_function_call": C_FUNCTION_CALL,
    "xml_open_tag": XML_OPEN_TAG,
    "xml_close_tag": XML_CLOSE_TAG,
    "xml_single_tag": XML_SINGLE_TAG,
    "lt": "<",
    "rt": ">",
}
NAMED_BUILTIN_PATTERNS = {
    key: f"(?P<{key}>({value}))" for key, value in BUILTIN_PATTERNS.items()
}


def interlace(*iterables):
    for items_to_yield in itertools.zip_longest(*iterables):
        for item in items_to_yield:
            if item is not None:
                yield item


def convert_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    return value.lower() in ("t", "true", "1")


def kebab_to_snake_case(name: str):
    return name.replace("-", "_")
