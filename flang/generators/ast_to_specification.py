from collections import Counter

from flang.core.utils import get_available_children, resolve_use_node
from flang.structures import (
    FlangAST,
    FlangBranch,
    FlangLeaf,
    FlangRoot,
    Specification,
    TemplateRoot,
    TemplateTree,
)

from .common import (
    CHILDREN_KEY,
    CHOICE_INDEX_KEY,
    FILENAME_KEY,
    TEXT_CONTENT_KEY,
    is_constant_cardinality,
)


def create_specification_for_cardinality(
    template: TemplateTree, branch: FlangBranch
) -> Specification:
    ctr = Counter([item.name for item in branch.children])
    children_card_dict = {}

    for child in get_available_children(template):
        original_node = child

        if child.type == "use":
            child = resolve_use_node(child)

        if is_constant_cardinality(original_node):
            assert (
                ctr.get(original_node.get_id(), 0) <= 1
            ), f"Node has constant cardinality but shows up wrong amount of times: {ctr.get(original_node.get_id(), 0), original_node}"
            continue

        children_card_dict[original_node.get_id()] = ctr.get(original_node.get_id(), 0)

    return (
        {CHILDREN_KEY.format(branch.location): children_card_dict}
        if children_card_dict
        else {}
    )


def create_specification_for_branch(
    template: TemplateTree, branch: FlangBranch
) -> Specification:
    specs = create_specification_for_cardinality(template, branch)

    if template.type == "choice":
        specs[CHOICE_INDEX_KEY.format(branch.location)] = [
            item.location for item in get_available_children(template)
        ].index(branch.children[0].template_id)
    elif template.type == "file":
        specs[FILENAME_KEY.format(branch.location)] = branch.filename

    return specs


def create_specification_for_leaf(
    template: TemplateTree, leaf: FlangLeaf
) -> Specification:
    not_deterministic = template.get_bool_attrib(
        "regex"
    ) and leaf.content != template.get_attrib("default")

    return (
        {TEXT_CONTENT_KEY.format(leaf.location): leaf.content}
        if not_deterministic
        else {}
    )


def create_specification(
    template_tree: TemplateTree, flang_ast: FlangAST
) -> Specification:
    if isinstance(flang_ast, FlangRoot):
        fake_root = TemplateRoot()
        fake_root.add_node(template_tree)
        template = fake_root
    else:
        template = template_tree.full_search(flang_ast.template_id)

    if template.type == "use":
        template = resolve_use_node(template)

    specification = {}

    if isinstance(flang_ast, FlangLeaf):
        specification |= create_specification_for_leaf(template, flang_ast)
    elif isinstance(flang_ast, FlangBranch):
        specification |= create_specification_for_branch(template, flang_ast)

        for child in flang_ast.children:
            specification |= create_specification(template_tree, child)
    else:
        raise Exception

    return specification
