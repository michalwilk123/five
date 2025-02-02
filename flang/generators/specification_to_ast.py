from flang.core.utils import (
    get_available_children,
    is_flang_node_hidden,
    resolve_use_node,
)
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
    CHOICE_INDEX_KEY,
    FILENAME_KEY,
    TEXT_CONTENT_KEY,
    MissingSpecificationValueEvent,
    generate_random_value_for_key,
    is_constant_cardinality,
    raise_exception_value_for_key,
)


def get_cardinality(
    template: TemplateTree,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
    node: FlangBranch,
    node_name: str,
):
    key = CHILDREN_KEY.format(node.location)

    if is_constant_cardinality(template):  # NOTE: Czy na pewno powinnismy to sprawdzac?
        assert node_name not in specification.get(
            key, {}
        ), f"Node with constant cardinality had it set manually. This {specification.get(key, {})} should not be set in specification {template}"
        return 1

    cardinality_dict = specification.get(key, {})

    if node_name in cardinality_dict:
        return cardinality_dict[node_name]

    return on_missing_value(template, key)


def get_content(
    template: TemplateTree,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
    name: str,
):
    key = None

    if template.type == "text":
        key = TEXT_CONTENT_KEY.format(name)
        if custom_content := specification.get(key):
            return custom_content
        elif not template.get_bool_attrib("regex"):
            return template.get_attrib("value", template.text)
        elif "default" in template.attributes:
            return template.attributes["default"]
    elif template.type == "file":
        key = FILENAME_KEY.format(name)
        if filename := specification.get(key):
            return filename
        elif not template.get_bool_attrib("regex"):
            return template.get_attrib("pattern")
        elif "default" in template.attributes:
            return template.attributes["default"]
    elif template.type == "choice":
        key = CHOICE_INDEX_KEY.format(name)
        if (chosen_index := specification.get(key)) is not None:
            return chosen_index
    elif template.type in ("sequence", ""):
        return

    if key is not None:
        return on_missing_value(template, key)

    raise ImpossibleOperationError(template.type)


def get_node_and_children(
    template: TemplateTree,
    specification: Specification,
    path_to_node: str,
    on_missing_value: MissingSpecificationValueEvent,
) -> tuple[FlangAST, list]:
    assert not isinstance(template, TemplateRoot)

    if template.type == "use":
        resolved_template = resolve_use_node(template)
        node, children = get_node_and_children(
            resolved_template, specification, path_to_node, on_missing_value
        )
        node.name = template.get_id()
        node.template_id = template.location
        return node, children

    children = None
    content = get_content(template, specification, on_missing_value, path_to_node)

    if template.type == "text":
        node = FlangLeaf(
            name=template.get_id(), template_id=template.location, content=content
        )
    elif template.type == "sequence":
        node = FlangBranch(name=template.get_id(), template_id=template.location)
        children = get_available_children(template)
    elif template.type == "file":
        node = FlangBranch(
            name=template.get_id(), template_id=template.location, filename=content
        )
        children = get_available_children(template)
    elif template.type == "choice":
        # NOTE: trzeba sie upewnic ze wpisywany indeks tez nie bieze pod uwage czy komponent jest ukryty
        node = FlangBranch(name=template.get_id(), template_id=template.location)
        assert not is_flang_node_hidden(child_node := template.children[content])
        children = [child_node]

        if children[0].get_bool_attrib("terminal"):
            node.is_terminal = None
    else:
        raise Exception

    return node, children


def create_ast(
    template: TemplateTree,
    specification: Specification,
    parent: FlangBranch | None,
    on_missing_value: MissingSpecificationValueEvent,
) -> FlangAST:
    if parent is None:
        node = FlangRoot()
        children = [template]
    else:
        index = parent.get_next_node_index(
            template.get_id()
        )  # node name only for specification
        node_name = FlangAST.pack(index, template.get_id())
        full_path = parent.join_paths(parent.location, node_name)

        node, children = get_node_and_children(
            template,
            specification,
            full_path,
            on_missing_value,
        )
        parent.add_node(node)
        assert full_path == node.location, (full_path, node.location)

    if not children:
        return node

    for child in children:
        cardinality = get_cardinality(
            child,
            specification,
            on_missing_value,
            node,
            child.get_id(),
        )

        for _ in range(cardinality):
            child_node = create_ast(
                child,
                specification,
                node,
                on_missing_value,
            )

            if hasattr(child_node, "is_terminal"):
                break

    return node


def _create_ast_root(
    template: TemplateTree,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
):
    return create_ast(
        template,
        specification,
        None,
        on_missing_value,
    )


def create_ast_with_patched_values(
    template: TemplateTree,
    specification: Specification,
) -> FlangRoot:
    return _create_ast_root(template, specification, generate_random_value_for_key)


def create_ast_strict(
    template: TemplateTree,
    specification: Specification,
) -> FlangRoot:
    return _create_ast_root(template, specification, raise_exception_value_for_key)
