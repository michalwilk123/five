"""
Do not use the operations from this file if you don't have to
"""

import re
from typing import NamedTuple

from flang.generators.common import CHILDREN_KEY
from flang.structures import (
    FlangAST,
    Operation,
    OperationLog,
    Specification,
    TemplateTree,
)

# __all__ = ["CORE_OPS", "OperationState", "reverse_operation", "execute"]


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


def _select(template_tree: TemplateTree, specification: Specification, location):
    """
    returns the list of specification of flang_tree at given location query. Location can be fuzzy.
    """
    matched = {}

    # from pprint import pprint
    # pprint(specification)

    for key, value in specification.items():
        if re.match(location, key):
            node_name, _ = key.split(":")

            if node_name not in matched:
                matched[node_name] = {}

            matched[node_name][key] = value

    return matched


def _insert(
    template_tree: TemplateTree, specification: Specification, target: str
) -> Specification:
    # NOTE: do not remove template_tree
    # TODO: SHOULD VALIDATE IF COMPONENT HAS MULTI
    parent, template_name, target_index = split_location_path(target)
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


def _update(
    template_tree: TemplateTree,
    specification: Specification,
    target: str,
    constants: dict | None = None,
    transfers: dict | None = None,
):
    assert constants is not None or transfers is not None

    for key, value in constants.items():
        target = FlangAST.join_paths(target, key)
        # TODO: jakas walidacja moze tutaj?
        specification[target] = value

    for key, value_from in transfers.items():
        target = FlangAST.join_paths(target, key)

        try:
            value = specification[value_from]
        except KeyError as e:
            raise Exception(
                f"Cannot take value from {value_from} because there is no avaliable data"
            ) from e

        # TODO: jakas walidacja moze tutaj?
        specification[target] = value

    return specification


def _delete(
    template_tree: TemplateTree, specification: Specification, target: str
) -> Specification:
    parent, node_name, target_index = split_location_path(target)
    counts = specification.get(CHILDREN_KEY.format(parent))

    if not counts or node_name not in counts:
        raise Exception("cannot add child with constant number of items")

    # TODO: SHOULD VALIDATE IF COMPONENT HAS OPTIONAL OR AMOUT IS ALREADY ZERO

    counts[node_name] -= 1
    assert counts[node_name] >= 0

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


# def reverse_operation(operation: Operation): ...


CORE_OPS = {
    "select": _select,
    "insert": _insert,
    "delete": _delete,
    "update": _update,
    "commit": _commit,
    "checkpoint": _checkpoint,
}


def execute(operation: Operation, state: OperationState):
    return CORE_OPS[operation.signature](
        state.template_tree, state.specification, **operation.arguments
    )
