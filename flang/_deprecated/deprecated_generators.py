import fnmatch
import random

from flang.structures import BaseUserAST, FlangAST, UserBranch, UserLeaf, UserRoot
from flang.utils.exceptions import SymbolNotFoundError
from flang.utils.regex import lex_storage

from .core.utils import get_cardinality_key, resolve_use_node


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


## Second try on the generators, also deprecated

import random

from flang.structures import BaseUserAST, FlangAST, UserBranch, UserLeaf, UserRoot
from flang.utils.regex import lex_storage


class SpecificationKeyValueStore(dict):
    def get_cardinality_key(self, parent_location: str, child_name: str) -> str:
        return f"{parent_location}::card({child_name})"

    def set_cardinality(
        self, parent_location: str, child_name: str, cardinality: int
    ) -> str:
        assert isinstance(cardinality, int)
        key = self.get_cardinality_key(parent_location, child_name)
        self[key] = cardinality

    def get_cardinality(self, parent_location: str, child_name: str) -> int:
        return self.get(self.get_cardinality_key(parent_location, child_name))

    def get_choice_node_key(self, location: str) -> str:
        return f"{location}::choice"

    def get_choice_node(self, location: str):
        return self.get(self.get_choice_node_key(location))

    def set_choice_node(self, location: str, chosen_node: str):
        assert isinstance(chosen_node, str)
        key = self.get_choice_node_key(location)
        self[key] = chosen_node

    def get_regex_content_key(self, location: str) -> str:
        return f"{location}::regex"

    def get_regex_content(self, location: str) -> str:
        return self.get(self.get_regex_content_key(location))

    def set_regex_content(self, location: str, content: str):
        self[self.get_regex_content_key(location)] = content


def get_node_cardinality(
    flang_node: FlangAST, parent_location: str, specification: SpecificationKeyValueStore
):
    quantity = specification.get_cardinality(parent_location, flang_node.name)

    if quantity is not None:
        return quantity

    if flang_node.get_bool_attrib("hidden") or flang_node.type in ["event"]:
        return 0

    number_choice = [1]

    if flang_node.get_bool_attrib("multi"):
        number_choice = number_choice + [2, 3]

    if flang_node.get_bool_attrib("optional"):
        number_choice = number_choice + [0]

    quantity = random.choice(number_choice)

    return quantity


def get_choice_node(
    flang_node: FlangAST, parent_location: str, specification: SpecificationKeyValueStore
) -> int:
    chosen_node = specification.get_cardinality(parent_location, flang_node.name)

    if chosen_node is not None:
        return chosen_node

    return random.randrange(len(flang_node.children))


def get_regex_content(
    flang_node: FlangAST, node_location: str, specification: SpecificationKeyValueStore
) -> int:
    content = specification.get_regex_content(node_location, flang_node.name)

    if content is not None:
        return content

    content = flang_node.get_attrib("value", flang_node.text)

    return lex_storage.generate_example(content)


def determine_node_and_children(
    flang_node: FlangAST,
    parent_node: BaseUserAST,
    node_index: int,
    spec: SpecificationKeyValueStore,
) -> BaseUserAST:
    assert flang_node is not None

    node_name = parent_node.generate_child_name(amount_of_duplicates=node_index)
    node_location = parent_node.join_paths(parent_node.location, node_name)

    if flang_node.type == "sequence":
        return (
            UserBranch(flang_ast_path=flang_node.location, name=node_name),
            flang_node.children,
        )
    elif flang_node.type == "choice":
        node = UserBranch(flang_ast_path=flang_node.location, name=node_name)
        index = get_choice_node(flang_node, node_location)

        return node, [flang_node.children[index]]
    elif flang_node.type == "text":

        if flang_node.get_bool_attrib("regex"):
            content = get_regex_content(flang_node, node_location)
        else:
            content = flang_node.get_attrib("value", flang_node.text)

        node = UserLeaf(
            flang_ast_path=flang_node.location, name=node_name, content=content
        )

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


def generate_node_with_cardinality(
    flang_node: FlangAST, parent: BaseUserAST, spec: SpecificationKeyValueStore
) -> list[BaseUserAST]:
    quantity = get_node_cardinality()
    list_of_nodes = []

    for idx in range(quantity):
        node, children = determine_node_and_children(
            flang_node, parent, parent.location, spec
        )
        # node.name = node_name

        if children is not None:
            children_nodes = []

            for child in children:
                children_nodes += generate_node_with_cardinality(child, node, spec)

            node.children = children_nodes

        list_of_nodes.append(node)

    return list_of_nodes


def generate_ast_from_specification(
    flang_ast: FlangAST, specification: SpecificationKeyValueStore
): ...


def _join_children(content: list) -> list[VirtualFileRepresentation] | str:
    is_directory = None

    for item in content:
        if isinstance(item, str):
            assert (
                is_directory != True
            ), "Ast cannot contain strings and files. Cannot create directory with text content!"
            is_directory = False
        elif isinstance(item, VirtualFileRepresentation):
            assert (
                is_directory != False
            ), "Ast cannot contain strings and files. Cannot create directory with text content!"
            is_directory = True

    if is_directory:
        return [file for sublist in content for file in sublist]
    return "".join(content)


def _inner_materialize_ast(user_ast: BaseUserAST) -> VirtualFileRepresentation | str:
    if isinstance(user_ast, UserLeaf):
        return user_ast.content
    elif isinstance(user_ast, UserBranch):
        materialized = [_inner_materialize_ast(child) for child in user_ast.children]
        content = _join_children(materialized)

        return (
            VirtualFileRepresentation(name=user_ast.filename, content=content)
            if user_ast.filename
            else content
        )

    raise RuntimeError


def materialize_ast(user_ast: BaseUserAST, file_target: str | None = None):
    assert isinstance(user_ast, UserBranch)

    if file_target:
        user_ast.filename = file_target

    return _inner_materialize_ast()


def get_cardinality_key(location: str) -> str:
    return f"_card:{location}"
