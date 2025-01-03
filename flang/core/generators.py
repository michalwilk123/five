import random
from collections import Counter

from flang.structures import (
    BaseUserAST,
    FlangAST,
    FlangASTRoot,
    UserBranch,
    UserLeaf,
    UserRoot,
)
from flang.utils.regex import lex_storage

from .utils import get_available_children, resolve_use_node, is_flang_node_hidden

TEXT_CONTENT_KEY = "{}:content"
CHOICE_INDEX_KEY = "{}:choice-index"
CHILDREN_KEY = "{}:children"
FILENAME_KEY = "{}:filename"


def has_deterministic_cardinality(flang_node: FlangAST) -> bool:
    return flang_node.get_bool_attrib("hidden") or not (
        "multi" in flang_node.attributes or "optional" in flang_node.attributes
    )


def generate_specification_for_cardinality(
    flang_node: FlangAST, branch: UserBranch
) -> dict:
    ctr = Counter([flang_node.full_search(item.flang_ast_path).name for item in branch.children])
    children_card_dict = {}

    for child in get_available_children(flang_node):
        original_node = child

        if child.type == "use":
            child = resolve_use_node(child)

        if has_deterministic_cardinality(child):
            continue

        children_card_dict[original_node.name] = ctr.get(original_node.name, 0)

    return (
        {CHILDREN_KEY.format(branch.location): children_card_dict}
        if children_card_dict
        else {}
    )


def generate_specification_for_branch(flang_node: FlangAST, branch: UserBranch) -> dict:
    specs = generate_specification_for_cardinality(flang_node, branch)

    if flang_node.type == "choice":
        specs[CHOICE_INDEX_KEY.format(branch.location)] = [
            item.location for item in get_available_children(flang_node)
        ].index(branch.children[0].flang_ast_path)
    elif flang_node.type == "file":
        specs[FILENAME_KEY.format(branch.location)] = branch.filename

    return specs


def generate_specification_for_leaf(flang_node: FlangAST, leaf: UserLeaf) -> dict:
    not_deterministic = flang_node.get_bool_attrib(
        "regex"
    ) and leaf.content != flang_node.get_attrib("default")

    return (
        {TEXT_CONTENT_KEY.format(leaf.location): leaf.content}
        if not_deterministic
        else {}
    )


def generate_specification(flang_ast: FlangAST, user_ast: BaseUserAST) -> dict:
    if isinstance(user_ast, UserRoot):
        fake_root = FlangASTRoot()
        fake_root.add_node(flang_ast)
        flang_node = fake_root
    else:
        flang_node = flang_ast.full_search(user_ast.flang_ast_path)
    
    if flang_node.type == "use":
        flang_node = resolve_use_node(flang_node)

    specification = {}

    if isinstance(user_ast, UserLeaf):
        specification |= generate_specification_for_leaf(flang_node, user_ast)
    elif isinstance(user_ast, UserBranch):
        specification |= generate_specification_for_branch(flang_node, user_ast)

        for child in user_ast.children:
            specification |= generate_specification(flang_ast, child)
    else:
        raise Exception

    return specification


class MissingSpecificationError(Exception):
    pass


def get_cardinality(
    flang_node: FlangAST, specification: dict, fill_missing: bool, node: UserBranch, node_name:str
):
    if has_deterministic_cardinality(flang_node):
        return 1

    cardinality_dict = specification.get(CHILDREN_KEY.format(node.location), {})

    if node_name in cardinality_dict:
        return cardinality_dict[node_name]

    if not fill_missing:
        from pprint import pprint
        pprint(specification)
        raise MissingSpecificationError(CHILDREN_KEY.format(node.location), node_name)

    number_choice = [1]

    if flang_node.get_bool_attrib("multi"):
        # Adding muliple values makes it so the result tree explodes in branches
        # number_choice += [2,3]
        pass

    if flang_node.get_bool_attrib("optional"):
        number_choice += [0]

    return random.choice(number_choice)


