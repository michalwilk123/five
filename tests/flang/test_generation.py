import unittest

from flang.core.generators import generate_ast
from flang.parsers.xml import parse_text

from . import templates as tpl

TEXT_TEMPLATES = [
    [tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE],
    [tpl.TEST_TEMPLATE_CHOICE_NESTED, tpl.TEST_CHOICE_NESTED_SAMPLE],
    [tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_3],
    [tpl.TEST_TEMPLATE_CHOICE_AND_MULTI, tpl.TEST_CHOICE_AND_MULTI_SAMPLE],
    [tpl.TEST_TEMPLATE_USE, "foo"],
    [tpl.TEST_TEMPLATE_MULTI, tpl.TEST_SAMPLE_MULTI],
    [tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_TEMPLATE_RECURSIVE],
    [tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_TEMPLATE_CHOICE_TERMINAL],
    [tpl.TEST_TEMPLATE_LINKING, tpl.TEST_SAMPLE_LINKING],
    [tpl.TEST_TEMPLATE_FUNCTION_1, "say hello_world"],
]


class GeneratorTestCase(unittest.TestCase):
    def test_generate_text_on_empty_setup(self):

        for template, _ in TEXT_TEMPLATES:
            flang_ast = parse_text(template, validate_attributes=True)
            user_ast = generate_ast(flang_ast)
