import fnmatch
import random

from flang.structures import BaseUserAST, FlangAST, UserBranch, UserLeaf, UserRoot
from flang.utils.exceptions import SymbolNotFoundError
from flang.utils.regex import lex_storage

from .utils import get_cardinality_key, resolve_use_node


class GeneratorSetup:
    def __init__(self, ast: FlangAST) -> None:
        self.patches: dict[str, str | int] = {}
        self.enforce_full_specification: bool = False
        self.ast = ast

    def _generate_random_content(self, location: str):
        flang_node = self.ast.full_search(location)

        if flang_node is None:
            raise SymbolNotFoundError

        if flang_node.type == "sequence":
            return None
        elif flang_node.type == "choice":
            return random.randrange(len(flang_node.children))
        elif flang_node.type == "text":
            flang_ast_text = flang_node.get_attrib("value", flang_node.text)
            return (
                lex_storage.generate_example(flang_ast_text)
                if flang_node.get_bool_attrib("regex")
                else flang_ast_text
            )
        elif flang_node.type == "file":
            filename = flang_node.get_attrib("filename")
            return (
                lex_storage.generate_example(filename)
                if flang_node.get_attrib("variant") == "regex"
                else filename
            )

        raise RuntimeError

    def _generate_cardinality(self, flang_node: FlangAST):
        if flang_node.get_bool_attrib("hidden"):
            return 0

        number_choice = [1]

        if flang_node.get_bool_attrib("multi"):
            number_choice = number_choice + [2, 3]

        if flang_node.get_bool_attrib("optional"):
            number_choice = number_choice + [0]

        return random.choice(number_choice)

    def get_cardinality(self, flang_node: BaseUserAST):
        cardinality_key = get_cardinality_key(flang_node.location)

        for key, value in self.patches.items():
            if fnmatch.fnmatchcase(cardinality_key, key):
                return value

        return self._generate_cardinality(flang_node)

    def get(self, node: BaseUserAST):
        location = node.location

        for key, value in self.patches.items():
            if fnmatch.fnmatchcase(location, key):
                return value

        return self._generate_random_content(node.flang_ast_path)


def create_empty_setup(flang_ast: FlangAST):
    return GeneratorSetup(flang_ast)


def generate_empty_node(flang_ast: FlangAST) -> BaseUserAST:
    if flang_ast.type == "sequence":
        return UserBranch(
            flang_ast_path=flang_ast.location, name=flang_ast.name, children=[]
        )
    elif flang_ast.type == "choice":
        return UserBranch(
            flang_ast_path=flang_ast.location, name=flang_ast.name, children=[]
        )
    elif flang_ast.type == "text":
        return UserLeaf(
            flang_ast_path=flang_ast.location, name=flang_ast.name, content="dummy_text"
        )
    elif flang_ast.type == "regex":
        return UserLeaf(
            flang_ast_path=flang_ast.location,
            name=flang_ast.name,
            content="dummy_[0-9]regex",
        )
    elif flang_ast.type == "use":
        resolved_node = resolve_use_node(flang_ast)
        return generate_empty_node(resolved_node)
    elif flang_ast.type == "file":
        return UserBranch(
            filename="dummy-name",
            children=[],
            flang_ast_path=flang_ast.location,
            name=flang_ast.name,
        )


def fill_node_content(
    flang_ast: FlangAST, node_to_fill: BaseUserAST, data
) -> list | None:
    if flang_ast.type == "sequence":
        assert isinstance(node_to_fill, UserBranch)
        return [child for child in flang_ast.children]

    elif flang_ast.type == "choice":
        assert isinstance(node_to_fill, UserBranch)
        chosen_child = flang_ast.children[data]

        if chosen_child.get_bool_attrib("terminal"):
            node_to_fill.is_terminal = None

        return [chosen_child]
    elif flang_ast.type == "text" or flang_ast.type == "regex":
        assert isinstance(node_to_fill, UserLeaf)
        node_to_fill.content = data
        return None
    elif flang_ast.type == "use":
        assert 0, "ImpossibleOperationError"
    elif flang_ast.type == "file":
        assert isinstance(node_to_fill, UserBranch)

        node_to_fill.filename = data
        return [child for child in flang_ast.children]

    assert 0, "ImpossibleOperationError"


def generate_filled_node_with_cardinality(
    flang_node: FlangAST, parent: BaseUserAST, setup: GeneratorSetup
) -> None:
    if flang_node.get_bool_attrib("hidden") or flang_node.type in ["event"]:
        return

    quantity = setup.get_cardinality(flang_node)

    for _ in range(quantity):
        node = generate_empty_node(flang_node)
        flang_node = flang_node.full_search(node.flang_ast_path)

        assert flang_node is not None

        parent.add_node(node)
        data = setup.get(node)
        children_to_setup = fill_node_content(flang_node, node, data) or []

        for child in children_to_setup:
            generate_filled_node_with_cardinality(child, node, setup)

        if hasattr(node, "is_terminal"):
            break


def generate_ast(flang_ast: FlangAST, setup=None):
    setup = setup or create_empty_setup(flang_ast)
    root = UserRoot()

    generate_filled_node_with_cardinality(flang_ast, root, setup)

    return root
