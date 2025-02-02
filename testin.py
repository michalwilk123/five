import tests.flang.templates as t
from flang.flang_object import FlangObjectBuilder
from flang.operations import lib
from flang.structures import OperationState

from flang.generators.specification_to_ast import _create_ast_root


def new_insert(state: OperationState, location):
    before_hash = state.log.get_hash()

    # result = execute(Operation("insert", {"target": location}), state)
    # assert result is None

    return before_hash

def main():
    fo = FlangObjectBuilder()\
        .xml_template(t.TEST_TEMPLATE_REWRITE, True).text_sample(t.REWRITE_SAMPLE_1).build()
    

    with fo.run_operation() as state:
        # lib.insert(state, )
        ...

if __name__ == "__main__":
    main()



