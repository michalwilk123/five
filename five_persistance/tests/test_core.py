import os
import shutil
import tempfile
import unittest

from five_persistance.core import get_symbol_declarations_db


class CoreTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "path_to_config", ".five")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_symbol_declarations_db_basic_functionality(self):
        """Test basic functionality of get_symbol_declarations_db"""
        # Test writing and reading from the database
        with get_symbol_declarations_db(self.config_path) as db:
            db["key"] = "value"

        with get_symbol_declarations_db(self.config_path) as db:
            self.assertEqual(db["key"], "value")

        # Verify the database file was created
        expected_db_path = os.path.join(self.config_path, "symbol-declarations.shelve")
        self.assertTrue(os.path.exists(expected_db_path))
