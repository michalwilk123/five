import unittest

from flang.core.parsers import parse_user_language
from flang.core.spec_generation import generate_specification
from flang.parsers.xml import parse_text
from flang.structures import FlangTextInputReader

from . import templates as tpl

TEXT_TEMPLATES = [
    # [tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE],
    # [tpl.TEST_TEMPLATE_CHOICE_NESTED, tpl.TEST_CHOICE_NESTED_SAMPLE],
    [tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_2],
    [tpl.TEST_TEMPLATE_CHOICE_AND_MULTI, tpl.TEST_CHOICE_AND_MULTI_SAMPLE],
    [tpl.TEST_TEMPLATE_USE, "foo"],
    [tpl.TEST_TEMPLATE_MULTI, tpl.TEST_SAMPLE_MULTI],
    [tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_3],
    [tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_TEMPLATE_CHOICE_TERMINAL],
    [tpl.TEST_TEMPLATE_LINKING, tpl.TEST_SAMPLE_LINKING],
    [tpl.TEST_TEMPLATE_FUNCTION_1, "say hello_world"],
]


class SpecGenerationTestCase(unittest.TestCase):
    def test_generation(self):
        for template, sample in TEXT_TEMPLATES:
            # template, sample = tpl.TEST_TEMPLATE_CHOICE_AND_MULTI, tpl.TEST_CHOICE_AND_MULTI_SAMPLE

            flang_ast = parse_text(template, validate_attributes=True)
            reader = FlangTextInputReader(sample)
            user_ast = parse_user_language(flang_ast, reader)
            print(generate_specification(flang_ast, user_ast))
            print("===============\n")
