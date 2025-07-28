import os
import tempfile
import unittest

from indexer.parsers.python import parse, parse_source
from indexer.utils import SymbolType, SymbolScope


class SymbolParsingTestCase(unittest.TestCase):
    """Test cases for Python symbol parsing functions."""

    def test_parse_source_and_parse_equivalence(self):
        """Test that parse_source and parse produce the same results."""
        test_code = '''
def global_function():
    """A global function."""
    pass

class TestClass:
    """A test class."""
    
    def class_method(self):
        """A method in the class."""
        pass

GLOBAL_CONSTANT = 42
another_constant = "test"
'''

        # Create a temporary file and test parse
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            temp_file_path = f.name

        try:
            # Get the directory and filename
            temp_dir = os.path.dirname(temp_file_path)
            temp_filename = os.path.basename(temp_file_path)

            # Test parse_source directly with the same filename
            symbols_from_source = parse_source(test_code, temp_filename)

            # Test parse function
            symbols_from_file = parse(temp_dir, temp_filename)

            # Both should produce the same results
            self.assertEqual(len(symbols_from_source), len(symbols_from_file))

            # Check that symbols are identical
            for i, (source_symbol, file_symbol) in enumerate(
                zip(symbols_from_source, symbols_from_file)
            ):
                self.assertEqual(source_symbol.name, file_symbol.name)
                self.assertEqual(source_symbol.symbol_type, file_symbol.symbol_type)
                self.assertEqual(source_symbol.line_number, file_symbol.line_number)
                self.assertEqual(source_symbol.file_path, file_symbol.file_path)

        finally:
            os.unlink(temp_file_path)

    def test_parse_source_with_various_symbols(self):
        """Test parse_source with different types of symbols."""
        test_code = '''
import os

# Constants
API_VERSION = "1.0"
DEBUG_MODE = True

def public_function():
    """A public function."""
    return "hello"

def _private_function():
    """A private function."""
    return "world"

class PublicClass:
    """A public class."""
    
    def __init__(self):
        self.value = 42
    
    def public_method(self):
        return self.value
    
    def _private_method(self):
        return "private"

class _PrivateClass:
    """A private class."""
    
    def method(self):
        return "private class method"
'''

        symbols = parse_source(test_code, "test_module.py")

        # Should find all symbols
        symbol_names = [s.name for s in symbols]

        # Check for constants
        self.assertIn("API_VERSION", symbol_names)
        self.assertIn("DEBUG_MODE", symbol_names)

        # Check for functions
        self.assertIn("public_function", symbol_names)
        self.assertIn("_private_function", symbol_names)

        # Check for classes
        self.assertIn("PublicClass", symbol_names)
        self.assertIn("_PrivateClass", symbol_names)

        # Check for methods (now with class name prefix)
        self.assertIn("PublicClass.__init__", symbol_names)
        self.assertIn("PublicClass.public_method", symbol_names)
        self.assertIn("PublicClass._private_method", symbol_names)
        self.assertIn("_PrivateClass.method", symbol_names)

        # Check symbol types
        constants = [s for s in symbols if s.symbol_type.value == "constant/variable"]
        functions = [s for s in symbols if s.symbol_type.value == "function/method"]
        classes = [s for s in symbols if s.symbol_type.value == "class/structure"]

        self.assertEqual(len(constants), 2)  # API_VERSION, DEBUG_MODE
        self.assertGreaterEqual(len(functions), 6)  # functions + methods
        self.assertEqual(len(classes), 2)  # PublicClass, _PrivateClass

    def test_parse_source_with_syntax_error(self):
        """Test parse_source handles syntax errors gracefully."""
        invalid_code = """
def incomplete_function(
    # Missing closing parenthesis and body
"""

        symbols = parse_source(invalid_code, "invalid.py")
        self.assertEqual(symbols, [])

    def test_parse_source_empty_content(self):
        """Test parse_source with empty content."""
        symbols = parse_source("", "empty.py")
        self.assertEqual(symbols, [])

        symbols = parse_source("\n\n", "whitespace.py")
        self.assertEqual(symbols, [])

    def test_detect_globals_functions_and_variables(self):
        code = """
GLOBAL_VAR = 123

def foo():
    return 1

class Bar:
    CLASS_VAR = 42
    def method(self):
        pass
"""
        symbols = parse_source(code, "sample.py")
        names = {s.name: s for s in symbols}
        self.assertIn("GLOBAL_VAR", names)
        self.assertEqual(names["GLOBAL_VAR"].symbol_type, SymbolType.CONSTANT)
        self.assertEqual(names["GLOBAL_VAR"].scope, SymbolScope.GLOBAL)
        self.assertIn("foo", names)
        self.assertEqual(names["foo"].symbol_type, SymbolType.FUNCTION)
        self.assertEqual(names["foo"].scope, SymbolScope.GLOBAL)
        self.assertIn("Bar", names)
        self.assertEqual(names["Bar"].symbol_type, SymbolType.CLASS)
        self.assertEqual(names["Bar"].scope, SymbolScope.GLOBAL)
        self.assertIn("Bar.CLASS_VAR", names)
        self.assertEqual(names["Bar.CLASS_VAR"].symbol_type, SymbolType.CONSTANT)
        self.assertEqual(names["Bar.CLASS_VAR"].scope, SymbolScope.CLASS)
        self.assertIn("Bar.method", names)
        self.assertEqual(names["Bar.method"].symbol_type, SymbolType.FUNCTION)
        self.assertEqual(names["Bar.method"].scope, SymbolScope.CLASS)

    def test_detect_dataclass_like_declarations(self):
        """Test that dataclass-like declarations are parsed as OTHER SymbolType."""
        code = """
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Point:
    x: int
    y: int

@dataclass
class Config:
    name: str = "default"
    debug: bool = False

class SimpleClass:
    x: int = 5
    y: str = "hello"
    z: list

class EnumClass:
    ACTIVE = "active"
    INACTIVE = "inactive"

# Global annotated assignments
global_var: int = 10
another_var: str = "test"
"""
        symbols = parse_source(code, "dataclass_test.py")
        names = {s.name: s for s in symbols}

        # Check dataclass attributes are OTHER type
        self.assertIn("Point.x", names)
        self.assertEqual(names["Point.x"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["Point.x"].scope, SymbolScope.CLASS)

        self.assertIn("Point.y", names)
        self.assertEqual(names["Point.y"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["Point.y"].scope, SymbolScope.CLASS)

        self.assertIn("Config.name", names)
        self.assertEqual(names["Config.name"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["Config.name"].scope, SymbolScope.CLASS)

        self.assertIn("Config.debug", names)
        self.assertEqual(names["Config.debug"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["Config.debug"].scope, SymbolScope.CLASS)

        # Check class attributes with type annotations are OTHER type
        self.assertIn("SimpleClass.x", names)
        self.assertEqual(names["SimpleClass.x"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["SimpleClass.x"].scope, SymbolScope.CLASS)

        self.assertIn("SimpleClass.y", names)
        self.assertEqual(names["SimpleClass.y"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["SimpleClass.y"].scope, SymbolScope.CLASS)

        self.assertIn("SimpleClass.z", names)
        self.assertEqual(names["SimpleClass.z"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["SimpleClass.z"].scope, SymbolScope.CLASS)

        # Check regular class attributes remain CONSTANT type
        self.assertIn("EnumClass.ACTIVE", names)
        self.assertEqual(names["EnumClass.ACTIVE"].symbol_type, SymbolType.CONSTANT)
        self.assertEqual(names["EnumClass.ACTIVE"].scope, SymbolScope.CLASS)

        self.assertIn("EnumClass.INACTIVE", names)
        self.assertEqual(names["EnumClass.INACTIVE"].symbol_type, SymbolType.CONSTANT)
        self.assertEqual(names["EnumClass.INACTIVE"].scope, SymbolScope.CLASS)

        # Check global annotated variables are OTHER type
        self.assertIn("global_var", names)
        self.assertEqual(names["global_var"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["global_var"].scope, SymbolScope.GLOBAL)

        self.assertIn("another_var", names)
        self.assertEqual(names["another_var"].symbol_type, SymbolType.OTHER)
        self.assertEqual(names["another_var"].scope, SymbolScope.GLOBAL)

        # Verify total count
        other_symbols = [s for s in symbols if s.symbol_type == SymbolType.OTHER]
        self.assertEqual(
            len(other_symbols), 9
        )  # 7 class attributes + 2 global variables
