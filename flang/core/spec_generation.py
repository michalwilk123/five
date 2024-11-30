from typing import Any

from flang.structures import BaseUserAST, FlangAST, UserBranch, UserLeaf, UserRoot

from .utils import get_cardinality_key


def generate_single_specification(
    flang_node: FlangAST, user_ast: BaseUserAST
) -> dict[str, Any]:
    if flang_node.type == "sequence":
        assert isinstance(user_ast, UserBranch)
        return _generate_specification_from_list(flang_node.children, user_ast.children)
    elif flang_node.type == "choice":
        assert isinstance(user_ast, UserBranch)
        available_choices = [f.location for f in flang_node.children]
        try:
            child_idx = available_choices.index(user_ast.children[0].flang_ast_path)
        except ValueError as e:
            print(available_choices)
            print(user_ast.children[0].flang_ast_path)
            raise e
        return {user_ast.location: child_idx} | _generate_specification_from_list(
            [flang_node.children[child_idx]], user_ast.children
        )
    elif flang_node.type == "text" and flang_node.get_bool_attrib("regex"):
        assert isinstance(user_ast, UserLeaf)
        return {user_ast.location: user_ast.content}
    elif flang_node.type == "file":
        assert isinstance(user_ast, UserBranch) and user_ast.filename is not None
        return {user_ast.location: user_ast.filename}

    return {}


def _generate_specification_from_list(
    flang_ast_content: list[FlangAST], user_ast_content: list[BaseUserAST]
) -> dict[str, Any]:
    if user_ast_content == []:
        return {}

    specification = {}
    idx = 0

    for flang_ast in flang_ast_content:
        cardinality = 0
        previous_node = user_ast_content[idx].flang_ast_path

        while idx < len(user_ast_content):
            node = user_ast_content[idx]

            if previous_node != node.flang_ast_path:
                break

            specification |= generate_single_specification(flang_ast.full_search(node.flang_ast_path), node)
            cardinality += 1
            idx += 1

        # this is a sanity check if cardinality checking worked in parsing step
        if flang_ast.get_bool_attrib("multi") or flang_ast.get_bool_attrib("optional"):
            specification[get_cardinality_key(flang_ast.location)] = cardinality
        elif cardinality > 1:
            raise RuntimeError

    return specification


def _generate_specification_from_root(
    flang_ast: FlangAST, root: UserRoot
) -> dict[str, Any]:
    root_content = root.children
    return generate_specification(flang_ast, root_content)


def generate_specification(
    flang_ast: FlangAST, user_ast_content: list[BaseUserAST] | UserRoot
) -> dict[str, Any]:
    if isinstance(user_ast_content, list):
        return _generate_specification_from_list([flang_ast], user_ast_content)
    return _generate_specification_from_root(flang_ast, user_ast_content)
