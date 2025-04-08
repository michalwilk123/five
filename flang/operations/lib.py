from flang.structures import Operation, OperationLog

from .core import OperationState, execute


# def select(self, template_tree, specification, location) -> list[Operation]:
def select(state: OperationState, location):
    """
    returns the list of specification of specification at given location query. Location can be fuzzy.
    """
    operation = Operation("select", {"location": location})
    state.log.append(operation)
    return execute(operation, state)


# def insert(self, template_tree, specification, location, change_dict):
def insert(state: OperationState, location):
    """
    Modifies the
    """
    before_hash = state.log.get_hash()
    result = execute(Operation("insert", {"target": location}), state)
    assert result is None

    return before_hash


def delete(state, location):
    """
    Modifies the
    """
    before_hash = state.log.get_hash()
    result = execute(state.log, Operation("insert", {"location": location}), state)
    assert result is None

    return before_hash


def update(state, location, change_dict):
    """
    dsadsa dsan dsanm dsa
    """
    before_hash = state.log.get_hash()
    result = execute(
        state.log,
        Operation("update", {"location": location, "change": change_dict}),
        state,
    )
    assert result is None

    return before_hash


def checkpoint(log):
    """
    Validates specification

    Easiest way to validate specification is to generate the project from tree, reparse the project
    and then compare if old and generated trees are the same
    """
    ...


def rollback(state: OperationState, hash_signature: str | None):
    rollback_operations = []

    for operation in state.log.get_log():
        rollback_operations.append(reverse_operation(operation))

        if operation.get_hash() == hash_signature or hash_signature is None:
            rollback_operations = reversed(rollback_operations)
            break
    else:
        raise Exception(f'"{hash_signature}" is not ')

    for operation in rollback_operations:
        execute(operation, state, False)

    return state.log.get_hash()


def rewrite(
    log,
    template_tree,
    spec,
    source_template_id,
    target_template_id,
    transition_dict,
    const_transition_dict,
):
    before_hash = checkpoint(log, template_tree, spec)
    search_query = {"template_id": source_template_id}
    objects_to_rewrite = select(
        log, template_tree, spec, {"template_id": source_template_id}
    )

    for item in objects_to_rewrite:
        spec = {}

        if transition_dict:
            spec |= {
                k: value
                for k, value in generate_specification(item).items()
                if k in transition_dict
            }

        spec |= const_transition_dict
        id_ = log.insert(log, template_tree, spec, item.location, target_template_id)
        log.update(log, template_tree, spec, {"id_": id_}, spec)

    delete(log, template_tree, spec, search_query)

    return before_hash


def move(log): ...
