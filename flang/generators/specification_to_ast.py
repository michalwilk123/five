import random

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
from flang.utils.regex import lex_storage

from .common import (
    CHILDREN_KEY,
    CHOICE_INDEX_KEY,
    FILENAME_KEY,
    TEXT_CONTENT_KEY,
    is_constant_cardinality,
)


class MissingSpecificationError(Exception):
    pass


def get_cardinality(
    template: TemplateTree,
    specification: Specification,
    fill_missing: bool,
    node: FlangBranch,
    node_name: str,
):
    if is_constant_cardinality(template):  # NOTE: Czy na pewno powinnismy to sprawdzac?
        assert node_name not in specification.get(
            CHILDREN_KEY.format(node.location), {}
        ), f"Node with constant cardinality had it set manually. This {specification.get(CHILDREN_KEY.format(node.location), {})} should not be set in specification {template}"
        return 1

    cardinality_dict = specification.get(CHILDREN_KEY.format(node.location), {})

    if node_name in cardinality_dict:
        return cardinality_dict[node_name]

    if not fill_missing:
        raise MissingSpecificationError(CHILDREN_KEY.format(node.location), node_name)

    number_choice = [1]

    if template.get_bool_attrib("multi"):
        # NOTE: Adding muliple values makes it so the result tree explodes in branches number_choice += [2,3]
        pass

    if template.get_bool_attrib("optional"):
        number_choice += [0]

    return random.choice(number_choice)


def get_content(
    template: TemplateTree,
    specification: Specification,
    fill_missing: bool,
    variant: str,
    name: str,
):
    if variant == "text":
        if custom_content := specification.get(TEXT_CONTENT_KEY.format(name)):
            return custom_content
        elif not template.get_bool_attrib("regex"):
            return template.get_attrib("value", template.text)
        elif "default" in template.attributes:
            return template.attributes["default"]
    elif variant == "file":
        if filename := specification.get(FILENAME_KEY.format(name)):
            return filename
        elif not template.get_bool_attrib("regex"):
            return template.get_attrib("pattern")
        elif "default" in template.attributes:
            return template.attributes["default"]
    elif variant == "choice":
        if (chosen_index := specification.get(CHOICE_INDEX_KEY.format(name))) is not None:
            return chosen_index
    elif variant in ("sequence", ""):
        return
    else:
        raise Exception(variant)

    if not fill_missing:
        # from pprint import pprint
        # pprint(specification)
        raise MissingSpecificationError(variant, name)

    if variant == "text":
        return lex_storage.generate_example(template.get_attrib("value", template.text))
    elif variant == "file":
        return lex_storage.generate_example(template.get_attrib("pattern"))
    elif variant == "choice":
        return random.randrange(len(template.children))


def get_node_and_children(
    template: TemplateTree,
    specification: Specification,
    path_to_node: str,
    fill_missing: bool,
) -> tuple[FlangAST, list]:
    assert not isinstance(template, TemplateRoot)

    if template.type == "use":
        resolved_template = resolve_use_node(template)
        node, children = get_node_and_children(
            resolved_template, specification, path_to_node, fill_missing
        )
        node.name = template.get_id()
        node.template_id = template.location
        return node, children

    children = None
    content = get_content(
        template, specification, fill_missing, template.type, path_to_node
    )

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


def construct_ast(
    template: TemplateTree,
    specification: Specification,
    parent: FlangBranch | None,
    fill_missing: bool,
    # flang_node_location: str,
    # node_name: str,
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
            parent.join_paths(parent.location, node_name),
            fill_missing,
        )
        # node.template_id = template.location
        parent.add_node(node)
        assert full_path == node.location, (full_path, node.location)

    if not children:
        return node

    for child in children:
        # original_node = child

        # if child.type == "use":
        #     child = resolve_use_node(child)

        cardinality = get_cardinality(
            child,
            specification,
            fill_missing,
            node,
            child.get_id(),
            # child, specification, fill_missing, node, original_template.get_id()
        )

        for _ in range(cardinality):
            child_node = construct_ast(
                child,
                specification,
                node,
                fill_missing,
                # flang_node_location=original_node.location,
                # node_name=original_node.get_id(),
            )

            if hasattr(child_node, "is_terminal"):
                break

    return node


def get_constructed_ast(
    template: TemplateTree, specification: Specification, fill_missing: bool
) -> FlangRoot:
    return construct_ast(
        template,
        specification,
        None,
        fill_missing=fill_missing,
        # flang_node_location=template.location,
    )
