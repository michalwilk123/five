import unittest
from pprint import pprint

from flang.core.generators import generate_specification, get_constructed_ast
from flang.interactive_flang_object import InteractiveFlangObject
from flang.parsers.xml import parse_text

from . import templates as tpl

TEXT_TEMPLATES = [
    [tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE],
    [tpl.TEST_TEMPLATE_CHOICE_NESTED, tpl.TEST_CHOICE_NESTED_SAMPLE],
    [tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_2],
    [tpl.TEST_TEMPLATE_CHOICE_AND_MULTI, tpl.TEST_CHOICE_AND_MULTI_SAMPLE],
    [tpl.TEST_TEMPLATE_USE, "foo"],
    [tpl.TEST_TEMPLATE_MULTI, tpl.TEST_SAMPLE_MULTI],
    [tpl.TEST_TEMPLATE_RECURSIVE, tpl.TEST_SAMPLE_RECURSIVE_3],
    [tpl.TEST_TEMPLATE_CHOICE_TERMINAL, tpl.TEST_SAMPLE_TERMINAL_PARSING],
    [tpl.TEST_TEMPLATE_LINKING, tpl.TEST_SAMPLE_LINKING],
    [tpl.TEST_TEMPLATE_FUNCTION_1, "say hello_world"],
]


class GeneratorTestCase(unittest.TestCase):
    def test_generate_text_sanity_check(self):
        for template, _ in TEXT_TEMPLATES:
            flang_ast = parse_text(template, validate_attributes=True)
            get_constructed_ast(flang_ast, {}, fill_missing=True)

    def test_create_specification_sanity_check(self):
        for template, sample in TEXT_TEMPLATES:
            flang_ast = parse_text(template, validate_attributes=True)
            user_ast = InteractiveFlangObject.from_string(flang_ast, sample).user_ast
            generate_specification(flang_ast, user_ast)

    def test_lossless_generation_cycle(self):
        for template, sample in TEXT_TEMPLATES:
            flang_ast = parse_text(template, validate_attributes=True)
            user_ast = InteractiveFlangObject.from_string(flang_ast, sample).user_ast

            spec = generate_specification(flang_ast, user_ast)
            generated = get_constructed_ast(flang_ast, spec, fill_missing=False)
            self.assertEqual(user_ast, generated)
