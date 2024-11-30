from flang.structures import (
    BaseUserAST,
    FlangAST,
    UserBranch,
    UserLeaf,
    UserRoot,
    VirtualFileRepresentation,
)
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
    return target_flang_ast.replace(attributes=attributes)


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
