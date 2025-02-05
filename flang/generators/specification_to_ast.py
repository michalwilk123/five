from typing import Callable

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

AstBuilderCallback = Callable[[FlangAST, list[TemplateTree]], None]


def get_child_node_path(node: FlangAST, child_template: TemplateTree) -> str:
    child_template_id = child_template.get_id()
    index = node.get_next_node_index(child_template_id)  # node name only for specification
    child_node_name = FlangAST.pack(index, child_template_id)
    return node.join_paths(node.location, child_node_name)


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
) -> tuple[FlangAST, list[TemplateTree]]:
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
        assert not is_flang_node_hidden(
            child_node := template.children[content]
        )
        children = [child_node]

        if children[0].get_bool_attrib("terminal"):
            node.is_terminal = None
    else:
        raise Exception

    return node, children


def create_ast_for_children(
    node: FlangAST,
    children: list[TemplateTree],
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
    ast_builder_callback: AstBuilderCallback,
):
    for child in children:
        cardinality = get_cardinality(
            child,
            specification,
            on_missing_value,
            node,
            child.get_id(),
        )

        for _ in range(cardinality):
            child_node_path = get_child_node_path(node, child)
            node, children = get_node_and_children(
                child,
                specification,
                child_node_path,
                on_missing_value,
            )
            node.add_node(child_node)

            child_node = ast_builder_callback(
                child,
                child_node_path,
            )
            # print(f"{ child_node_path=}")
            # try:
            # except Exception as e:
            #     pass
            #     raise e

            assert child_node_path == child_node.location, (
                child_node_path,
                child_node.location,
            )

            if hasattr(child_node, "is_terminal"):
                break

    return node

def get_node(template: TemplateTree, specification:Specification, node_path: str, on_missing_value: MissingSpecificationValueEvent):
    assert not isinstance(template, TemplateRoot)

    if template.type == "use":
        resolved_template = resolve_use_node(template)
        node = get_node(resolved_template, specification, node_path, on_missing_value)
        node.name = template.get_id()
        node.template_id = template.location
        return node

    content = get_content(template, specification, on_missing_value, node_path)

    if template.type == "text":
        node = FlangLeaf(
            name=template.get_id(), template_id=template.location, content=content
        )
    elif template.type in ["sequence", "choice"]:
        node = FlangBranch(name=template.get_id(), template_id=template.location)
    elif template.type == "file":
        node = FlangBranch(
            name=template.get_id(), template_id=template.location, filename=content
        )
    else:
        raise Exception

    return node

def get_children_templates(template: TemplateTree, specification:Specification, node_path: str, on_missing_value: MissingSpecificationValueEvent):
    if template.type == "use":
        resolved_template = resolve_use_node(template)
        children = get_children_templates(
            resolved_template, specification, node_path, on_missing_value
        )
        return children
    elif template.type == "choice":
        content = get_content(template, specification, on_missing_value, node_path)
        assert not is_flang_node_hidden(
            child_node := template.children[content]
        )
        if child_node.get_bool_attrib("terminal"):
            child_node.is_terminal = None

        return [child_node]
    
    return get_available_children(template) if template.children else None

def create_children_for_ast(
    template: TemplateTree,
    node: FlangAST,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
) -> FlangAST:
    # node, children = get_node_and_children(
    #     template,
    #     specification,
    #     path,
    #     on_missing_value,
    # )
    
    # if template.type == "use":
    #     target_template = resolve_use_node(template)
    #     return create_ast(target_template, specification, on_missing_value)
    # elif isinstance(template, TemplateRoot):
    #     node = FlangRoot()
    # else:
    #     node = get_node(
    #         child_template,
    #         specification,
    #         on_missing_value,
    #     )

    # children_templates = get_children_templates(node.location)

    if template.type == "use":
        tempe = resolve_use_node(template)
        

    if tempe.children:
        children = []

        get_cardinality(tempe, specification, on_missing_value)

        for child_template in tempe.children:

            for _ in range(get_cardinality(child_template, specification, on_missing_value, node, node.location)):
                child_node = get_node(
                    child_template,
                    specification,
                    on_missing_value,
                )
                children.append(child_node)
                # node.add_node(child_node)
    
    return node


    for child_template in children_templates:
        child_node_path = get_child_node_path(node, child_template)
        child_node = get_node(
            child_template,
            specification,
            on_missing_value,
        )
        node.add_node(child_node)
        assert child_node_path == child_node.location, (
            child_node_path,
            child_node.location,
        )
    
    for child_node in node.children:
        create_ast(child_node, specification, on_missing_value)
    
    return node


    # create_ast_for_children(
    #     node,
    #     children_templates,
    #     specification,
    #     on_missing_value,
    #     lambda child, child_path: create_ast(
    #         child, specification, child_path, on_missing_value
    #     ),
    # )

    # return node


def create_root_ast(
    template: TemplateTree,
    specification: Specification,
    on_missing_value: MissingSpecificationValueEvent,
) -> FlangAST:
    return create_ast_for_children(
        FlangRoot(),
        [template],
        specification,
        on_missing_value,
        lambda child, child_path: create_ast(
            child, specification, child_path, on_missing_value
        ),
    )


# def create_ast(
#     template: TemplateTree,
#     specification: Specification,
#     parent: FlangBranch | None,
#     on_missing_value: MissingSpecificationValueEvent,
# ) -> FlangAST:
#     if parent is None:
#         node = FlangRoot()
#         children = [template]
#     else:
#         index = parent.get_next_node_index(
#             template.get_id()
#         )  # node name only for specification
#         node_name = FlangAST.pack(index, template.get_id())
#         full_path = parent.join_paths(parent.location, node_name)

#         node, children = get_node_and_children(
#             template,
#             specification,
#             full_path,
#             on_missing_value,
#         )
#         parent.add_node(node)
#         assert full_path == node.location, (full_path, node.location)

#     if not children:
#         return node

#     for child in children:
#         cardinality = get_cardinality(
#             child,
#             specification,
#             on_missing_value,
#             node,
#             child.get_id(),
#         )

#         for _ in range(cardinality):
#             child_node = create_ast(
#                 child,
#                 specification,
#                 node,
#                 on_missing_value,
#             )

#             if hasattr(child_node, "is_terminal"):
#                 break

#     return node


# def _create_ast_root(
#     template: TemplateTree,
#     specification: Specification,
#     on_missing_value: MissingSpecificationValueEvent,
# ):
#     return create_ast(
#         template,
#         specification,
#         None,
#         on_missing_value,
#     )


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
