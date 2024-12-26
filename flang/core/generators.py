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

from .utils import get_resolved_children, is_flang_node_hidden, resolve_use_node

TEXT_CONTENT_KEY = "{}:content"
CHOICE_INDEX_KEY = "{}:choice-index"
CHILDREN_KEY = "{}:children"
FILENAME_KEY = "{}:filename"


def has_deterministic_cardinality(flang_node: FlangAST) -> bool:
    return (
        "multi" not in flang_node.attributes and "optional" not in flang_node.attributes
    )


def generate_specification_for_cardinality(
    flang_node: FlangAST, branch: UserBranch
) -> dict:
    node_names = [
        flang_node.full_search(item.flang_ast_path).name for item in branch.children
    ]
    ctr = Counter(node_names)
    children_card_dict = {}

    for child in get_resolved_children(flang_node):
        node_name = child.name

        if has_deterministic_cardinality(child):
            continue

        children_card_dict[node_name] = ctr.get(node_name, 0)

    return (
        {CHILDREN_KEY.format(branch.location): children_card_dict}
        if children_card_dict
        else {}
    )


def generate_specification_for_branch(flang_ast: FlangAST, branch: UserBranch) -> dict:
    flang_node = flang_ast.full_search(branch.flang_ast_path)
    specs = generate_specification_for_cardinality(flang_node, branch)

    if flang_node.type == "choice":
        specs[CHOICE_INDEX_KEY.format(branch.location)] = [
            item.location for item in get_resolved_children(flang_node)
        ].index(branch.children[0].flang_ast_path)
    elif flang_node.type == "file":
        specs[FILENAME_KEY.format(branch.location)] = branch.filename

    return specs


def generate_specification_for_leaf(flang_ast: FlangAST, leaf: UserLeaf) -> dict:
    flang_node = flang_ast.full_search(leaf.flang_ast_path)
    not_deterministic = flang_node.get_bool_attrib(
        "regex"
    ) and leaf.content != flang_node.get_attrib("default")

    return (
        {TEXT_CONTENT_KEY.format(leaf.location): leaf.content}
        if not_deterministic
        else {}
    )


def generate_specification(flang_ast: FlangAST, user_ast: BaseUserAST) -> dict:
    specification = {}

    if isinstance(user_ast, UserLeaf):
        specification |= generate_specification_for_leaf(flang_ast, user_ast)
    elif isinstance(user_ast, UserBranch):
        if isinstance(user_ast, UserRoot):
            fake_root = FlangASTRoot()
            fake_root.add_node(flang_ast)
            specification |= generate_specification_for_branch(fake_root, user_ast)
        else:
            specification |= generate_specification_for_branch(flang_ast, user_ast)

        for child in user_ast.children:
            specification |= generate_specification(flang_ast, child)
    else:
        raise Exception

    return specification


class MissingSpecificationError(Exception):
    pass


def get_cardinality(
    flang_node: FlangAST, specification: dict, fill_missing: bool, node: UserBranch
):
    if has_deterministic_cardinality(flang_node):
        return 1

    cardinality_dict = specification.get(CHILDREN_KEY.format(node.location), {})

    if flang_node.name in cardinality_dict:
        return cardinality_dict[flang_node.name]

    if not fill_missing:
        raise MissingSpecificationError

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
        raise Exception

    if not fill_missing:
        raise MissingSpecificationError

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
) -> tuple:
    assert not isinstance(flang_node, FlangASTRoot)

    children = None
    content = get_content(flang_node, specification, fill_missing, flang_node.type, name)

    if flang_node.name == "choice":
        pass

    if flang_node.type == "text":
        node = UserLeaf(
            name=flang_node.name, flang_ast_path=flang_node.location, content=content
        )
    elif flang_node.type == "sequence":
        node = UserBranch(name=flang_node.name, flang_ast_path=flang_node.location)
        children = get_resolved_children(flang_node)
    elif flang_node.type == "file":
        node = UserBranch(
            name=flang_node.name, flang_ast_path=flang_node.location, filename=content
        )
        children = get_resolved_children(flang_node)
    elif flang_node.type == "choice":
        node = UserBranch(name=flang_node.name, flang_ast_path=flang_node.location)
        # NOTE: trzeba sie upewnic ze wpisywany indeks tez nie bieze pod uwage czy komponent jest ukryty
        children = [flang_node.children[content]]

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
        parent.add_node(node)
        assert name.startswith(node.name)

    if not children:
        return node

    for child in children:
        if alias_name := child.get_attrib("alias"):
            child.create_alias(alias_name)

        if is_flang_node_hidden(child):
            continue

        if child.type == "use":
            child = resolve_use_node(child)

        cardinality = get_cardinality(child, specification, fill_missing, node)

        for _ in range(cardinality):
            child_node = construct_ast(child, specification, node, fill_missing)

            if hasattr(child_node, "is_terminal"):
                break

    return node


def get_constructed_ast(
    flang_node: FlangAST, specification: dict, fill_missing: bool
) -> UserRoot:
    return construct_ast(flang_node, specification, None, fill_missing=fill_missing)
