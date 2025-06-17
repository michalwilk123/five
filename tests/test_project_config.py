import os
import tempfile
import unittest
from contextlib import contextmanager

from core.project_config import ConfigValidationException, FiveProjectConfig

VALID_CONFIG = """
rules = "test rules"
structure = "test structure"
examples = ["example1", "example2"]
override = ["."]
environment_defaults = {BACKEND_PACKAGES = "~/Programming/libs"}

[[objects]]
id = "test-object"
structure = "test structure"
examples = ["example1"]
globs = ["*.py"]
description = "test description"

[[scripts]]
id = "test-script"
command = "test command"
relations = "test: test"
"""

INVALID_TOML = """
invalid toml syntax
"""

INVALID_CONFIG = """
rules = "test rules"
structure = "test structure"
examples = ["example1", "example2"]
override = ["."]
environment_defaults = {BACKEND_PACKAGES = "~/Programming/libs"}

[[objects]]
id = "test-object"
# Missing required field 'structure'
examples = ["example1"]
globs = ["*.py"]
description = "test description"
"""

VALID_YAML_CONFIG = """
[[scripts]]
id = "test-script"
command = "test command"
relations = '''
django-router:
    - django-viewset:
        - django-permission:
            - django-model
        - django-model
        - django-serializer:
            - django-model
django-unittest:
    - django-viewset
    - django-permission
    - django-model
    - django-serializer
'''
"""

INVALID_YAML_CONFIG = """
[[scripts]]
id = "test-script"
command = "test command"
relations = "invalid: yaml: syntax:"
"""

MISSING_REQUIRED_FIELDS_CONFIG = """
rules = "test rules"
# Missing structure field
examples = ["example1"]
"""


@contextmanager
def temp_toml_file(content: str):
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False)
    try:
        temp_file.write(content)
        temp_file.flush()
        yield temp_file.name
    finally:
        temp_file.close()
        os.unlink(temp_file.name)


class ProjectConfigTestCase(unittest.TestCase):
    def test_valid_config(self):
        with temp_toml_file(VALID_CONFIG) as config_path:
            config = FiveProjectConfig(config_path)
            self.assertEqual(config.settings.rules, "test rules")
            self.assertEqual(config.settings.structure, "test structure")
            self.assertEqual(len(config.settings.objects), 1)
            self.assertEqual(config.settings.objects[0].id, "test-object")
            self.assertEqual(len(config.settings.scripts), 1)
            self.assertEqual(config.settings.scripts[0].id, "test-script")

    def test_invalid_toml(self):
        with temp_toml_file(INVALID_TOML) as config_path:
            with self.assertRaises(ConfigValidationException):
                FiveProjectConfig(config_path)

    def test_invalid_config(self):
        with temp_toml_file(INVALID_CONFIG) as config_path:
            with self.assertRaises(ConfigValidationException):
                FiveProjectConfig(config_path)

    def test_missing_required_fields(self):
        with temp_toml_file(MISSING_REQUIRED_FIELDS_CONFIG) as config_path:
            config = FiveProjectConfig(config_path)
            self.assertEqual(config.settings.rules, "test rules")
            self.assertIsNone(config.settings.structure)
            self.assertEqual(len(config.settings.examples), 1)

    def test_empty_config(self):
        with temp_toml_file("") as config_path:
            config = FiveProjectConfig(config_path)
            self.assertEqual(config.settings.rules, "")
            self.assertIsNone(config.settings.structure)
            self.assertEqual(len(config.settings.examples), 0)
            self.assertEqual(len(config.settings.objects), 0)
            self.assertEqual(len(config.settings.scripts), 0)

    def test_demo_toml_config(self):
        config = FiveProjectConfig("demo.toml")

        # Test rules
        self.assertIn("do not add docstrings", config.settings.rules)
        self.assertIn("surround strings in single quotes", config.settings.rules)

        # Test structure
        self.assertIn("import statements", config.settings.structure)
        self.assertIn("constants global variables", config.settings.structure)

        # Test examples
        self.assertTrue(len(config.settings.examples) > 0)
        self.assertIn("import hashlib", config.settings.examples[0])

        # Test override
        self.assertEqual(config.settings.override, ["."])

        # Test environment defaults
        self.assertEqual(
            config.settings.environment_defaults["BACKEND_PACKAGES"], "~/Programming/libs"
        )

        # Test objects
        self.assertTrue(len(config.settings.objects) > 0)
        swagger_tag = next(
            obj
            for obj in config.settings.objects
            if obj.id == "swagger-documentation-tag"
        )
        self.assertEqual(swagger_tag.globs, ["*/*/drf_yasg_constants/common.py"])

        # Test scripts
        self.assertTrue(len(config.settings.scripts) > 0)
        create_endpoint = next(
            script
            for script in config.settings.scripts
            if script.id == "create-django-endpoint"
        )
        self.assertEqual(
            create_endpoint.command,
            "Create endpoint for external api users. Make sure that every endpoint has implemented authentication mechanism",
        )
        self.assertIsNotNone(create_endpoint.relations)

    def test_yaml_relations_validation(self):
        with temp_toml_file(VALID_YAML_CONFIG) as config_path:
            config = FiveProjectConfig(config_path)
            self.assertIsNotNone(config.settings.scripts[0].relations)
            self.assertIn("django-router", config.settings.scripts[0].relations)

        with temp_toml_file(INVALID_YAML_CONFIG) as config_path:
            with self.assertRaises(ConfigValidationException):
                FiveProjectConfig(config_path)
