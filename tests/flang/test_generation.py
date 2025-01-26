import unittest

from flang.generators import generate_specification, get_constructed_ast
from flang.interactive_flang_object import InteractiveFlangObject
from flang.parsers.xml import parse_text
from flang.tools import ast_to_string, diff

from . import generation_templates as gtpl
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
    [gtpl.JAVASCRIPT_CODE_TEMPLATE, gtpl.JS_CODE_SAMPLE_3],
    [gtpl.PYTHON_CODE_TEMPLATE, gtpl.PYTHON_CODE_SAMPLE_FIZZBUZZ],
]

FILE_TEMPLATES = [
    [tpl.TEST_TEMPLATE_FILES_EASY, tpl.TEST_SAMPLE_FILES + "/easy"],
    [tpl.TEST_TEMPLATE_FILES_XML, tpl.TEST_SAMPLE_FILES + "/xml"],
]


class GeneratorTestCase(unittest.TestCase):
    # does not assert anything
    def test_generate_text_sanity_check(self):
        for template, _ in TEXT_TEMPLATES:
            template_tree = parse_text(template, validate_attributes=True)
            flang_tree = get_constructed_ast(template_tree, {}, fill_missing=True)
            # print(ast_to_string(flang_tree))

    # does not assert anything
    def test_create_specification_sanity_check(self):
        for template, sample in TEXT_TEMPLATES:
            template_tree = parse_text(template, validate_attributes=True)
            flang_tree = InteractiveFlangObject.from_string(
                template_tree, sample
            ).flang_tree
            generate_specification(template_tree, flang_tree)

    def test_lossless_generation_cycle_text(self):
        for template, sample in TEXT_TEMPLATES:
            template_tree = parse_text(template, validate_attributes=True)
            flang_tree = InteractiveFlangObject.from_string(
                template_tree, sample
            ).flang_tree
            # print("====================== original:")
            # print(flang_tree)

            spec = generate_specification(template_tree, flang_tree)
            generated = get_constructed_ast(template_tree, spec, fill_missing=False)

            # print("====================== generated:")
            # print(generated)
            # print("====================== spec:")
            # print(spec)
            # print("====================== diff:")
            # print(diff(flang_tree, generated))
            self.assertEqual(flang_tree, generated)

    def test_lossless_generation_cycle_files(self):
        for template, filepath in FILE_TEMPLATES:
            template_tree = parse_text(template, validate_attributes=True)
            flang_tree = InteractiveFlangObject.from_filenames(
                template_tree, [filepath]
            ).flang_tree

            spec = generate_specification(template_tree, flang_tree)
            generated = get_constructed_ast(
                template_tree, spec, fill_missing=False
            ).first_child  # TODO: wtf dude...

            # print(diff(flang_tree, generated))
            # print("======================")
            # print(flang_tree)
            # print("======================")
            # print(generated)
            # print("======================")
            # print(spec)

            self.assertEqual(flang_tree, generated)