def get_content(
    flang_node: FlangAST, specification: dict, fill_missing: bool, variant: str, name: str
):
    if variant == "text":
        if custom_content := specification.get(TEXT_CONTENT_KEY.format(name)):
            return custom_content
        elif not flang_node.get_bool_attrib("regex"):
            return flang_node.get_attrib("value", flang_node.text)
        elif "default" in flang_node.attributes:
            return flang_node.attributes["default"]
    elif variant == "file":
        if filename := specification.get(FILENAME_KEY.format(name)):
            return filename
        elif not flang_node.get_bool_attrib("regex"):
            return flang_node.get_attrib("pattern")
        elif "default" in flang_node.attributes:
            return flang_node.attributes["default"]
    elif variant == "choice":
        if (chosen_index := specification.get(CHOICE_INDEX_KEY.format(name))) is not None:
            return chosen_index
    elif variant in ("sequence", ""):
        return
    else:
        raise Exception(variant)

    if not fill_missing:
        from pprint import pprint
        pprint(specification)
        raise MissingSpecificationError(variant, name)

    if variant == "text":
        return lex_storage.generate_example(
            flang_node.get_attrib("value", flang_node.text)
        )
    elif variant == "file":
        return lex_storage.generate_example(flang_node.get_attrib("pattern"))
    elif variant == "choice":
        return random.randrange(len(flang_node.children))


def get_node_and_children(
    flang_node: FlangAST, specification: dict, name: str, fill_missing: bool
) -> tuple[BaseUserAST, list]:
    assert not isinstance(flang_node, FlangASTRoot)

    children = None
    content = get_content(flang_node, specification, fill_missing, flang_node.type, name)

    if flang_node.type == "text":
        node = UserLeaf(
            name=flang_node.name, flang_ast_path=flang_node.location, content=content
        )
    elif flang_node.type == "sequence":
        node = UserBranch(name=flang_node.name, flang_ast_path=flang_node.location)
        children = get_available_children(flang_node)
    elif flang_node.type == "file":
        node = UserBranch(
            name=flang_node.name, flang_ast_path=flang_node.location, filename=content
        )
        children = get_available_children(flang_node)
    elif flang_node.type == "choice":
        # NOTE: trzeba sie upewnic ze wpisywany indeks tez nie bieze pod uwage czy komponent jest ukryty
        node = UserBranch(name=flang_node.name, flang_ast_path=flang_node.location)
        assert not is_flang_node_hidden(child_node := flang_node.children[content])
        children = [child_node]

        if children[0].get_bool_attrib("terminal"):
            node.is_terminal = None
    else:
        raise Exception

    return node, children


def construct_ast(
    flang_node: FlangAST,
    specification: dict,
    parent: UserBranch | None,
    fill_missing: bool,
    flang_node_location: str
) -> BaseUserAST:
    if parent is None:
        node = UserRoot()
        children = [flang_node]
    else:
        name = parent.get_next_node_name(
            flang_node.name
        )  # node name only for specification
        node, children = get_node_and_children(
            flang_node,
            specification,
            parent.join_paths(parent.location, name),
            fill_missing,
        )
        node.flang_ast_path = flang_node_location
        parent.add_node(node)
        assert name.startswith(node.name)

    if not children:
        return node

    for child in children:
        original_node = child

        if child.type == "use":
            child = resolve_use_node(child)

        cardinality = get_cardinality(child, specification, fill_missing, node, original_node.name)

        for _ in range(cardinality):
            child_node = construct_ast(child, specification, node, fill_missing, flang_node_location=original_node.location)

            if hasattr(child_node, "is_terminal"):
                break

    return node


def get_constructed_ast(
    flang_node: FlangAST, specification: dict, fill_missing: bool
) -> UserRoot:
    return construct_ast(flang_node, specification, None, fill_missing=fill_missing, flang_node_location=flang_node.location)
