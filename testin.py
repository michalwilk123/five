import tests.flang.templates as t
from flang.flang_object import FlangObjectBuilder
from flang.operations import lib
from flang.structures import OperationState, FlangAST, Specification

from flang.generators.specification_to_ast import create_ast_strict
from flang.generators.common import raise_exception_value_for_key


def new_insert(state: OperationState, location: str, specification:Specification):
    before_hash = state.log.get_hash()

    # result = execute(Operation("insert", {"target": location}), state)
    # assert result is None
    new_spec = {FlangAST.join_paths(location, key): value for key, value in specification.items()}
    print(new_spec)

    body = "Jak sie masz"
    template_id = "sequence.sequence[1].extra-message"
    target = "sequence.greeting(4).choice.english.extra-message"


    # templ = state.template_tree.full_search(template_id)

    # node = create_ast_node(
    #     templ, 
    #     new_spec,
    #     location,
    #     raise_exception_value_for_key
    # )
    # expand_ast(state.template_tree, node, specification, raise_exception_value_for_key)
    nn = create_ast_strict(state.template_tree, { **state.specification, **new_spec })

    return before_hash

def main():
    fo = FlangObjectBuilder()\
        .xml_template(t.TEST_TEMPLATE_REWRITE, True).text_sample(t.REWRITE_SAMPLE_1).build()

    target = "sequence.greeting(4).choice.english.extra-message"
    spec = {"text[1]:content": "Jak sie masz?", ":children": {}}
    
    with fo.run_operation() as state:
        new_insert(state, target, spec)


if __name__ == "__main__":
    main()



