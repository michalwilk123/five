"""Shared path constants for test modules."""

import importlib.util
from pathlib import Path


_TESTS_SPEC = importlib.util.find_spec("tests")
if _TESTS_SPEC is None or not _TESTS_SPEC.submodule_search_locations:
    raise RuntimeError("Unable to locate tests package paths")

_SEARCH_PATHS = list(_TESTS_SPEC.submodule_search_locations)
if not _SEARCH_PATHS:
    raise RuntimeError("Tests package does not expose search locations")

TESTS_DIR = Path(_SEARCH_PATHS[0]).resolve()
SYSTEST_DIR = TESTS_DIR / "systest"
TINYDB_DIR = SYSTEST_DIR / "tinydb"
USER_CHANGES_DIR = SYSTEST_DIR / "user-changes"
FIVE_CLI_DIR = TESTS_DIR.parent / "five_cli"

