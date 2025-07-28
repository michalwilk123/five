import unittest
import tempfile
import os
import sys
from io import StringIO
from unittest.mock import patch

from indexer.differ import DiffOperation, DiffParser, FileEditor


class DiffOperationTestCase(unittest.TestCase):
    def test_diff_operation_creation(self):
        op = DiffOperation("test.py", 1, 5, ["line1", "line2"])
        self.assertEqual(op.filepath, "test.py")
        self.assertEqual(op.start_line, 1)
        self.assertEqual(op.end_line, 5)
        self.assertEqual(op.content, ["line1", "line2"])

    def test_diff_operation_repr(self):
        op = DiffOperation("test.py", 1, 5, ["line1", "line2"])
        self.assertEqual(repr(op), "DiffOperation(test.py, 1+5)")


class DiffParserTestCase(unittest.TestCase):
    def setUp(self):
        self.parser = DiffParser()

    def test_parse_simple_operation(self):
        input_data = [
            "======test.py:1+3",
            "new line 1",
            "new line 2",
            "new line 3",
            "======end",
        ]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            operations = self.parser.parse_stdin()

        self.assertEqual(len(operations), 1)
        op = operations[0]
        self.assertEqual(op.filepath, "test.py")
        self.assertEqual(op.start_line, 1)
        self.assertEqual(op.end_line, 3)
        self.assertEqual(op.content, ["new line 1", "new line 2", "new line 3"])

    def test_parse_multiple_operations(self):
        input_data = [
            "======file1.py:1+2",
            "content1",
            "content2",
            "======end",
            "======file2.py:5+7",
            "content3",
            "content4",
            "content5",
            "======end",
        ]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            operations = self.parser.parse_stdin()

        self.assertEqual(len(operations), 2)
        self.assertEqual(operations[0].filepath, "file1.py")
        self.assertEqual(operations[1].filepath, "file2.py")

    def test_parse_with_project_path(self):
        parser = DiffParser("/tmp/project")
        input_data = ["======src/test.py:1+2", "content", "======end"]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            operations = parser.parse_stdin()

        self.assertEqual(operations[0].filepath, "/tmp/project/src/test.py")

    def test_invalid_header_format(self):
        input_data = ["======invalid_format", "content", "======end"]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_stdin()
            self.assertIn("Invalid diff header format", str(cm.exception))

    def test_start_line_greater_than_end_line(self):
        input_data = ["======test.py:5+3", "content", "======end"]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_stdin()
            self.assertIn(
                "Start line cannot be greater than end line", str(cm.exception)
            )

    def test_missing_end_marker(self):
        input_data = ["======test.py:1+3", "content1", "content2"]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            with self.assertRaises(ValueError) as cm:
                self.parser.parse_stdin()
            self.assertIn("Missing end marker", str(cm.exception))

    def test_empty_content(self):
        input_data = ["======test.py:1+1", "======end"]

        with patch("sys.stdin", StringIO("\n".join(input_data))):
            operations = self.parser.parse_stdin()

        self.assertEqual(len(operations), 1)
        self.assertEqual(operations[0].content, [])


class FileEditorTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.editor = FileEditor()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_file(self, filename, content):
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_add_operations(self):
        op1 = DiffOperation("test1.py", 1, 3, ["new1", "new2"])
        op2 = DiffOperation("test2.py", 1, 2, ["new3"])

        self.editor.add_operations([op1, op2])

        self.assertIn("test1.py", self.editor.file_operations)
        self.assertIn("test2.py", self.editor.file_operations)
        self.assertEqual(len(self.editor.file_operations["test1.py"]), 1)
        self.assertEqual(len(self.editor.file_operations["test2.py"]), 1)

    def test_validate_nonexistent_file(self):
        op = DiffOperation("nonexistent.py", 1, 3, ["content"])
        self.editor.add_operations([op])

        with self.assertRaises(ValueError) as cm:
            self.editor.validate_operations()
        self.assertIn("File does not exist", str(cm.exception))

    def test_validate_directory_path(self):
        dir_path = os.path.join(self.temp_dir, "testdir")
        os.makedirs(dir_path)

        op = DiffOperation(dir_path, 1, 3, ["content"])
        self.editor.add_operations([op])

        with self.assertRaises(ValueError) as cm:
            self.editor.validate_operations()
        self.assertIn("Path is not a file", str(cm.exception))

    def test_validate_empty_file(self):
        filepath = self.create_test_file("empty.txt", "")

        op = DiffOperation(filepath, 1, 3, ["content"])
        self.editor.add_operations([op])

        with self.assertRaises(ValueError) as cm:
            self.editor.validate_operations()
        self.assertIn("File is empty", str(cm.exception))

    def test_validate_line_range_exceeds_file(self):
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        op = DiffOperation(filepath, 1, 5, ["content"])
        self.editor.add_operations([op])

        with self.assertRaises(ValueError) as cm:
            self.editor.validate_operations()
        self.assertIn("End line 5 exceeds file length 3", str(cm.exception))

    def test_validate_overlapping_ranges(self):
        filepath = self.create_test_file(
            "test.txt", "line1\nline2\nline3\nline4\nline5\n"
        )

        op1 = DiffOperation(filepath, 1, 3, ["content1"])
        op2 = DiffOperation(filepath, 2, 4, ["content2"])
        self.editor.add_operations([op1, op2])

        with self.assertRaises(ValueError) as cm:
            self.editor.validate_operations()
        self.assertIn("Overlapping line ranges", str(cm.exception))

    def test_apply_single_operation(self):
        filepath = self.create_test_file(
            "test.txt", "original1\noriginal2\noriginal3\n"
        )

        op = DiffOperation(filepath, 2, 2, ["replaced"])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        self.assertEqual(modified_files, [filepath])

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "original1\nreplaced\noriginal3\n")

    def test_apply_multiple_operations_same_file(self):
        filepath = self.create_test_file(
            "test.txt", "line1\nline2\nline3\nline4\nline5\n"
        )

        op1 = DiffOperation(filepath, 2, 2, ["replaced1"])
        op2 = DiffOperation(filepath, 4, 4, ["replaced2"])
        self.editor.add_operations([op1, op2])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        self.assertEqual(modified_files, [filepath])

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "line1\nreplaced1\nline3\nreplaced2\nline5\n")

    def test_apply_operations_different_files(self):
        filepath1 = self.create_test_file("test1.txt", "original1\noriginal2\n")
        filepath2 = self.create_test_file("test2.txt", "original3\noriginal4\n")

        op1 = DiffOperation(filepath1, 1, 1, ["replaced1"])
        op2 = DiffOperation(filepath2, 1, 1, ["replaced2"])
        self.editor.add_operations([op1, op2])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        self.assertEqual(set(modified_files), {filepath1, filepath2})

        with open(filepath1, "r", encoding="utf-8") as f:
            content1 = f.read()
        with open(filepath2, "r", encoding="utf-8") as f:
            content2 = f.read()

        self.assertEqual(content1, "replaced1\noriginal2\n")
        self.assertEqual(content2, "replaced2\noriginal4\n")


class OrderDependentOperationsTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.editor = FileEditor()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_file(self, filename, content):
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_order_dependent_replacements(self):
        """Test that operations are applied in reverse order to maintain line numbers"""
        filepath = self.create_test_file(
            "test.txt", "line1\nline2\nline3\nline4\nline5\n"
        )

        # These operations don't overlap and should work correctly
        op1 = DiffOperation(
            filepath, 1, 1, ["new1", "new2"]
        )  # Replace line 1 with 2 lines
        op2 = DiffOperation(filepath, 4, 4, ["new3"])  # Replace line 4 with 1 line

        self.editor.add_operations([op1, op2])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Expected: new1, new2, line2, line3, new3, line5
        expected = "new1\nnew2\nline2\nline3\nnew3\nline5\n"
        self.assertEqual(content, expected)

    def test_cascading_line_number_changes(self):
        """Test that line number changes are handled correctly when operations affect subsequent lines"""
        filepath = self.create_test_file("test.txt", "A\nB\nC\nD\nE\nF\n")

        # Insert content that changes line numbers - using non-overlapping ranges
        op1 = DiffOperation(
            filepath, 2, 2, ["B1", "B2", "B3"]
        )  # Replace B with 3 lines
        # Use line 5 (E) which exists in the original file
        op2 = DiffOperation(filepath, 5, 5, ["E1", "E2"])  # Replace E with 2 lines

        self.editor.add_operations([op1, op2])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Expected: A, B1, B2, B3, C, D, E1, E2, F
        expected = "A\nB1\nB2\nB3\nC\nD\nE1\nE2\nF\n"
        self.assertEqual(content, expected)

    def test_multiple_insertions_different_regions(self):
        """Test multiple replacements in different regions that depend on order"""
        filepath = self.create_test_file("test.txt", "start\nmiddle\nend\n")

        # Replace different lines to demonstrate order dependency
        # Replace start, middle, and end lines
        op1 = DiffOperation(filepath, 1, 1, ["before_start"])
        op2 = DiffOperation(filepath, 2, 2, ["after_start"])
        op3 = DiffOperation(filepath, 3, 3, ["before_end"])

        self.editor.add_operations([op1, op2, op3])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Expected: before_start, after_start, before_end (replacing start, middle, end)
        expected = "before_start\nafter_start\nbefore_end\n"
        self.assertEqual(content, expected)

    def test_order_dependent_line_expansion(self):
        """Test that operations are applied in reverse order to handle line expansion correctly"""
        filepath = self.create_test_file("test.txt", "A\nB\nC\nD\n")

        # First operation expands line 2 (B) to multiple lines
        op1 = DiffOperation(filepath, 2, 2, ["B1", "B2", "B3"])
        # Second operation targets line 4 (D) which should remain at line 4 after first operation
        op2 = DiffOperation(filepath, 4, 4, ["D1", "D2"])

        self.editor.add_operations([op1, op2])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Expected: A, B1, B2, B3, C, D1, D2
        # The order matters because op2 targets line 4 which is D in the original file
        expected = "A\nB1\nB2\nB3\nC\nD1\nD2\n"
        self.assertEqual(content, expected)

    def test_order_dependent_overlapping_behavior(self):
        """Test that demonstrates why overlapping ranges are not allowed - order would be critical"""
        filepath = self.create_test_file("test.txt", "original\n")

        # This test demonstrates why overlapping ranges are problematic
        # If overlapping were allowed, the order would be critical:
        # op1: replace line 1 with ["A", "B"]
        # op2: replace line 1 with ["X", "Y"]
        # Result would depend on order: either ["A", "B"] or ["X", "Y"]

        # Since overlapping is not allowed, we test the validation
        op1 = DiffOperation(filepath, 1, 1, ["A", "B"])
        op2 = DiffOperation(filepath, 1, 1, ["X", "Y"])

        self.editor.add_operations([op1, op2])

        with self.assertRaises(ValueError) as cm:
            self.editor.validate_operations()
        self.assertIn("Overlapping line ranges", str(cm.exception))

    def test_complex_non_overlapping_replacements(self):
        """Test complex scenario with non-overlapping replacements that require correct ordering"""
        filepath = self.create_test_file(
            "test.txt",
            "header\nsection1\nitem1\nitem2\nsection2\nitem3\nitem4\nfooter\n",
        )

        # Replace non-overlapping sections
        op1 = DiffOperation(filepath, 2, 4, ["new_section1", "new_item1", "new_item2"])
        op2 = DiffOperation(filepath, 6, 7, ["new_item3", "new_item3b"])

        self.editor.add_operations([op1, op2])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Expected: header, new_section1, new_item1, new_item2, section2, new_item3, new_item3b, footer
        expected = "header\nnew_section1\nnew_item1\nnew_item2\nsection2\nnew_item3\nnew_item3b\nfooter\n"
        self.assertEqual(content, expected)


class EdgeCasesTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.editor = FileEditor()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_file(self, filename, content):
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_replace_entire_file(self):
        """Test replacing the entire file content"""
        filepath = self.create_test_file("test.txt", "old1\nold2\nold3\n")

        op = DiffOperation(filepath, 1, 3, ["new1", "new2", "new3", "new4"])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "new1\nnew2\nnew3\nnew4\n"
        self.assertEqual(content, expected)

    def test_replace_single_line_with_multiple(self):
        """Test replacing a single line with multiple lines"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        op = DiffOperation(filepath, 2, 2, ["new2a", "new2b", "new2c"])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "line1\nnew2a\nnew2b\nnew2c\nline3\n"
        self.assertEqual(content, expected)

    def test_replace_multiple_lines_with_single(self):
        """Test replacing multiple lines with a single line"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\nline4\n")

        op = DiffOperation(filepath, 2, 3, ["replaced"])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "line1\nreplaced\nline4\n"
        self.assertEqual(content, expected)

    def test_replace_with_empty_content(self):
        """Test replacing content with empty lines"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        op = DiffOperation(filepath, 2, 2, [])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "line1\nline3\n"
        self.assertEqual(content, expected)

    def test_unicode_content(self):
        """Test handling of unicode content"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        unicode_content = ["café", "naïve", "résumé", "über"]
        op = DiffOperation(filepath, 2, 2, unicode_content)
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "line1\ncafé\nnaïve\nrésumé\nüber\nline3\n"
        self.assertEqual(content, expected)

    def test_special_characters_in_content(self):
        """Test handling of special characters in content"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        special_content = ["line with spaces", "line\twith\ttabs"]
        op = DiffOperation(filepath, 2, 2, special_content)
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "line1\nline with spaces\nline\twith\ttabs\nline3\n"
        self.assertEqual(content, expected)

    def test_replace_last_line(self):
        """Test replacing the last line of a file"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        op = DiffOperation(filepath, 3, 3, ["new_last"])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "line1\nline2\nnew_last\n"
        self.assertEqual(content, expected)

    def test_replace_first_line(self):
        """Test replacing the first line of a file"""
        filepath = self.create_test_file("test.txt", "line1\nline2\nline3\n")

        op = DiffOperation(filepath, 1, 1, ["new_first"])
        self.editor.add_operations([op])
        self.editor.validate_operations()

        modified_files = self.editor.apply_operations()

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        expected = "new_first\nline2\nline3\n"
        self.assertEqual(content, expected)


if __name__ == "__main__":
    unittest.main()
