import unittest
from copy import deepcopy

import flang.operations.lib as ops
from flang.flang_object import FlangObject, FlangObjectBuilder
from flang.generators.common import CHOICE_INDEX_KEY, TEXT_CONTENT_KEY
from flang.parsers.xml import parse_text
from flang.utils.common import dict_hash

from . import templates as t


class OperationsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self) -> None:
        self.flang_object = (
            FlangObjectBuilder()
            .xml_template(t.TEST_TEMPLATE_REWRITE, True)
            .text_sample(t.REWRITE_SAMPLE_1)
            .build()
        )
        self.baseline = deepcopy(self.flang_object.flang_tree)

    def test_select(self):
        before_hash = dict_hash(self.flang_object.specification)

        with self.flang_object.run_operation() as state:
            res1 = ops.select(state, "sequence.greeting.choice.polish.name")
            res2 = ops.select(state, ".*.polish.*")

        self.assertEqual(
            before_hash,
            dict_hash(self.flang_object.specification),
            "Select operation should not modify the state",
        )
        self.assertEqual(len(res1), 1)
        self.assertEqual(len(res2), 2)

    def test_insert(self):
        before_hash = dict_hash(self.flang_object.specification)

        # with self.interactive_object.run_operation() as state:
        #     res1 = ops.insert(state, "sequence.greeting(4).choice.english.extra-message.text[1]")

    # def test_insert_2(self):
    #     before_hash = dict_hash(self.flang_object.specification)

    #     with self.flang_object.run_operation() as state:
    #         res1 = ops.insert(state, "sequence.greeting(5)")
    #         res1 = ops.insert(state, "sequence.greeting(5).choice")
    #         res1 = ops.update(
    #             state,
    #             "sequence.greeting(5).choice",
    #             {CHOICE_INDEX_KEY.format("sequence.greeting(5).choice"): 1},
    #         )
    #         res1 = ops.insert(state, "sequence.greeting(5).choice.polish.name")
    #         res1 = ops.update(
    #             state,
    #             "sequence.greeting(5).choice.polish.name",
    #             {
    #                 TEXT_CONTENT_KEY.format(
    #                     "sequence.greeting(5).choice.polish.name"
    #                 ): "kolejna wartosc"
    #             },
    #         )

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
