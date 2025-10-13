"""
Simple git operations test using RepoTestCase.
Tests basic functionality without touching five CLI code.
Rewritten to use Click's isolated filesystem approach.
"""

import unittest
import os
import subprocess
from pathlib import Path
from tests.repo_test_case import RepoTestCaseWithDebug
from tests.test_paths import TINYDB_DIR, USER_CHANGES_DIR


class SimpleGitOperationsTest(RepoTestCaseWithDebug):
    """Test basic git operations and patch application with automatic cleanup."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        super().setUpClass()
        cls.tinydb_dir = TINYDB_DIR
        cls.user_changes_dir = USER_CHANGES_DIR

        # Configure RepoTestCase
        cls.repo_paths = [str(cls.tinydb_dir)]

    def test_git_operations_and_patches(self):
        """Test basic git operations and patch application."""
        # Get the copied repository path
        temp_tinydb_path = Path(self.get_temp_repo_path(str(self.tinydb_dir)))

        # Verify initial state
        self.assertTrue(temp_tinydb_path.exists(), f"Copied TinyDB directory should exist: {temp_tinydb_path}")
        self.assertTrue(self.user_changes_dir.exists(), f"User changes directory should exist: {self.user_changes_dir}")
        self.assertTrue((temp_tinydb_path / '.git').exists(), "Copied TinyDB should be a git repository")

        # Check initial git status
        initial_status = self.get_git_status(str(temp_tinydb_path))
        print(f"Initial git status: '{initial_status}'")

        # Apply patch_1.patch
        patch_1_path = self.user_changes_dir / "patch_1.patch"
        self.assertTrue(patch_1_path.exists(), f"patch_1.patch should exist: {patch_1_path}")

        result = self.apply_patch(str(patch_1_path), str(temp_tinydb_path))
        self.assertEqual(result.returncode, 0, f"patch_1.patch should apply successfully: {result.stderr}")

        # Check status after patch_1
        status_after_patch1 = self.get_git_status(str(temp_tinydb_path))
        self.assertTrue(bool(status_after_patch1), "Should have changes after applying patch_1")
        print(f"Status after patch_1: {status_after_patch1}")

        # Apply patch_2.patch
        patch_2_path = self.user_changes_dir / "patch_2.patch"
        self.assertTrue(patch_2_path.exists(), f"patch_2.patch should exist: {patch_2_path}")

        result = self.apply_patch(str(patch_2_path), str(temp_tinydb_path))
        self.assertEqual(result.returncode, 0, f"patch_2.patch should apply successfully: {result.stderr}")

        # Check status after patch_2
        status_after_patch2 = self.get_git_status(str(temp_tinydb_path))
        self.assertTrue(bool(status_after_patch2), "Should have changes after applying patch_2")
        print(f"Status after patch_2: {status_after_patch2}")

        # Show git diff stats
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_tinydb_path)
            result = self._run_git_command(['diff', '--stat'])
            if result.returncode == 0:
                print(f"Git diff stats:\n{result.stdout}")
        finally:
            os.chdir(original_cwd)

    def test_individual_patch_application(self):
        """Test applying patches individually."""
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Test patch_1 only
        patch_1_path = self.user_changes_dir / "patch_1.patch"
        result = self.apply_patch(str(patch_1_path), temp_tinydb_path)
        self.assertEqual(result.returncode, 0, "patch_1 should apply cleanly")

        # Verify changes
        self.assertTrue(self.has_uncommitted_changes(temp_tinydb_path),
                       "Should have uncommitted changes after patch_1")

    def test_patch_file_existence(self):
        """Test that all required patch files exist."""
        required_patches = ["patch_1.patch", "patch_2.patch", "ai_changes.patch"]

        for patch_name in required_patches:
            patch_path = self.user_changes_dir / patch_name
            self.assertTrue(patch_path.exists(), f"Required patch should exist: {patch_name}")
            self.assertGreater(patch_path.stat().st_size, 0, f"Patch file should not be empty: {patch_name}")

    def test_repository_state_isolation(self):
        """Test that changes in one test don't affect another."""
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Make some changes
        patch_1_path = self.user_changes_dir / "patch_1.patch"
        self.apply_patch(str(patch_1_path), temp_tinydb_path)

        # Verify changes exist
        self.assertTrue(self.has_uncommitted_changes(temp_tinydb_path))

        # Changes will be automatically cleaned up with the temp directory

    def apply_patch(self, patch_file: str, repo_path: str):
        """Apply a patch file to a repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = self._run_git_command(['apply', patch_file])
            return result
        finally:
            os.chdir(original_cwd)

    def get_git_status(self, repo_path: str) -> str:
        """Get git status for a repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = self._run_git_command(['status', '--porcelain'])
            return result.stdout.strip() if result.returncode == 0 else ""
        finally:
            os.chdir(original_cwd)

    def has_uncommitted_changes(self, repo_path: str) -> bool:
        """Check if repository has uncommitted changes."""
        return bool(self.get_git_status(repo_path))

    def get_commit_count(self, repo_path: str, ref: str = 'HEAD') -> int:
        """Get number of commits in repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = self._run_git_command(['rev-list', '--count', ref])
            return int(result.stdout.strip()) if result.returncode == 0 else 0
        finally:
            os.chdir(original_cwd)

    def get_recent_commits(self, repo_path: str, count: int = 5) -> str:
        """Get recent commit messages."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = self._run_git_command(['log', '--oneline', f'-n{count}'])
            return result.stdout.strip() if result.returncode == 0 else ""
        finally:
            os.chdir(original_cwd)

    def _run_git_command(self, args: list):
        """Run a git command in the current directory."""
        cmd = ['git'] + args
        return self._run_command(cmd)

    def _run_command(self, cmd: list):
        """Run a shell command."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result


class RepositoryStateTest(RepoTestCaseWithDebug):
    """Test repository state management."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        super().setUpClass()
        cls.tinydb_dir = TINYDB_DIR
        cls.repo_paths = [str(cls.tinydb_dir)]

    def test_clean_state_between_tests_1(self):
        """First test that modifies repository state."""
        temp_tinydb_path = Path(self.get_temp_repo_path(str(self.tinydb_dir)))

        # Repository should start clean
        initial_status = self.get_git_status(str(temp_tinydb_path))
        self.assertEqual(initial_status, "", "Repository should start clean")

        # Make some changes by creating a file
        test_file = temp_tinydb_path / "test_file_1.txt"
        test_file.write_text("Test content 1")

        # Verify changes exist
        self.assertTrue(self.has_uncommitted_changes(str(temp_tinydb_path)))

    def test_clean_state_between_tests_2(self):
        """Second test that should start with clean repository."""
        temp_tinydb_path = Path(self.get_temp_repo_path(str(self.tinydb_dir)))

        # Repository should be clean (each test gets a fresh copy)
        initial_status = self.get_git_status(str(temp_tinydb_path))
        self.assertEqual(initial_status, "", "Repository should start clean for each test")

        # Verify test file from previous test doesn't exist (fresh copy)
        test_file = temp_tinydb_path / "test_file_1.txt"
        self.assertFalse(test_file.exists(), "File from previous test should not exist in fresh copy")

        # Make different changes
        test_file_2 = temp_tinydb_path / "test_file_2.txt"
        test_file_2.write_text("Test content 2")

        # Verify changes exist
        self.assertTrue(self.has_uncommitted_changes(str(temp_tinydb_path)))

    def get_git_status(self, repo_path: str) -> str:
        """Get git status for a repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = subprocess.run(['git', 'status', '--porcelain'],
                                   capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else ""
        finally:
            os.chdir(original_cwd)

    def has_uncommitted_changes(self, repo_path: str) -> bool:
        """Check if repository has uncommitted changes."""
        return bool(self.get_git_status(repo_path))


if __name__ == "__main__":
    # Configure test runner
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(SimpleGitOperationsTest))
    suite.addTests(loader.loadTestsFromTestCase(RepositoryStateTest))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)