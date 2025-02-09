import tests.flang.templates as t
from flang.flang_object import FlangObjectBuilder
from flang.operations import lib
from flang.structures import OperationState, FlangAST, Specification

from flang.generators.specification_to_ast import expand_ast, create_ast_node
from flang.generators.common import raise_exception_value_for_key


def new_insert(state: OperationState, location: str, specification:Specification):
    before_hash = state.log.get_hash()

    # result = execute(Operation("insert", {"target": location}), state)
    # assert result is None
    new_spec = {FlangAST.join_paths(location, key): value for key, value in specification}


    node = create_ast_node(
        state.template_tree, 
        new_spec,
        location,
        raise_exception_value_for_key
    )
    expand_ast(state.template_tree, node, specification, raise_exception_value_for_key)

    return before_hash

def main():
    fo = FlangObjectBuilder()\
        .xml_template(t.TEST_TEMPLATE_REWRITE, True).text_sample(t.REWRITE_SAMPLE_1).build()

    target = "sequence.greeting(4).choice.english.extra-message.text[1]", 
    spec = {}
    
    with fo.run_operation() as state:
        new_insert(state, target, {})


if __name__ == "__main__":
    main()



