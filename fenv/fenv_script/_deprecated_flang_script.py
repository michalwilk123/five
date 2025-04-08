import enum
import functools
import re


class Symbol(enum.Enum):
    STRING = r'"([^"]|\s)*"'
    KEYWORD = r"[_A-Za-z]\S*"
    INTEGER = "[0-9]|([1-9][0-9]+)"
    ARGUMENT = "{{.*}}"
    MACRO_START = "BEGIN"
    MACRO_END = "END"
    ASSIGNMENT_OPERAND = ":="
    SEMICOLON = ";"
    WHITESPACE = r"\s"
    COMMENT = r"#.*\n"


def define_match_function(function):

    @functools.wraps(function)
    def _inner(match_funcs):
        f = functools.partial(function, match_funcs)

        def _dinn(*args, **kwargs):
            r = f(*args, **kwargs)
            print(r)
            return r

        return _dinn

    return _inner


@define_match_function
def Or_(match_functions, content):
    all_matches = []

    for func in match_functions:
        matched = func(content)
        all_matches.append(matched)

    all_matches = [it for it in all_matches if it is not None]
    return max(all_matches, key=len) if all_matches else None


@define_match_function
def And_(match_functions, content):
    all_matches = []

    for func in match_functions:
        matched = func(content[len(all_matches) :])
        if matched is None:
            return None

        all_matches += matched

    return all_matches


@define_match_function
def Multi_(func, content):
    all_matches = None

    while True:
        matches = func(content[len(all_matches or []) :])

        if matches in (None, []):
            return all_matches or matches

        all_matches = (all_matches or []) + matches


@define_match_function
def Opt_(func, value):
    matches = func(value)
    return [] if matches is None else matches


@define_match_function
def Lit_(atom, lexems):
    _, matched = lexems[0]

    if lexems and atom == matched:
        return [lexems[0]]
    return None


@define_match_function
def Lex_(atom, lexems):
    lex_keyword, _ = lexems[0]

    if lexems and atom == lex_keyword:
        return [lexems[0]]
    return None


Operations = [Or_, And_, Multi_, Opt_]


def eval_operation(operation, arguments):
    return operation(arguments)


class FlangSyntaxParser:
    def __init__(self, *expressions, entrypoint) -> None:
        self.primitives = tuple(item.name for item in Symbol)
        self.constructs = {}

        for construct_name, syntax_body in expressions:
            self.constructs[construct_name] = self.generate_syntax(syntax_body)

        self.root = self.generate_syntax(entrypoint)

    def resolve_symbol(self, symbol):
        if isinstance(symbol, str):
            if symbol in self.constructs:
                return self.constructs[symbol]
            elif symbol in self.primitives:
                return Lex_(symbol)
            else:
                raise RuntimeError(symbol)

        return symbol

    def generate_syntax(self, syntax_body):
        if not isinstance(syntax_body, (list, tuple)):
            return self.resolve_symbol(syntax_body)

        expr = [self.generate_syntax(item) for item in syntax_body]

        if expr[0] in Operations:
            return eval_operation(*expr)

        return expr

    def evaluate(self, tokens): ...

    def parse_tokens(self, tokens):
        return self.root(tokens)


parser = FlangSyntaxParser(
    (
        "ASSIGNMENT_R_VALUE",
        (Or_, ("STRING", "INTEGER", "KEYWORD")),
    ),
    ("EMPTY_SPACE", (Multi_, "WHITESPACE")),
    (
        "ASSIGNMENT",
        (
            And_,
            (
                "KEYWORD",
                "EMPTY_SPACE",
                "ASSIGNMENT_OPERAND",
                "EMPTY_SPACE",
                "ASSIGNMENT_R_VALUE",
            ),
        ),
    ),
    ("ARGUMENTS", (And_, ("KEYWORD", (Opt_, (Multi_, "WHITESPACE"))))),
    ("ASSIGNMENT_LIST", (And_, ("ASSIGNMENT", (Opt_, (Multi_, "ASSIGNMENT"))))),
    (
        "MACRO_BODY",
        (
            And_,
            (
                "MACRO_START",
                (
                    Multi_,
                    (
                        Or_,
                        (
                            "STRING",
                            "INTEGER",
                            "KEYWORD",
                            "WHITESPACE",
                            "ARGUMENT",
                            "ASSIGNMENT_OPERAND",
                        ),
                    ),
                ),
                "MACRO_END",
            ),
        ),
    ),
    (
        "EXPRESSION_CALL",
        (
            And_,
            (
                "KEYWORD",
                "EMPTY_SPACE",
                "ARGUMENTS",
                "EMPTY_SPACE",
                (Opt_, "ASSIGNMENT_LIST"),
                "SEMICOLON",
            ),
        ),
    ),
    (
        "MACRO_CALL",
        (And_, ("KEYWORD", "EMPTY_SPACE", "ARGUMENTS", "EMPTY_SPACE", "MACRO_BODY")),
    ),
    ("COMMENT", "COMMENT"),
    entrypoint=(
        Opt_,
        (
            Multi_,
            (
                Or_,
                ("COMMENT", "EMPTY_SPACE", "EXPRESSION_CALL"),
                # ("COMMENT", "EMPTY_SPACE", "MACRO_CALL", "MACRO_BODY", "EXPRESSION_CALL"),
            ),
        ),
    ),
)


events = {}


def create_interpreter_context(): ...


def parse_command(): ...


def lexify_input(text_content: str):
    cursor = 0
    last_char_index = len(text_content)
    lexed = []

    while cursor < last_char_index:
        for item in Symbol:
            match_obj = re.match(item.value, text_content[cursor:])

            if match_obj is not None:
                break

        if match_obj is None:
            raise RuntimeError(text_content[cursor:15])

        lexed.append((item.name, match_obj.group()))
        cursor += len(match_obj.group())

    return lexed


def evaluate_script(input_text):
    lexed_tokens = lexify_input(input_text)
    ast = parser.parse_tokens(lexed_tokens)
    print(ast)


input_text = """
# comment
INSERT AFTER path.to.other.component FOR _ IN node.to.change;

MODIFY item 
    item.other.change := 2
    item.other.choice.value.text := x.sth.text
    FOR item IN path.to.other.component
    WHERE x := node.to.change;

DELETE NODE FOR node IN node.to.change;
COMMIT;

# this still works. Language is case insensitive for keywords
modify 
    node.to.change[1].value.text := path.to.other.component[2].text;
COmmit;

# this still works continuation:
modify 
    node.to.change[1].value.text := {{path.to.other.component[2].name with spaces .text}};
COmmit;


DEFINE REWRITE source target steps
START
    INSERT {{target}} AFTER item FOR item IN {{source}};
    MODIFY 
        {{steps}}
        FOR source IN {{source}}
        WHERE target := {{target}};
    DELETE node FOR node IN {{source}};
    COMMIT;
END;

REWRITE {{node.to.change}} {{path.to.other.component}} {{item.other.change := 2 item.other.choice.value.text := x.sth.text}};
"""

evaluate_script(input_text)
