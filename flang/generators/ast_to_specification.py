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
    FILENAME_KEY,
    TEXT_CONTENT_KEY,
    is_constant_cardinality,
)


def create_specification_for_branch(
    template: TemplateTree, branch: FlangBranch
) -> Specification:
    ctr = Counter([item.name for item in branch.children])
    children_card_dict = {}

    for child in get_available_children(template):
        if is_constant_cardinality(child):
            assert (
                ctr.get(child.get_id(), 0) <= 1
            ), f"Node has constant cardinality but shows up wrong amount of times: {ctr.get(child.get_id(), 0), child}"
            continue

        children_card_dict[child.get_id()] = ctr.get(child.get_id(), 0)

    specs = {CHILDREN_KEY.format(branch.location): children_card_dict}

    if template.type == "file":
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
