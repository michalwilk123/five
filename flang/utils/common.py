import sys
import textwrap
from pathlib import Path
from typing import Callable

VNAME = r"[A-Za-z]\w*"
INTEGER = r"[0-9]|([1-9][0-9]+)"
NUMBER = r"-?(([1-9]+\d*)|0)(\.\d*)?"
STRING = r'(?<!\\)(?:\\{2})*"(?:(?<!\\)(?:\\{2})*\\"|[^"])+(?<!\\)(?:\\{2})*"'
C_FUNCTION_CALL = rf"{VNAME}\({VNAME}(,\s*)?\)"
XML_ATTR = rf'{VNAME}="[^"\n]*"'
XML_OPEN_TAG = rf"<{VNAME}(\s*{XML_ATTR})*>"
XML_CLOSE_TAG = rf"</{VNAME}>"
XML_SINGLE_TAG = rf"<{VNAME}(\s*{XML_ATTR})*\s*/>"

SPECIAL_CHARS = {
    "lt": "<",
    "gt": ">",
}
BUILTIN_PATTERNS = {
    "vname": VNAME,
    "integer": INTEGER,
    "number": NUMBER,
    "string": STRING,
    "c_function_call": C_FUNCTION_CALL,
    "xml_open_tag": XML_OPEN_TAG,
    "xml_close_tag": XML_CLOSE_TAG,
    "xml_single_tag": XML_SINGLE_TAG,
    **SPECIAL_CHARS,
}
NAMED_BUILTIN_PATTERNS = {
    key: f"(?P<{key}>({value}))" for key, value in BUILTIN_PATTERNS.items()
}


def convert_to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    return value.lower() in ("t", "true", "1")


def create_callable_from_raw_code(code: str) -> Callable:
    namespace = {}
    formatted_code = textwrap.dedent(code)
    formatted_code = textwrap.indent(formatted_code, "    ")

    function = f"""\
def _generated_function(context, **kwargs):
{formatted_code}
"""

    exec(function, namespace)

    return namespace["_generated_function"]


def create_callable_from_pathname(path: str, function: str) -> Callable:
    path = Path(path)

    assert path.exists()
    assert path.is_file()

    name_without_ext = path.stem
    parent = path.parent

    module_path = str(parent.absolute())
    sys.path.append(module_path)

    try:
        module = __import__(name_without_ext)
        function = getattr(module, function)
    except AttributeError:
        raise RuntimeError(f"No function {function} available in {path}")

    sys.path.remove(module_path)
    return function
