import dataclasses
import functools
import itertools
from collections.abc import Callable

from .atoms import And_, Lex_, Literal_, Multi_, Opt_, Or_, get_constr_size
from .lex import LexSymbols, lexify_input


@dataclasses.dataclass
class FenvConstruct:
    name: str
    body: tuple
    event: Callable | None = None


@dataclasses.dataclass
class FenvEvaluatedConstruct:
    name: str
    function: Callable | None = None
    event: Callable | None = None


def Ref_(construct: FenvEvaluatedConstruct, tokens):
    parsed = construct.function(tokens)

    if parsed is not None:
        if construct.event is not None:
            construct.event(parsed)

    return [(construct.name, parsed)] if parsed is not None else None


def listof(construct, separator):
    return (And_, construct, (Opt_, (Multi_, (And_, separator, construct))))


def manyof(*constrs):
    return (Multi_, (Or_, *constrs))


def interlaced(*constrs, _with=None):
    assert _with is not None
    return tuple(itertools.chain(*zip(constrs, itertools.repeat(_with))))[:-1]


AssignmentRValue = FenvConstruct(
    "ASSIGNMENT_R_VALUE",
    (
        Or_,
        (Lex_, "STRING"),
        (Lex_, "INTEGER"),
        (Lex_, "KEYWORD"),
        (Lex_, "TEMPLATE_ARGUMENT"),
    ),
)

EmptySpace = FenvConstruct("EMPTY_SPACE", (Multi_, (Lex_, "WHITESPACE")))

Assignment = FenvConstruct(
    "ASSIGNMENT",
    (
        And_,
        *interlaced(
            (Lex_, "KEYWORD"),
            (Lex_, "ASSIGNMENT_OPERAND"),
            (Ref_, "ASSIGNMENT_R_VALUE"),
            _with=(Or_, (Ref_, "EMPTY_SPACE")),
        ),
    ),
)

Arguments = FenvConstruct(
    "ARGUMENT", (Or_, (Lex_, "KEYWORD"), (Lex_, "TEMPLATE_ARGUMENT"))
)

AssignmentList = FenvConstruct(
    "ASSIGNMENT_LIST", listof((Ref_, "ASSIGNMENT"), (Ref_, "EMPTY_SPACE"))
)

MacroBody = FenvConstruct(
    "MACRO_BODY",
    (
        And_,
        (Lex_, "MACRO_START_KW"),
        manyof(
            (Lex_, "STRING"),
            (Lex_, "INTEGER"),
            (Lex_, "KEYWORD"),
            (Lex_, "WHITESPACE"),
            (Lex_, "TEMPLATE_ARGUMENT"),
            (Lex_, "ASSIGNMENT_OPERAND"),
            (Lex_, "IN_KW"),
            (Lex_, "FORLOOP_KW"),
            (Lex_, "WHERE_KW"),
            (Lex_, "COMMIT_KW"),
            (Lex_, "SEMICOLON"),
        ),
        (Lex_, "MACRO_END_KW"),
    ),
)

# should expand this below
ExpressionCall = FenvConstruct(
    "EXPRESSION_CALL",
    (
        And_,
        (Lex_, "KEYWORD"),
        (Ref_, "EMPTY_SPACE"),
        manyof((Ref_, "ARGUMENT"), (Ref_, "ASSIGNMENT"), (Ref_, "EMPTY_SPACE")),
    ),
)

ExpressionForLoop = FenvConstruct(
    "EXPRESSION_FORLOOP",
    (
        And_,
        *interlaced(
            (Lex_, "FORLOOP_KW"),
            (Lex_, "KEYWORD"),
            (Lex_, "IN_KW"),
            (Lex_, "KEYWORD"),
            _with=(Ref_, "EMPTY_SPACE"),
        ),
    ),
)

ExpressionWhereStatement = FenvConstruct(
    "EXPRESSION_WHERE_SMT",
    (
        And_,
        (Lex_, "WHERE_KW"),
        (Ref_, "EMPTY_SPACE"),
        (Ref_, "ASSIGNMENT"),
    ),
)

FullExpressionCall = FenvConstruct(
    "FULL_EXPRESSION_CALL",
    (
        And_,
        (Ref_, "EXPRESSION_CALL"),
        (
            Opt_,
            manyof(
                (Ref_, "EMPTY_SPACE"),
                (Ref_, "EXPRESSION_FORLOOP"),
                (Ref_, "EXPRESSION_WHERE_SMT"),
            ),
        ),
        (Lex_, "SEMICOLON"),
    ),
)

MacroDefinition = FenvConstruct(
    "MACRO_DEFINITION",
    (
        And_,
        (Lex_, "DEFINE_KW"),
        manyof((Ref_, "ARGUMENT"), (Ref_, "ASSIGNMENT"), (Ref_, "EMPTY_SPACE")),
        (Ref_, "MACRO_BODY"),
        (Lex_, "SEMICOLON"),
    ),
)

Transaction = FenvConstruct(
    "TRANSACTION",
    (
        And_,
        manyof(
            (Ref_, "EMPTY_SPACE"),
            (Lex_, "COMMENT"),
            (Ref_, "FULL_EXPRESSION_CALL"),
            (Ref_, "MACRO_DEFINITION"),
        ),
        (Lex_, "COMMIT_KW"),
        (Lex_, "SEMICOLON"),
        (Opt_, (Ref_, "EMPTY_SPACE")),
    ),
)

Root = FenvConstruct(
    "ROOT",
    (Opt_, manyof((Lex_, "COMMENT"), (Ref_, "EMPTY_SPACE"), (Ref_, "TRANSACTION"))),
)


class SyntaxParser:
    def __init__(self, expressions: list[FenvConstruct], entrypoint) -> None:
        self.constuct_dict = {}

        for expr in expressions:
            self.constuct_dict[expr.name] = FenvEvaluatedConstruct(
                name=expr.name,
                function=self.evaluate_expression(expr.body),
                event=expr.event,
            )

        self.entrypoint = entrypoint

    def evaluate_expression(self, construct_body: tuple):
        function, *raw_args = construct_body

        if function is Ref_:
            assert (
                raw_args[0] in self.constuct_dict
            ), f"Symbol {raw_args[0]} is not declared and cannot be referenced"

            return functools.partial(function, self.constuct_dict[raw_args[0]])
        elif function is Literal_:
            return functools.partial(function, raw_args[0])
        elif function is Lex_:
            assert hasattr(LexSymbols, raw_args[0])

            return functools.partial(function, raw_args[0])

        arguments = [self.evaluate_expression(arg) for arg in raw_args]

        if function in (Multi_, Opt_):
            assert len(arguments) == 1
            return function(arguments[0])

        return function(arguments)

    def execute(self, content: str):
        tokens = lexify_input(content)
        root = self.constuct_dict[self.entrypoint]

        toks = root.function(tokens) or []
        assert get_constr_size(toks) == len(
            tokens
        ), f"Text not parsed! Text left: {''.join(it for _, it in tokens[get_constr_size(toks):])}"

        return toks


parser = SyntaxParser(
    [
        AssignmentRValue,
        EmptySpace,
        Assignment,
        Arguments,
        AssignmentList,
        MacroBody,
        ExpressionCall,
        ExpressionForLoop,
        ExpressionWhereStatement,
        FullExpressionCall,
        MacroDefinition,
        Transaction,
        Root,
    ],
    entrypoint="ROOT",
)
