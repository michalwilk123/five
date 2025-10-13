"""
Simplified RepoTestCase class using Click's isolated filesystem.
Provides automatic repository copying and cleanup for testing.
"""

import unittest
import shutil
from pathlib import Path
from typing import List
from click.testing import CliRunner


class RepoTestCase(unittest.TestCase):
    """
    Base test case class that copies repositories to isolated test environments.

    Uses Click's isolated_filesystem() to create temporary test directories
    and copies specified repositories for safe testing.

    Usage:
        class MyRepoTest(RepoTestCase):
            repo_paths = ['/path/to/repo1', '/path/to/repo2']

            def test_something(self):
                # Work with copied repos in self.temp_repos
                # Changes are automatically cleaned up
                pass
    """

    repo_paths: List[str] = []

    def setUp(self):
        """Set up isolated filesystem and copy repositories."""
        self.runner = CliRunner()
        self.fs_context = self.runner.isolated_filesystem()
        self.temp_dir = self.fs_context.__enter__()
        self.temp_repos = {}

        # Copy each repository to the isolated filesystem
        for repo_path in self.repo_paths:
            repo_path = Path(repo_path).resolve()
            if not repo_path.exists():
                self.skipTest(f"Repository path does not exist: {repo_path}")

            if not (repo_path / '.git').exists():
                self.skipTest(f"Not a git repository: {repo_path}")

            # Create destination path in temp directory
            repo_name = repo_path.name
            temp_repo_path = Path(self.temp_dir) / repo_name

            # Copy the entire repository
            shutil.copytree(repo_path, temp_repo_path)
            self.temp_repos[str(repo_path)] = str(temp_repo_path)

    def tearDown(self):
        """Clean up isolated filesystem."""
        if hasattr(self, 'fs_context'):
            self.fs_context.__exit__(None, None, None)

    def get_temp_repo_path(self, original_path: str) -> str:
        """Get the temporary path for a copied repository."""
        return self.temp_repos.get(str(Path(original_path).resolve()))


class RepoTestCaseWithDebug(RepoTestCase):
    """RepoTestCase with debug logging enabled."""

    def setUp(self):
        super().setUp()
        print(f"[RepoTestCase] Created temp directory: {self.temp_dir}")
        for orig, temp in self.temp_repos.items():
            print(f"[RepoTestCase] Copied {orig} -> {temp}")

    def tearDown(self):
        print(f"[RepoTestCase] Cleaning up temp directory: {self.temp_dir}")
        super().tearDown()