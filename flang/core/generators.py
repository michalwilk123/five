import random
from collections import Counter

from flang.structures import (
    FlangAST,
    FlangBranch,
    FlangLeaf,
    FlangRoot,
    TemplateRoot,
    TemplateTree,
)
from flang.utils.regex import lex_storage

from .utils import get_available_children, is_flang_node_hidden, resolve_use_node

TEXT_CONTENT_KEY = "{}:content"
CHOICE_INDEX_KEY = "{}:choice-index"
CHILDREN_KEY = "{}:children"
FILENAME_KEY = "{}:filename"


def has_deterministic_cardinality(template: TemplateTree) -> bool:
    return template.get_bool_attrib("hidden") or not (
        "multi" in template.attributes or "optional" in template.attributes
    )


def generate_specification_for_cardinality(
    template: TemplateTree, branch: FlangBranch
) -> dict:
    ctr = Counter(
        [template.full_search(item.template_id).name for item in branch.children]
    )
    children_card_dict = {}

    for child in get_available_children(template):
        original_node = child

        if child.type == "use":
            child = resolve_use_node(child)

        if has_deterministic_cardinality(child):
            continue

        children_card_dict[original_node.name] = ctr.get(original_node.name, 0)

    return (
        {CHILDREN_KEY.format(branch.location): children_card_dict}
        if children_card_dict
        else {}
    )


def generate_specification_for_branch(
    template: TemplateTree, branch: FlangBranch
) -> dict:
    specs = generate_specification_for_cardinality(template, branch)

    if template.type == "choice":
        specs[CHOICE_INDEX_KEY.format(branch.location)] = [
            item.location for item in get_available_children(template)
        ].index(branch.children[0].template_id)
    elif template.type == "file":
        specs[FILENAME_KEY.format(branch.location)] = branch.filename

    return specs


def generate_specification_for_leaf(template: TemplateTree, leaf: FlangLeaf) -> dict:
    not_deterministic = template.get_bool_attrib(
        "regex"
    ) and leaf.content != template.get_attrib("default")

    return (
        {TEXT_CONTENT_KEY.format(leaf.location): leaf.content}
        if not_deterministic
        else {}
    )


def generate_specification(template_tree: TemplateTree, flang_tree: FlangAST) -> dict:
    if isinstance(flang_tree, FlangRoot):
        fake_root = TemplateRoot()
        fake_root.add_node(template_tree)
        template = fake_root
    else:
        template = template_tree.full_search(flang_tree.template_id)

    if template.type == "use":
        template = resolve_use_node(template)

    specification = {}

    if isinstance(flang_tree, FlangLeaf):
        specification |= generate_specification_for_leaf(template, flang_tree)
    elif isinstance(flang_tree, FlangBranch):
        specification |= generate_specification_for_branch(template, flang_tree)

        for child in flang_tree.children:
            specification |= generate_specification(template_tree, child)
    else:
        raise Exception

    return specification


class MissingSpecificationError(Exception):
    pass


def get_cardinality(
    template: TemplateTree,
    specification: dict,
    fill_missing: bool,
    node: FlangBranch,
    node_name: str,
):
    if has_deterministic_cardinality(template):
        return 1

    cardinality_dict = specification.get(CHILDREN_KEY.format(node.location), {})

    if node_name in cardinality_dict:
        return cardinality_dict[node_name]

    if not fill_missing:
        from pprint import pprint

        pprint(specification)
        raise MissingSpecificationError(CHILDREN_KEY.format(node.location), node_name)

    number_choice = [1]

    if template.get_bool_attrib("multi"):
        # Adding muliple values makes it so the result tree explodes in branches
        # number_choice += [2,3]
        pass

    if template.get_bool_attrib("optional"):
        number_choice += [0]

    return random.choice(number_choice)


def get_content(
    template: TemplateTree,
    specification: dict,
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
        from pprint import pprint

        pprint(specification)
        raise MissingSpecificationError(variant, name)

    if variant == "text":
        return lex_storage.generate_example(template.get_attrib("value", template.text))
    elif variant == "file":
        return lex_storage.generate_example(template.get_attrib("pattern"))
    elif variant == "choice":
        return random.randrange(len(template.children))


def get_node_and_children(
    template: TemplateTree, specification: dict, name: str, fill_missing: bool
) -> tuple[FlangAST, list]:
    assert not isinstance(template, TemplateRoot)

    children = None
    content = get_content(template, specification, fill_missing, template.type, name)

    if template.type == "text":
        node = FlangLeaf(
            name=template.name, template_id=template.location, content=content
        )
    elif template.type == "sequence":
        node = FlangBranch(name=template.name, template_id=template.location)
        children = get_available_children(template)
    elif template.type == "file":
        node = FlangBranch(
            name=template.name, template_id=template.location, filename=content
        )
        children = get_available_children(template)
    elif template.type == "choice":
        # NOTE: trzeba sie upewnic ze wpisywany indeks tez nie bieze pod uwage czy komponent jest ukryty
        node = FlangBranch(name=template.name, template_id=template.location)
        assert not is_flang_node_hidden(child_node := template.children[content])
        children = [child_node]

        if children[0].get_bool_attrib("terminal"):
            node.is_terminal = None
    else:
        raise Exception

    return node, children


def construct_ast(
    template: TemplateTree,
    specification: dict,
    parent: FlangBranch | None,
    fill_missing: bool,
    flang_node_location: str,
) -> FlangAST:
    if parent is None:
        node = FlangRoot()
        children = [template]
    else:
        name = parent.get_next_node_name(
            template.name
        )  # node name only for specification
        node, children = get_node_and_children(
            template,
            specification,
            parent.join_paths(parent.location, name),
            fill_missing,
        )
        node.template_id = flang_node_location
        parent.add_node(node)
        assert name.startswith(node.name)

    if not children:
        return node

    for child in children:
        original_node = child

        if child.type == "use":
            child = resolve_use_node(child)

        cardinality = get_cardinality(
            child, specification, fill_missing, node, original_node.name
        )

        for _ in range(cardinality):
            child_node = construct_ast(
                child,
                specification,
                node,
                fill_missing,
                flang_node_location=original_node.location,
            )

            if hasattr(child_node, "is_terminal"):
                break

    return node


def get_constructed_ast(
    template: TemplateTree, specification: dict, fill_missing: bool
) -> FlangRoot:
    return construct_ast(
        template,
        specification,
        None,
        fill_missing=fill_missing,
        flang_node_location=template.location,
    )
