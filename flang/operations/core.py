"""
Do not use the operations from this file if you don't have to
"""

import re
from typing import NamedTuple

from flang.generators.common import CHILDREN_KEY
from flang.structures import (
    FlangAST,
    FlangBranch,
    Operation,
    OperationLog,
    Specification,
    TemplateTree,
)

__all__ = ["CORE_OPS", "OperationState", "reverse_operation", "execute"]


class OperationState(NamedTuple):
    log: OperationLog
    template_tree: TemplateTree
    specification: Specification


def filter_to_relevant_specification(
    specification: Specification, template_id: str
) -> dict:
    mapping = {}

    for key, value in specification.items():
        if key.startswith(template_id):
            mapping[key] = value

    return mapping


def split_location_path(location: str):
    node_name = location.split(FlangAST.PATH_SEPARATOR)[-1]
    parent = location.removesuffix(FlangAST.PATH_SEPARATOR + node_name)
    index, template_name = FlangAST.unpack(node_name)

    return parent, template_name, index


def _select(specification, location):
    """
    returns the list of specification of flang_tree at given location query. Location can be fuzzy.
    """
    matched = []

    for key in specification:
        if re.match(location, key):
            matched.append(key)

    return matched


def _insert(
    template_tree, specification, target_location
):  # NOTE: do not remove template_tree
    """
    target -> str

    parent, object, target_index = split_insert_path(target)
    counts = specification.get(CARDINALITY_KEY.format(parent))

    if not counts:
        raise Exception("nie mozna znalezc lalala")

    counts[object] += 1

    pattern = parent + object
    new_spec = spec.copy()
    new_object_name = FlangNode.pack(object, target_index)
    k_val_pairs = defaultdict(list)

    for k, v in spec.items():
        if k.startswith(pattern):
            _, idx = FlangNode.unpack(k.split(":")[0])
            k_val_pairs[idx].append((k.split(":")[1], val))

            if idx >= target_index:
                idx += 1

            new_name = FlangNode.pack(idx, object)

            new_spec[new_name] = new_spec.pop(k)

    return new_spec
    """
    # TODO: SHOULD VALIDATE IF COMPONENT HAS MULTI
    parent, template_name, target_index = split_location_path(target_location)
    counts = specification.get(CHILDREN_KEY.format(parent))

    if not counts or template_name not in counts:
        raise Exception("cannot add child with constant number of items")

    counts[template_name] += 1
    template_id = TemplateTree.join_paths(parent, template_name)

    for key in filter_to_relevant_specification(specification, template_id):
        if index >= target_index:
            location, key_type = key.split(":")
            index, template_name = FlangAST.unpack(location)
            new_key = ":".join(FlangAST.pack(index + 1, template_name), key_type)
            specification[new_key] = specification.pop(key)

    return specification


def _update(template_tree, flang_tree, location):
    # dsad
    ...


def _delete(template_tree, specification, target_location):
    parent, node_name, target_index = split_location_path(target_location)
    counts = specification.get(CHILDREN_KEY.format(parent))

    if not counts or node_name not in counts:
        raise Exception("cannot add child with constant number of items")

    # TODO: SHOULD VALIDATE IF COMPONENT HAS OPTIONAL OR AMOUT IS ALREADY ZERO

    counts[node_name] -= 1
    template_id = TemplateTree.join_paths(parent, node_name)

    for key in filter_to_relevant_specification(specification, template_id):
        if index > target_index:
            location, key_type = key.split(":")
            index, node_name = FlangAST.unpack(location)
            new_key = ":".join(FlangAST.pack(index + 1, node_name), key_type)
            specification[new_key] = specification.pop(key)
        elif index == target_index:
            specification.pop(key)

    return specification


def _commit(template_tree, flang_tree, location): ...


def _checkpoint(): ...


def reverse_operation(operation: Operation): ...


CORE_OPS = {
    "select": _select,
    "insert": _insert,
    "delete": _delete,
    "update": _update,
    "commit": _commit,
    "checkpoint": _checkpoint,
}


def execute(operation: Operation, state: OperationState, remember: bool):
    state.log.append(operation)
    return operation.execute(CORE_OPS[operation.signature], state)
