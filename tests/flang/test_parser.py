import unittest

from flang.exceptions import MatchNotFoundError, TextNotParsedError
from flang.parser import FlangXMLParser
from flang.processing import FlangProjectProcessor
from flang.structures import FlangAbstractMatchObject, FlangProjectConstruct

from . import templates as tpl


class FlangParserTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = FlangXMLParser()

    def _parse_template(
        self, template: str, sample: str, file: bool = False
    ) -> tuple[FlangProjectConstruct, list[FlangAbstractMatchObject]]:
        project_construct = self.parser.parse_text(template, validate_attributes=True)
        processor = FlangProjectProcessor(project_construct)

        if file:
            structured_text = processor.forward_filename(sample)
        else:
            structured_text = processor.forward_string(sample)

        return project_construct, structured_text

    def test_basic(self):
        self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE)

    def test_failure_wrong_symbol(self):
        with self.assertRaises(MatchNotFoundError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_1)

    def test_failure_not_fully_matched(self):
        with self.assertRaises(TextNotParsedError):
            self._parse_template(tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE_FAILURE_2)

    def test_choice(self):
        project_construct, match_object = self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE, "AAA"
        )
        constr = match_object[0].first_child.first_child

        constr = constr.get_construct(project_construct)
        self.assertEqual(constr.name, "text")

        project_construct, match_object = self._parse_template(
            tpl.TEST_TEMPLATE_CHOICE, "SOMEVALUE"
        )
        constr = match_object[0].first_child.first_child
        constr = constr.get_construct(project_construct)
        self.assertEqual(constr.name, "regex")

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
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_1)
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_2)
        self._parse_template(tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_3)

    def test_linking(self):
        self._parse_template(tpl.TEST_TEMPLATE_LINKING, tpl.TEST_SAMPLE_LINKING)

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
