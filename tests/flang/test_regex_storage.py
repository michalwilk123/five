import re
import unittest

from flang.utils import regex


class RegexStorageTestCase(unittest.TestCase):
    def test_create_pattern(self):
        pattern = regex.lex_storage.create_pattern("{vname}")
        self.assertEqual(pattern, regex.VNAME)

        pattern = regex.lex_storage.create_pattern("{InTeGeR}")
        self.assertEqual(pattern, regex.INTEGER)

    def test_create_pattern_complex(self):
        pattern = regex.lex_storage.create_pattern("{vname|integer|number}")
        self.assertEqual(pattern, f"{regex.VNAME}|{regex.INTEGER}|{regex.NUMBER}")

        pattern = regex.lex_storage.create_pattern(
            "foo{vNaMe|inTEGer|nuMBER}bar(pat){1,3}ern"
        )
        self.assertEqual(
            pattern, f"foo{regex.VNAME}|{regex.INTEGER}|{regex.NUMBER}bar(pat){{1,3}}ern"
        )

    def test_create_example(self):
        example = regex.lex_storage.generate_example("{vname}")
        self.assertIn(example, regex.VNamePattern.examples)

        example = regex.lex_storage.generate_example("{integer}")
        self.assertIn(example, regex.IntegerPattern.examples)

    def test_create_example_complex(self):
        example = regex.lex_storage.generate_example(
            "{vname}; value:{integer|number}; value:{string}"
        )
        examples_chunks = example.split("; value:")

        self.assertIn(examples_chunks[0], regex.VNamePattern.examples)
        self.assertIn(
            examples_chunks[1],
            regex.IntegerPattern.examples + regex.NumberPattern.examples,
        )
        self.assertIn(examples_chunks[2], regex.StringPattern.examples)
