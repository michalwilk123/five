import unittest

from flang.interactive_flang_object import BuiltinEvent, InteractiveFlangObject
from flang.parsers.xml import parse_text
from flang.structures import BaseUserAST, FlangAST
from flang.utils.exceptions import MatchNotFoundError, TextNotParsedError

from . import templates as tpl


class ParserTestCase(unittest.TestCase):
    def _parse_template(
        self, template: str, sample: str, file: bool = False
    ) -> InteractiveFlangObject:
        flang_ast = parse_text(template, validate_attributes=True)

        if file:
            interactive_object = InteractiveFlangObject.from_filenames(
                flang_ast, paths=[sample]
            )
        else:
            interactive_object = InteractiveFlangObject.from_string(flang_ast, sample)

        return interactive_object

    def test_basic(self):
        self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE)

    def test_failure_wrong_symbol(self):
        with self.assertRaises(MatchNotFoundError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_1)

    def test_failure_not_fully_matched(self):
        with self.assertRaises(TextNotParsedError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_2)

    def test_choice(self):
        interactive_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "AAA")
        user_ast_node: BaseUserAST = interactive_object.user_ast.first_child.first_child

        flang_ast_node: FlangAST = interactive_object.flang_ast.full_search(
            user_ast_node.flang_ast_path
        )
        self.assertEqual(flang_ast_node.type, "text")

        interactive_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "SOMEVALUE")
        interactive_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "AAA")
        user_ast_node: BaseUserAST = interactive_object.user_ast.first_child.first_child

        flang_ast_node: FlangAST = interactive_object.flang_ast.full_search(
            user_ast_node.flang_ast_path
        )
        self.assertEqual(flang_ast_node.type, "text")

    def test_choice_nested(self):
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_NESTED, tpl.TEST_CHOICE_NESTED_SAMPLE
        )

    def test_multi_choice_combined(self):
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_AND_MULTI, tpl.TEST_CHOICE_AND_MULTI_SAMPLE
        )

    def test_use(self):
        self._parse_template(tpl.TEST_TEMPLATE_USE, "foo")

    def test_multi(self):
        self._parse_template(tpl.TEST_TEMPLATE_MULTI, tpl.TEST_SAMPLE_MULTI)

    def test_optional(self):
        self._parse_template(tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_1)
        self._parse_template(tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_2)

        with self.assertRaises(TextNotParsedError):
            self._parse_template(tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_3)

    def test_recursive(self):
        # todo: parametrize?
        # self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_1)
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_2)
        # self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_3)

    def test_linking(self):
        self._parse_template(tpl.TEST_TEMPLATE_LINKING, tpl.TEST_SAMPLE_LINKING)

    def test_event(self):
        interactive_object = self._parse_template(
            tpl.TEST_TEMPLATE_FUNCTION_1, "say hello_world"
        )
        self.assertDictEqual(interactive_object.context, {"result": "hello_world"})

    def test_event_remote_with_alias(self):
        interactive_object = self._parse_template(
            tpl.TEST_TEMPLATE_FUNCTION_2, "say witaj_swiecie"
        )
        self.assertDictEqual(interactive_object.context, {"result": "witaj_swiecie1"})

    def test_multiple_events_priorities(self):
        interactive_object = self._parse_template(
            tpl.TEST_TEMPLATE_FUNCTION_3, "second first"
        )

        contexts = [
            ctx
            for ctx in iter(
                interactive_object.event_storage.execute_iter(BuiltinEvent.ON_READ.value)
            )
        ]
        self.assertDictEqual(contexts[0], {"message": "first"})
        self.assertDictEqual(contexts[1], {"message": "second"})

    def test_file_easy(self):
        self._parse_template(
            tpl.TEST_TEMPLATE_FILES_EASY, tpl.TEST_SAMPLE_FILES + "/easy", True
        )

    def test_file_xml(self):
        self._parse_template(
            tpl.TEST_TEMPLATE_FILES_XML, tpl.TEST_SAMPLE_FILES + "/xml", True
        )

    def test_file_medium(self):
        ...
        # self._parse_template(
        #     tpl.TEST_TEMPLATE_FILES_XML, tpl.TEST_SAMPLE_FILES + "/medium", True
        # )

    def test_file_hard(self): ...
