import random
import unittest

from flang.flang_object import FlangObjectBuilder
from flang.generators import (
    create_ast_strict,
    create_ast_with_patched_values,
    create_specification,
)
from flang.parsers.xml import parse_text
from flang.tools import ast_to_string, diff

from . import generation_templates as gtpl
from . import templates as tpl

TEXT_TEMPLATES = [
    [tpl.TEST_BASIC_TEMPLATE, tpl.TEST_BASIC_SAMPLE],
    [tpl.TEST_TEMPLATE_OPTIONAL, tpl.TEST_OPTIONAL_SAMPLE_2],
    [tpl.TEST_TEMPLATE_CHOICE_NESTED, tpl.TEST_CHOICE_NESTED_SAMPLE],
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
    def test_generate_text_sanity_check(self):
        """
        Sometimes may not pass because `tpl.TEST_TEMPLATE_RECURSIVE` can generate infinite trees.
        No easy way to fix for now :/
        """

        for template, _ in TEXT_TEMPLATES:
            template_tree = parse_text(template, validate_attributes=True)
            flang_tree = create_ast_with_patched_values(template_tree, {})
            # print(ast_to_string(flang_tree))

    # does not assert anything
    def test_create_specification_sanity_check(self):
        for template, sample in TEXT_TEMPLATES:
            fo = (
                FlangObjectBuilder()
                .xml_template(template, True)
                .text_sample(sample)
                .build()
            )
            create_specification(fo.template_tree, fo.flang_tree)

    def test_lossless_generation_cycle_text(self):
        for template, sample in TEXT_TEMPLATES:
            fo = (
                FlangObjectBuilder()
                .xml_template(template, True)
                .text_sample(sample)
                .build()
            )
            spec = create_specification(fo.template_tree, fo.flang_tree)
            generated = create_ast_strict(fo.template_tree, spec)

            from pprint import pprint

            # print("====================== original:")
            # print(ast_to_string(fo.flang_tree))
            # print("====================== generated:")
            # print(ast_to_string(generated))
            # print("====================== spec:")
            # print(spec)
            # print("====================== diff:")
            # print(diff(fo.flang_tree, generated))
            # print("======================")
            # print(fo.flang_tree)
            # print("======================")
            # print(generated)

            self.assertEqual(fo.flang_tree, generated)

    def test_lossless_generation_cycle_files(self):
        for template, filepath in FILE_TEMPLATES:
            fo = (
                FlangObjectBuilder()
                .xml_template(template, True)
                .filenames_sample([filepath])
                .build()
            )
            spec = create_specification(fo.template_tree, fo.flang_tree)
            generated = create_ast_strict(
                fo.template_tree, spec
            )

            # print(diff(flang_tree, generated))
            # print("======================")
            # print(flang_tree)
            # print("======================")
            # print(generated)
            # print("======================")
            # print(spec)

            self.assertEqual(fo.flang_tree, generated)
