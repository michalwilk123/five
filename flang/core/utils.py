from flang.structures import BaseUserAST, FlangAST, UserBranch
from flang.utils.exceptions import SymbolNotFoundError


def resolve_use_node(flang_ast: FlangAST):
    target_location = flang_ast.get_attrib("ref")
    location = flang_ast.location

    target_location = flang_ast.normalize_path(target_location)
    target_flang_ast = flang_ast.resolve_path(target_location, location)

    if target_flang_ast is None:
        raise SymbolNotFoundError(
            f"Could not find symbol for path: {target_location}, location: {location}"
        )
    # TODO: if target_flang_ast.type is "module" then "hidden" attribute should stay

    attributes = {
        **target_flang_ast.attributes,
        **flang_ast.attributes,
        "hidden": False,
    }
    attributes.pop("ref")

    # TODO: can be cached very easily
    target_copy = target_flang_ast.replace(attributes=attributes)

    if target_flang_ast.children:
        for child in target_flang_ast.children:
            target_copy.add_node(child)

    return target_copy


def is_flang_node_hidden(flang_node: FlangAST) -> bool:
    return flang_node.get_bool_attrib("hidden") or flang_node.type in ["event"]


def get_available_children(flang_node: FlangAST):
    assert flang_node.children

    children = []

    for child in flang_node.children:
        if alias_name := child.get_attrib("alias"):
            child.create_alias(alias_name)

        if is_flang_node_hidden(child):
            continue

        children.append(child)

    return children


def create_branch_with_children(
    name: str, ast_path: str, children: list[BaseUserAST], filename: None | str
):
    user_branch = UserBranch(
        name=name,
        flang_ast_path=ast_path,
        filename=filename,
    )

    for child in children:
        assert isinstance(child, BaseUserAST)
        user_branch.add_node(child)

    return user_branch
