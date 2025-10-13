"""
Five CLI integration test using RepoTestCase.
Tests the complete workflow following the test case requirements from systest/test_case.py.
Rewritten to use Click's isolated filesystem approach.
"""

import unittest
import os
import sys
import json
import subprocess
from pathlib import Path
from click.testing import CliRunner
from tests.repo_test_case import RepoTestCaseWithDebug
from tests.test_paths import FIVE_CLI_DIR, SYSTEST_DIR, TINYDB_DIR, USER_CHANGES_DIR
from five_cli.cli.app import cli
from five_cli.core.project import five_status
from click.testing import CliRunner


class FiveCliIntegrationTest(RepoTestCaseWithDebug):
    """Integration test for Five CLI application with automatic repository cleanup."""

    # Task JSON for stop-conversation command with comprehensive AI prompt
    TASK_JSON = {
        "referred_by": [],
        "conversation": {
            "user_prompt": """I have a TinyDB project (a lightweight Python document database). I want you to add useful statistical and aggregation methods to the Table class to make data analysis easier for users.

Please add the following methods to the Table class in tinydb/table.py:

1. sum(field, cond=None) - Calculate sum of numeric values in a field, with optional query condition
2. avg(field, cond=None) - Calculate average of numeric values in a field, with optional query condition
3. min(field, cond=None) - Find minimum value in a field, with optional query condition
4. max(field, cond=None) - Find maximum value in a field, with optional query condition
5. distinct(field, cond=None) - Get unique values in a field, with optional query condition

Requirements:
- All methods should accept an optional cond parameter for filtering documents (like existing search and count methods)
- Handle edge cases gracefully (empty results, non-existent fields, non-numeric values for sum/avg)
- For sum/avg methods, raise ValueError if field contains non-numeric values
- For distinct method, handle complex data types like lists and dicts properly
- Follow the existing code style and patterns in the TinyDB codebase

Also write comprehensive tests for all the new methods in tests/test_tinydb.py, including:
- Basic functionality with and without conditions
- Edge cases (empty database, non-existent fields, invalid data types)
- Tests with complex data types for the distinct method

Make sure all existing tests still pass after your changes.""",
            "messages": [
                {
                    "role": "user",
                    "content": "Add statistical and aggregation methods to TinyDB Table class",
                    "arguments": None,
                    "results": None,
                    "type": "text"
                }
            ],
            "temperature": 0.7,
            "model_name": "claude-3-sonnet"
        }
    }

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        super().setUpClass()

        # Define paths (now in tests directory)
        cls.systest_dir = SYSTEST_DIR
        cls.tinydb_dir = TINYDB_DIR
        cls.user_changes_dir = USER_CHANGES_DIR
        cls.five_cli_dir = FIVE_CLI_DIR
        cls.repo_paths = [str(cls.tinydb_dir)]

        # Create constants for patch paths
        cls.PATCH_1_PATH = cls.user_changes_dir / "patch_1.patch"
        cls.PATCH_2_PATH = cls.user_changes_dir / "patch_2.patch"
        cls.AI_CHANGES_PATH = cls.user_changes_dir / "ai_changes.patch"

        sys.path.insert(0, str(cls.five_cli_dir.parent))
        required_patches = ["patch_1.patch", "patch_2.patch", "ai_changes.patch"]

        assert all(path.exists() for path in [cls.tinydb_dir, cls.user_changes_dir, cls.five_cli_dir])
        assert all(patch_path.exists() for patch_path in [cls.user_changes_dir / patch for patch in required_patches])

    def five_command(self, subcommand, project_path=None, extra_args=None):
        """Run a five CLI command using Click's CliRunner."""

        runner = CliRunner()

        # Build command args
        args = ["project", subcommand]
        if project_path:
            args.extend(["--project-path", str(project_path)])
        if extra_args:
            args.extend(extra_args)

        # Run command with Click's test runner
        result = runner.invoke(cli, args, catch_exceptions=False)

        # Convert Click result to subprocess-like result for compatibility
        class SubprocessResult:
            def __init__(self, click_result):
                self.returncode = click_result.exit_code
                self.stdout = click_result.output
                self.stderr = ""  # Click doesn't separate stderr in testing

        return SubprocessResult(result)

    def apply_patch_and_verify(self, patch_path: Path, repo_path: str, description: str = None):
        """Apply a patch file to a repository and verify it was successful."""
        desc = description or f"patch {patch_path.name}"
        result = self.apply_patch(str(patch_path), repo_path)
        self.assertEqual(result.returncode, 0, f"{desc} should apply successfully: {result.stderr}")

        # Verify changes were made
        self.assertTrue(self.has_uncommitted_changes(repo_path),
                       f"Should have uncommitted changes after applying {desc}")
        return result

    def get_five_status(self, repo_path: str):
        """Get five status information for a repository."""
        try:
            # five_status requires: five_config_path, project_path, max_count
            five_config_path = Path(repo_path) / ".five"
            project_path = Path(repo_path)
            max_count = 10  # Default reasonable limit

            # Check if .five directory exists
            if not five_config_path.exists():
                return None

            return five_status(five_config_path, project_path, max_count)
        except Exception as e:
            # If five_status fails, return None
            print(f"Warning: Could not get five_status: {e}")
            return None

    def test_init_five_project(self):
        """Test Step 1: Initialize five project in tinydb repo."""
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Repository should start clean
        initial_status = self.get_git_status(temp_tinydb_path)
        self.assertEqual(initial_status, "", "Repository should start clean")

        # Initialize five project
        result = self.five_command("init", project_path=temp_tinydb_path)
        self.assertEqual(result.returncode, 0, f"Five init should succeed: {result.stderr}")

        # Check git log for commits
        recent_commits = self.get_recent_commits(temp_tinydb_path)
        self.assertTrue(bool(recent_commits), "Should have commits after init")

    
    def test_complete_workflow(self):
        """Test the complete Five CLI workflow in one test."""
        print("\n=== Testing Complete Five CLI Workflow ===")
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Step 1: Initialize five project
        print("Step 1: Initializing five project...")
        result = self.five_command("init", project_path=temp_tinydb_path)
        self.assertEqual(result.returncode, 0, "Five init should succeed")

        # Step 2: Apply change_1.patch using constants
        print("Step 2: Applying change_1.patch...")
        self.apply_patch_and_verify(self.PATCH_1_PATH, temp_tinydb_path, "patch_1")

        # Step 3: Start conversation
        print("Step 3: Starting conversation...")
        result = self.five_command("start-conversation", project_path=temp_tinydb_path)
        print(f"Start conversation result: {result.returncode}")

        # Check if patch 1 was committed with type = USER
        status = self.get_five_status(temp_tinydb_path)
        if status:
            print(f"Five status after start-conversation: {status}")
            # Check for user commit
            commit_count = self.get_commit_count(temp_tinydb_path)
            self.assertGreaterEqual(commit_count, 2, "Should have at least 2 commits (initial + user)")

        # Step 4: Apply AI changes using helper function
        print("Step 4: Applying AI changes...")
        self.apply_patch_and_verify(self.AI_CHANGES_PATH, temp_tinydb_path, "AI changes")

        # Step 5: Stop conversation
        print("Step 5: Stopping conversation...")
        task_json_str = json.dumps(self.TASK_JSON)
        result = self.five_command(
            "stop-conversation",
            project_path=temp_tinydb_path,
            extra_args=["--task-json", task_json_str]
        )
        print(f"Stop conversation result: {result.returncode}")

        # Check if AI changes were committed with type = assistant
        status = self.get_five_status(temp_tinydb_path)
        print(f"Five status after stop-conversation: {status}")
        # Check for assistant commit
        final_commit_count = self.get_commit_count(temp_tinydb_path)
        self.assertGreaterEqual(final_commit_count, 3,
                                "Should have at least 3 commits (initial + user + assistant)")

        # Step 6: Apply patch_2 using constants
        print("Step 6: Applying patch_2...")
        self.apply_patch_and_verify(self.PATCH_2_PATH, temp_tinydb_path, "patch_2")

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

    def _run_git_command(self, args: list, check: bool = True):
        """Run a git command in the current directory."""
        cmd = ['git'] + args
        return self._run_command(cmd, check=check)

    def _run_command(self, cmd: list, check: bool = True):
        """Run a shell command."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return e


class FiveCliErrorHandlingTest(RepoTestCaseWithDebug):
    """Test error handling in Five CLI integration."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        super().setUpClass()
        cls.tinydb_dir = TINYDB_DIR
        cls.five_cli_dir = FIVE_CLI_DIR
        cls.repo_paths = [str(cls.tinydb_dir)]

    def test_invalid_project_path(self):
        """Test five CLI with invalid project path."""

        runner = CliRunner()
        invalid_path = "/nonexistent/path"
        result = runner.invoke(cli, ["project", "init", "--project-path", invalid_path])
        # Should fail for nonexistent path
        self.assertNotEqual(result.exit_code, 0, "Should fail for nonexistent path")

if __name__ == "__main__":
    # Configure test runner with high verbosity
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(FiveCliIntegrationTest))
    suite.addTests(loader.loadTestsFromTestCase(FiveCliErrorHandlingTest))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=False)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")
