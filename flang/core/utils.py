from flang.structures import FlangAST, FlangBranch, TemplateTree
from flang.utils.exceptions import SymbolNotFoundError


def resolve_use_node(template_tree: TemplateTree) -> TemplateTree:
    target_location = template_tree.get_attrib("ref")
    location = template_tree.location

    target_location = template_tree.normalize_path(target_location)
    target_template_tree = template_tree.resolve_path(target_location, location)

    if target_template_tree is None:
        raise SymbolNotFoundError(
            f"Could not find symbol for path: {target_location}, location: {location}"
        )
    # TODO: if target_template_tree.type is "module" then "hidden" attribute should stay

    attributes = {
        **target_template_tree.attributes,
        **template_tree.attributes,
        "hidden": False,
    }
    attributes.pop("ref")

    # TODO: can be cached very easily
    target_copy = target_template_tree.replace(attributes=attributes)

    if target_template_tree.children:
        for child in target_template_tree.children:
            target_copy.add_node(child)

    return target_copy


def is_flang_node_hidden(template: TemplateTree) -> bool:
    return template.get_bool_attrib("hidden") or template.type in ["event"]


def get_available_children(template: TemplateTree):
    assert template.children
    children = []

    for child in template.children:
        if is_flang_node_hidden(child):
            continue

        children.append(child)

    return children


def create_branch_with_children(
    name: str, ast_path: str, children: list[FlangAST], filename: None | str
):
    user_branch = FlangBranch(
        name=name,
        template_id=ast_path,
        filename=filename,
    )
    user_branch.children = []  # if no children

    for child in children:
        assert isinstance(child, FlangAST)
        user_branch.add_node(child)

    return user_branch


# Do i really need this?
# def full_search_with_refs() -> TemplateTree | FlangAST:
#     ...
