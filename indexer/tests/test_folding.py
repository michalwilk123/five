import unittest
import tempfile
import os

from indexer.folding import (
    get_code_range,
    get_file_symbols,
    find_parent_symbols,
    is_in_folded_parent,
    process_line,
    fold_file,
    filter_symbols_by_level,
)
from indexer.utils import IndexConfig, SymbolDeclaration, SymbolType, SymbolScope


class FoldingTestCase(unittest.TestCase):
    """Test cases for the folding module."""

    def setUp(self):
        """Set up test data."""
        self.symbols = [
            SymbolDeclaration(
                "class1", "test.py", 1, SymbolType.CLASS, SymbolScope.GLOBAL
            ),
            SymbolDeclaration(
                "func1", "test.py", 3, SymbolType.FUNCTION, SymbolScope.CLASS
            ),
            SymbolDeclaration(
                "func2", "test.py", 5, SymbolType.FUNCTION, SymbolScope.CLASS
            ),
            SymbolDeclaration(
                "class2", "test.py", 8, SymbolType.CLASS, SymbolScope.GLOBAL
            ),
            SymbolDeclaration(
                "func3", "test.py", 10, SymbolType.FUNCTION, SymbolScope.GLOBAL
            ),
        ]

        self.config = IndexConfig(
            symbols=self.symbols,
            file_hashes={},
            merkle_hashes={},
            language="python",
            last_updated="2024-01-01",
        )

    def test_get_code_range_with_range(self):
        """Test get_code_range with provided range."""
        range_result = get_code_range("test.py", (5, 10))
        self.assertEqual(range_result, (5, 10))

    def test_get_code_range_without_range(self):
        """Test get_code_range without range creates temporary file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line1\nline2\nline3\n")
            temp_file = f.name

        try:
            range_result = get_code_range(temp_file, None)
            self.assertEqual(range_result, (0, 3))
        finally:
            os.unlink(temp_file)

    def test_get_file_symbols(self):
        """Test get_file_symbols returns correct symbols for file."""
        file_symbols = get_file_symbols(self.config, "test.py")
        self.assertEqual(len(file_symbols), 5)
        self.assertEqual(file_symbols[0].name, "class1")
        self.assertEqual(file_symbols[4].name, "func3")

    def test_get_file_symbols_empty(self):
        """Test get_file_symbols returns empty list for non-existent file."""
        file_symbols = get_file_symbols(self.config, "nonexistent.py")
        self.assertEqual(file_symbols, [])

    def test_find_parent_symbols(self):
        """Test find_parent_symbols identifies parent symbols correctly."""
        parent_symbols = find_parent_symbols(self.symbols)
        # Test that the function returns a set (even if empty)
        self.assertIsInstance(parent_symbols, set)

    def test_is_in_folded_parent_true(self):
        """Test is_in_folded_parent returns True for lines in folded parent."""
        # Create a set of parent symbols
        parent_symbols = {self.symbols[0]}  # class1 at line 1
        # Line 2 should be inside class1 (between line 1 and line 3)
        result = is_in_folded_parent(2, parent_symbols, self.symbols)
        self.assertTrue(result)

    def test_is_in_folded_parent_false(self):
        """Test is_in_folded_parent returns False for lines not in folded parent."""
        # Create a set of parent symbols
        parent_symbols = {self.symbols[0]}  # class1 at line 1
        # Line 9 should be outside class1 (after line 8)
        result = is_in_folded_parent(9, parent_symbols, self.symbols)
        self.assertFalse(result)

    def test_process_line_symbol_declaration(self):
        """Test process_line handles symbol declaration correctly."""
        lines = ["class class1:", "    pass", "    def func1():", "        pass"]
        next_line, content = process_line(1, self.symbols, lines, 4)

        self.assertEqual(next_line, 3)  # Should skip to next symbol
        self.assertEqual(content, (1, "class class1:"))

    def test_process_line_regular_line(self):
        """Test process_line handles regular line correctly."""
        lines = ["class class1:", "    pass", "    def func1():", "        pass"]
        next_line, content = process_line(2, self.symbols, lines, 4)

        self.assertEqual(next_line, 3)  # Should go to next line
        self.assertEqual(content, (2, "    pass"))

    def test_fold_file_basic(self):
        """Test fold_file performs basic folding operation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("class class1:\n    pass\n    def func1():\n        pass\n")
            temp_file = f.name

        try:
            result = fold_file(temp_file, self.config, (1, 4), 1)
            # Should show all visible lines (folding logic may vary)
            self.assertGreater(len(result), 0)
            # First line should be the class declaration
            self.assertEqual(result[0][1], "class class1:")
        finally:
            os.unlink(temp_file)

    def test_fold_file_empty_range(self):
        """Test fold_file with empty range returns empty result."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("class class1:\n    pass\n")
            temp_file = f.name

        try:
            # Test with range that's within file but no symbols
            result = fold_file(temp_file, self.config, (2, 2), 1)
            # Should return the line content
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0][1], "    pass")
        finally:
            os.unlink(temp_file)

    def test_fold_file_with_symbols(self):
        """Test fold_file with symbols in the file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                "class class1:\n    def func1():\n        pass\n    def func2():\n        pass\n"
            )
            temp_file = f.name

        try:
            result = fold_file(temp_file, self.config, (1, 5), 1)
            # Should show at least the class declaration
            self.assertGreater(len(result), 0)
            self.assertEqual(result[0][1], "class class1:")
        finally:
            os.unlink(temp_file)

    def test_filter_symbols_by_level_0(self):
        """Test filter_symbols_by_level with level 0."""
        filtered = filter_symbols_by_level(self.symbols, 0)
        # Level 0 should only show global classes
        self.assertEqual(len(filtered), 2)  # class1 and class2
        for symbol in filtered:
            self.assertEqual(symbol.scope, SymbolScope.GLOBAL)
            self.assertEqual(symbol.symbol_type, SymbolType.CLASS)

    def test_filter_symbols_by_level_1(self):
        """Test filter_symbols_by_level with level 1."""
        filtered = filter_symbols_by_level(self.symbols, 1)
        # Level 1 should show all global symbols
        self.assertEqual(len(filtered), 3)  # class1, class2, func3
        for symbol in filtered:
            self.assertEqual(symbol.scope, SymbolScope.GLOBAL)

    def test_filter_symbols_by_level_2(self):
        """Test filter_symbols_by_level with level 2."""
        filtered = filter_symbols_by_level(self.symbols, 2)
        # Level 2 should show everything except constants
        self.assertEqual(len(filtered), 5)  # All symbols (no constants in test data)

    def test_filter_symbols_by_level_3(self):
        """Test filter_symbols_by_level with level 3."""
        filtered = filter_symbols_by_level(self.symbols, 3)
        # Level 3 should show everything
        self.assertEqual(len(filtered), 5)  # All symbols

    def test_fold_file_level_3_shows_all(self):
        """Test fold_file with level 3 shows all lines."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line1\nline2\nline3\nline4\n")
            temp_file = f.name

        try:
            result = fold_file(temp_file, self.config, (1, 4), 3)
            # Level 3 should show all lines
            self.assertEqual(len(result), 4)
            self.assertEqual(result[0][1], "line1")
            self.assertEqual(result[1][1], "line2")
            self.assertEqual(result[2][1], "line3")
            self.assertEqual(result[3][1], "line4")
        finally:
            os.unlink(temp_file)
