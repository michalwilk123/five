import unittest

from flang.exceptions import MatchNotFoundError, TextNotParsedError
from flang.parser import FlangXMLParser
from flang.processors import FlangProjectProcessor
from flang.structures import FlangInputReader, FlangObject, FlangTextMatchObject

from . import templates as tpl


class FlangParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = FlangXMLParser()

    def _parse_template(
        self, template: str, sample: str
    ) -> tuple[FlangObject, FlangTextMatchObject]:
        flang_object = self.parser.parse_text(template)
        processor = FlangProjectProcessor(flang_object)
        reader = FlangInputReader(sample)

        structured_text = processor.forward(reader)
        return flang_object, structured_text

    def test_basic(self):
        self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE)

    def test_failure_wrong_symbol(self):
        with self.assertRaises(MatchNotFoundError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_1)

    def test_failure_not_fully_matched(self):
        with self.assertRaises(TextNotParsedError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_2)

    def test_choice(self):
        flang_object, match_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "AAA")
        constr = match_object.content[0].get_construct(flang_object)
        self.assertEqual(constr.construct_name, "text")

        flang_object, match_object = self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE, "SOMEVALUE"
        )
        constr = match_object.content[0].get_construct(flang_object)
        self.assertEqual(constr.construct_name, "regex")

    def test_choice_nested(self):
        self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE_NESTED, tpl.TEST_CHOICE_NESTED_SAMPLE
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

    def test_file_simple(self): ...

    def test_file_directories(self): ...

    def test_file_hard(self): ...
