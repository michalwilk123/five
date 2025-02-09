from flang.core.utils import is_flang_node_hidden, resolve_use_node
from flang.structures import (
    FlangAST,
    FlangBranch,
    FlangLeaf,
    FlangRoot,
    Specification,
    TemplateRoot,
    TemplateTree,
)
from flang.utils.exceptions import ImpossibleOperationError

from .common import (
    CHILDREN_KEY,
    FILENAME_KEY,
    TEXT_CONTENT_KEY,
    MissingSpecificationValueEvent,
    generate_random_value_for_key,
    is_constant_cardinality,
    raise_exception_value_for_key,
)


def create_count_dictionary(
    template: TemplateRoot,
    specification: Specification,
    node_path: str,
    on_missing_value: MissingSpecificationValueEvent,
) -> dict[str, int]:
    assert isinstance(template.children, list)
    assert template.type != "use"

    children_key = CHILDREN_KEY.format(node_path)

    try:
        count_dictionary = specification[children_key]
    except KeyError:
        count_dictionary = on_missing_value(template, children_key)

    for child_template in template.children:
        if is_flang_node_hidden(child_template):
            count_dictionary[child_template.get_id()] = 0
        elif is_constant_cardinality(child_template):
            count_dictionary[child_template.get_id()] = 1

    return count_dictionary


def create_ast_node(
    template: TemplateTree,
    specification: Specification,
    node_path: str,
    on_missing_value: MissingSpecificationValueEvent,
) -> FlangAST:
    assert not isinstance(template, TemplateRoot)

    if template.type == "use":
        resolved_template = resolve_use_node(template)
        node = create_ast_node(
            resolved_template, specification, node_path, on_missing_value
        )
        node.name = template.get_id()
        node.template_id = template.location
        return node

    if template.type == "text":
        key = TEXT_CONTENT_KEY.format(node_path)

        if specification.get(key):
            content = specification.get(key)
        elif not template.get_bool_attrib("regex"):
            content = template.get_attrib("value", template.text)
        elif "default" in template.attributes:
            content = template.attributes["default"]
        else:
            content = on_missing_value(template, key)

        node = FlangLeaf(
            name=template.get_id(), template_id=template.location, content=content
        )
    elif template.type in ["sequence", "choice"]:
        node = FlangBranch(name=template.get_id(), template_id=template.location)
    elif template.type == "file":
        key = FILENAME_KEY.format(node_path)

        if specification.get(key):
            filename = specification.get(key)
        elif not template.get_bool_attrib("regex"):
            filename = template.get_attrib("pattern")
        elif "default" in template.attributes:
            filename = template.attributes["default"]
        else:
            on_missing_value(template, key)

        node = FlangBranch(
            name=template.get_id(), template_id=template.location, filename=filename
        )
    else:
        raise ImpossibleOperationError

    return node


def create_children(
    template: TemplateTree,
    parent_path: str,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
) -> list[FlangAST]:
    if template.type == "use":
        resolved_template = resolve_use_node(template)
    else:
        resolved_template = template

    if resolved_template is None:
        raise ImpossibleOperationError

    if not resolved_template.children:
        return []

    children = []
    count_dictionary = create_count_dictionary(
        resolved_template, specification, parent_path, on_missing_value
    )

    for child_template in resolved_template.children:
        count = count_dictionary[child_template.get_id()]

        for index in range(count):
            node_name = FlangAST.pack(index, child_template.get_id())
            node_path = FlangAST.join_paths(parent_path, node_name)

            children.append(
                create_ast_node(
                    child_template, specification, node_path, on_missing_value
                )
            )

    return children


def expand_ast(
    template: TemplateTree,
    node: FlangAST,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
) -> None:
    children = create_children(
        template.full_search(node.template_id),
        node.location,
        specification,
        on_missing_value,
    )

    for child in children:
        node.add_node(child)
        expand_ast(template, child, specification, on_missing_value)


def create_root_ast(
    template: TemplateTree,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
) -> FlangAST:
    root = FlangRoot()
    template_root = TemplateRoot()
    template_root.add_node(template)
    expand_ast(template_root, root, specification, on_missing_value)
    return root


def create_ast_with_patched_values(
    template: TemplateTree,
    specification: Specification,
) -> FlangRoot:
    return create_root_ast(template, specification, generate_random_value_for_key)


def create_ast_strict(
    template: TemplateTree,
    specification: Specification,
) -> FlangRoot:
    return create_root_ast(template, specification, raise_exception_value_for_key)
