from flang.utils.exceptions import SymbolNotFoundError


def resolve_use_node(flang_ast):
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

