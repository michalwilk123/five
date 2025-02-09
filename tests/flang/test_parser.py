import unittest

from flang.flang_object import BuiltinEvent, FlangObject, FlangObjectBuilder
from flang.structures import FlangAST
from flang.utils.exceptions import MatchNotFoundError, TextNotParsedError
from tests.test_utils import time_limit

from . import generation_templates as gtpl
from . import templates as tpl


class ParserTestCase(unittest.TestCase):
    def _parse_template(
        self, template: str, sample: str, file: bool = False
    ) -> FlangObject:
        builder = FlangObjectBuilder().xml_template(template, True)

        if file:
            builder = builder.filenames_sample([sample])
        else:
            builder = builder.text_sample(sample)

        return builder.build()

    def test_basic(self):
        self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE)

    def test_failure_wrong_symbol(self):
        with self.assertRaises(MatchNotFoundError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_1)

    def test_failure_not_fully_matched(self):
        with self.assertRaises(TextNotParsedError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_2)

    def test_choice(self):
        flang_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "AAA")
        flang_tree_node: FlangAST = flang_object.flang_tree.full_search(
            "import.choice"
        ).first_child
        self.assertEqual(flang_tree_node.name, "text-val")

        flang_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "SOMEVALUE")
        flang_tree_node: FlangAST = flang_object.flang_tree.full_search(
            "import.choice"
        ).first_child
        self.assertEqual(flang_tree_node.name, "regex")

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
        # TODO: parametrize?
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_1)
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_2)
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_3)

    def test_choice_with_terminal(self):
        # TODO: parametrize?
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_SAMPLE_RECURSIVE_1
        )
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_SAMPLE_RECURSIVE_2
        )
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_SAMPLE_RECURSIVE_3
        )
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_SAMPLE_TERMINAL_PARSING
        )

        with self.assertRaises(TextNotParsedError):
            self._parse_template(
                tpl.TEST_TEMPLATE_CHOICE_TERMINAL,
                tpl.TEST_SAMPLE_TERMINAL_PARSING_INVALID,
            )

    def test_linking(self):
        self._parse_template(tpl.TEST_TEMPLATE_LINKING, tpl.TEST_SAMPLE_LINKING)

    def test_event(self):
        flang_object = self._parse_template(
            tpl.TEST_TEMPLATE_FUNCTION_1, "say hello_world"
        )
        self.assertDictEqual(flang_object.context, {"result": "hello_world"})

    def test_event_remote_with_alias(self):
        flang_object = self._parse_template(
            tpl.TEST_TEMPLATE_FUNCTION_2, "say witaj_swiecie"
        )
        self.assertDictEqual(flang_object.context, {"result": "witaj_swiecie1"})

    def test_multiple_events_priorities(self):
        flang_object = self._parse_template(tpl.TEST_TEMPLATE_FUNCTION_3, "second first")

        contexts = [
            ctx
            for ctx in iter(
                flang_object.event_storage.execute_iter(BuiltinEvent.ON_READ.value)
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

    def test_python_code_1(self):
        self._parse_template(gtpl.PYTHON_CODE_TEMPLATE, gtpl.PYTHON_CODE_SAMPLE_1)

    def test_python_code_2(self):
        self._parse_template(gtpl.PYTHON_CODE_TEMPLATE, gtpl.PYTHON_CODE_SAMPLE_2)

    def test_python_code_3(self):
        self._parse_template(gtpl.PYTHON_CODE_TEMPLATE, gtpl.PYTHON_CODE_SAMPLE_3)

    def test_python_code_4(self):
        self._parse_template(gtpl.PYTHON_CODE_TEMPLATE, gtpl.PYTHON_CODE_SAMPLE_4)

    def test_python_code_fizzbuzz(self):
        self._parse_template(gtpl.PYTHON_CODE_TEMPLATE, gtpl.PYTHON_CODE_SAMPLE_FIZZBUZZ)

    def test_js_code_1(self):
        self._parse_template(gtpl.JAVASCRIPT_CODE_TEMPLATE, gtpl.JS_CODE_SAMPLE_1)

    def test_js_code_2(self):
        self._parse_template(gtpl.JAVASCRIPT_CODE_TEMPLATE, gtpl.JS_CODE_SAMPLE_2)

    def test_js_code_3(self):
        self._parse_template(gtpl.JAVASCRIPT_CODE_TEMPLATE, gtpl.JS_CODE_SAMPLE_3)

    def test_js_code_4(self):
        self._parse_template(gtpl.JAVASCRIPT_CODE_TEMPLATE, gtpl.JS_CODE_SAMPLE_4)

    def test_js_code_fizzbuzz(self):
        self._parse_template(gtpl.JAVASCRIPT_CODE_TEMPLATE, gtpl.JS_CODE_SAMPLE_4)

    def test_rewrite_sample(self):
        self._parse_template(tpl.TEST_TEMPLATE_REWRITE, tpl.REWRITE_SAMPLE_1)

    def test_edge_case_sample(self):
        self._parse_template(tpl.TEST_TEMPLATE_EDGE_CASES, tpl.EDGE_CASE_SAMPLE)

    def test_halting_should_fail(self):
        with time_limit(1):
            with self.assertRaises(TextNotParsedError):
                self._parse_template(tpl.HALTING_TEST_TEMPLATE, tpl.HALTING_TEST_SAMPLE)

    def test_file_medium(self):
        ...
        # self._parse_template(
        #     tpl.TEST_TEMPLATE_FILES_XML, tpl.TEST_SAMPLE_FILES + "/medium", True
        # )

    def test_file_hard(self): ...
