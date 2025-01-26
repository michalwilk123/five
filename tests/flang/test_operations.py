import unittest
from copy import deepcopy

import flang.operations.lib as ops
from flang.interactive_flang_object import InteractiveFlangObject
from flang.parsers.xml import parse_text
from flang.structures import Operation
from flang.utils.common import dict_hash

from . import templates as t


class OperationsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self) -> None:
        template_tree = parse_text(t.TEST_TEMPLATE_REWRITE, validate_attributes=True)
        self.interactive_object = InteractiveFlangObject.from_string(
            template_tree, t.REWRITE_SAMPLE_1
        )
        self.baseline = deepcopy(self.interactive_object.flang_tree)

    # def test_insert(self):
    #     self.interactive_object.run()

    def test_select(self):
        before_hash = dict_hash(self.interactive_object.specification)

        with self.interactive_object.run_operation() as state:
            res1 = ops.select(state, "sequence.greeting.choice.polish.name")
            res2 = ops.select(state, ".*.polish.*")

        self.assertEqual(
            before_hash,
            dict_hash(self.interactive_object.specification),
            "Select operation should not modify the state",
        )
        self.assertEqual(len(res1), 1)
        self.assertEqual(len(res2), 2)

    def test_insert(self): ...

    # def test_insert_2(self):
    #     operation_1 = Operation("insert", {"after": "sequence.greeting(4)", "template": "sequence.text"})
    #     operation_2 = Operation("insert", {"after": "sequence.greeting(4)", "template": "sequence.text"})
    #     operation_3 = Operation("insert", {"after": "sequence.text", "template": "sequence.text"})

    #     id_1 = insert(self.state, "sequence.greeting(4)", "sequence.text")

    #     state_1 = deepcopy(self.interactive_object.flang_tree)
    #     id_2 = self.interactive_object.run(operation_2)

    #     self.assertIsNotNone(self.interactive_object.flang_tree.full_search("sequence.text"))

    #     self.interactive_object.rollback(id_2)
    #     id_2 = self.interactive_object.run(operation_2)
    #     self.interactive_object.run(operation_3)
    #     state_3 = deepcopy(self.interactive_object.flang_tree)
    #     self.interactive_object.rollback(id_1) # rollback twice

    #     self.assertEqual(self.interactive_object.flang_tree, state_1)

    #     self.interactive_object.run(operation_2, operation_3)
    #     self.assertEqual(self.interactive_object.flang_tree, state_3)

    # def test_insert_invalid(self): ...

    # def test_delete(self): ...

    # def test_delete_not_optional(self): ...


class ComplexOperationsTestCase(unittest.TestCase):
    def test_rewrite_fizzbuz(self): ...

    def test_rewrite_fizzbuz_serialized(self): ...
