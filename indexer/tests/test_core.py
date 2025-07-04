import os
import unittest

from tqdm import tqdm

from indexer.core import process_project
from indexer.utils import SymbolType


class ProcessProjectTestCase(unittest.TestCase):
    """Test cases for the process_project function."""

    def setUp(self):
        """Set up test using an existing test repository."""
        self.project_path = "test_repositories/tinydb"

    def test_process_project_extracts_symbols(self):
        """Test that process_project extracts symbols from Python files."""
        symbols = process_project(self.project_path, language="python")

        # Should find symbols from the Python files in the repository
        self.assertGreater(len(symbols), 0)

        symbol_types = [s.symbol_type for s in symbols]

        self.assertIn(SymbolType.FUNCTION, symbol_types)
        self.assertIn(SymbolType.CLASS, symbol_types)

    def test_process_project_symbol_types(self):
        """Test that symbols have correct types."""
        symbols = process_project(self.project_path, language="python")

        # Group symbols by type
        functions = [s for s in symbols if s.symbol_type == SymbolType.FUNCTION]
        classes = [s for s in symbols if s.symbol_type == SymbolType.CLASS]
        constants = [s for s in symbols if s.symbol_type == SymbolType.CONSTANT]

        # Should have functions and classes
        self.assertGreater(len(functions), 0)
        self.assertGreater(len(classes), 0)

    def test_process_project_file_paths(self):
        """Test that symbols have correct file paths."""
        symbols = process_project(self.project_path, language="python")

        for symbol in symbols:
            # All file paths should be relative to project root
            self.assertFalse(symbol.file_path.startswith("/"))
            self.assertTrue(symbol.file_path.endswith(".py"))

    def test_process_project_line_numbers(self):
        """Test that symbols have valid line numbers."""
        symbols = process_project(self.project_path, language="python")

        for symbol in symbols:
            self.assertIsInstance(symbol.line_number, int)
            self.assertGreater(symbol.line_number, 0)

    def test_process_project_empty_directory(self):
        """Test processing a directory that's not a git repository."""
        # Create a temporary directory without git
        import shutil
        import tempfile

        empty_dir = tempfile.mkdtemp()
        try:
            symbols = process_project(empty_dir, language="python")
            # Should return empty list for non-git directory
            self.assertEqual(symbols, [])
        finally:
            shutil.rmtree(empty_dir)

    def test_process_project_default_language(self):
        """Test that process_project defaults to python language."""
        symbols_default = process_project(self.project_path)
        symbols_python = process_project(self.project_path, language="python")

        # Should return the same results
        self.assertEqual(len(symbols_default), len(symbols_python))
        self.assertEqual(
            [s.name for s in symbols_default], [s.name for s in symbols_python]
        )

    def test_process_project_unsupported_language(self):
        """Test that process_project raises on unsupported languages."""
        with self.assertRaises(AssertionError):
            process_project(self.project_path, language="unsupported")


class ProcessAllRepositoriesTestCase(unittest.TestCase):
    """Parametrized test cases for processing all test repositories."""

    def test_all_repositories(self):
        """Test that process_project can handle all test repositories."""
        test_repositories = [
            "test_repositories/tinydb",
            "test_repositories/pre-commit",
            "test_repositories/babi",
            "test_repositories/flask",
        ]

        for repo_path in tqdm(test_repositories, desc="Testing repositories"):
            with self.subTest(repository=repo_path):
                # Check that the repository directory exists
                self.assertTrue(
                    os.path.exists(repo_path), f"Repository {repo_path} does not exist"
                )

                # Process the repository with python language
                symbols = process_project(
                    repo_path, language="python", show_progress=True
                )

                # Should return a list (even if empty)
                self.assertIsInstance(symbols, list)

                # For repositories with Python files, should find some symbols
                if repo_path in ["test_repositories/tinydb", "test_repositories/flask"]:
                    self.assertGreater(
                        len(symbols), 0, f"No symbols found in {repo_path}"
                    )

                    # Check that symbols have valid structure
                    for symbol in symbols[:5]:  # Check first 5 symbols
                        self.assertIsInstance(symbol.name, str)
                        self.assertIsInstance(symbol.file_path, str)
                        self.assertIsInstance(symbol.line_number, int)
                        self.assertIsInstance(symbol.symbol_type, SymbolType)
                        self.assertTrue(symbol.file_path.endswith(".py"))
                        self.assertGreater(symbol.line_number, 0)
