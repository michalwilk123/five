import enum
import re


class Commands(enum.Enum):
    INSERT = "INSERT"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    DEFINE = "DEFINE"
    COMMIT = "COMMIT"


class LexSymbols(enum.Enum):
    SEMICOLON = ";"
    ASSIGNMENT_OPERAND = ":="
    FORLOOP_KW = re.compile("FOR", re.I)
    WHERE_KW = re.compile("WHERE", re.I)
    IN_KW = re.compile("IN", re.I)
    DEFINE_KW = re.compile("DEFINE", re.I)
    MACRO_START_KW = re.compile("BEGIN", re.I)
    MACRO_END_KW = re.compile("END", re.I)
    COMMIT_KW = re.compile("COMMIT", re.I)
    STRING = r'"([^"]|\s)*"'
    KEYWORD = r"[_A-Za-z][_A-Za-z0-9\[\]\-.]*"
    INTEGER = "([1-9][0-9]+)|[0-9]"
    TEMPLATE_ARGUMENT = "{{.*}}"
    WHITESPACE = r"\s"
    COMMENT = r"#.*"


def lexify_input(text_content: str):
    cursor = 0
    last_char_index = len(text_content)
    lexed = []

    while cursor < last_char_index:
        cands = []

        for item in LexSymbols:
            match_obj = re.match(item.value, text_content[cursor:])

            if match_obj is not None:
                cands.append((item.name, match_obj.group()))

        if cands == []:
            print(lexed)
            raise RuntimeError(text_content[cursor:])

        matched = max(cands, key=lambda item: len(item[1]))
        lexed.append(matched)
        cursor += len(matched[1])

    return lexed
