import unittest

from flang.exceptions import MatchNotFoundError, TextNotParsedError
from flang.parser import FlangXMLParser
from flang.processors import FlangTextProcessor
from flang.structures import FlangObject, FlangStructuredText

from . import templates as tpl


class FlangParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = FlangXMLParser()

    def _parse_template(self, template: str, sample: str) -> tuple[FlangObject, FlangStructuredText]:
        flang_object = self.parser.parse_text(template)
        processor = FlangTextProcessor(flang_object)
        structured_text = processor.forward(sample)
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

        flang_object, match_object = self._parse_template(tpl.TEST_TEMPLATE_CHOICE, "SOMEVALUE")
        constr = match_object.content[0].get_construct(flang_object)
        self.assertEqual(constr.construct_name, "regex")

    def test_use(self):
        self._parse_template(tpl.TEST_TEMPLATE_USE, "foo")

    def test_multi(self):
        self._parse_template(tpl.TEST_TEMPLATE_MULTI, tpl.TEST_SAMPLE_MULTI)

    def test_optional(self): ...
