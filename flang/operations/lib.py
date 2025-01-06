from .core import commit, delete, insert, select, update


def rewrite(
    log,
    template_tree,
    spec,
    source_template_id,
    target_template_id,
    transition_dict,
    const_transition_dict,
):
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
        id_ = insert(log, template_tree, spec, item.location, target_template_id)
        update(log, template_tree, spec, {"id_": id_}, spec)

    delete(log, template_tree, spec, search_query)

    return commit(log, template_tree, spec)


def move(): ...
