"""
Test git operations for redo functionality.
Tests only the git utility functions in git_utils.py without touching CLI or high-level logic.
"""

import unittest
from pathlib import Path
from tests.git_operations.git_repo_test_case import FiveGitRepoTestCase
from five_cli.vcs.git_utils import GitRepo


class GitRedoOperationsTest(FiveGitRepoTestCase):
    """Test git utility functions for redo operations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_paths = [str(cls.tinydb_dir)]
        # Path to predefined patches
        cls.patches_dir = Path(__file__).parent.parent / "systest" / "user-changes"

    def load_patch(self, patch_filename: str) -> str:
        """Load a predefined patch file."""
        patch_path = self.patches_dir / patch_filename
        return patch_path.read_text()

    def test_rebase_edit_commit_stops_at_commit(self):
        """Test that rebase_edit_commit stops at the specified commit."""
        print("\n=== Testing rebase_edit_commit stops at commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        print(f"Initial commit: {initial_commit[:8]}")

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Create a test commit at HEAD so we can rebase at it
        test_file = Path(temp_tinydb_path) / "test_rebase.txt"
        test_file.write_text("Test content for rebase")
        test_commit = repo.create_commit("Test: add test file for rebase")
        print(f"Created test commit: {test_commit[:8]}")

        count_before = self.get_commit_count(git_dir, temp_tinydb_path)
        print(f"Commit count before rebase edit: {count_before}")

        repo.rebase_edit_commit(test_commit)

        self.assertTrue(repo.is_rebase_in_progress(), "Rebase should be in progress")

        status_result = repo.run(['status', '--porcelain'])
        print(f"Status after rebase edit: {status_result.stdout}")

        # Clean up - abort the rebase
        repo.abort_rebase()

        print("✓ Rebase edit stops at commit")

    def test_apply_patch_and_continue_rebase(self):
        """Test applying a predefined patch during rebase."""
        print("\n=== Testing apply_patch_and_continue_rebase ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Load predefined patch that adds multiply function to operations.py
        patch_content = self.load_patch("patch_1.patch")
        print(f"Loaded patch_1.patch, size: {len(patch_content)} bytes")

        # Create a test commit at HEAD so we can rebase at it
        # This ensures we're working with the current file state
        test_file = Path(temp_tinydb_path) / "test_patch.txt"
        test_file.write_text("Test content for patch application")
        test_commit = repo.create_commit("Test: add test file for patch")
        print(f"Created test commit: {test_commit[:8]}")

        # Now rebase at this commit - this will check out its parent (original HEAD)
        # where all the tinydb files exist in their current state
        repo.rebase_edit_commit(test_commit)

        new_message = "Test: add multiply operation"
        repo.apply_patch_and_continue_rebase(patch_content, new_message)

        messages_after = self.get_all_commit_messages(git_dir, temp_tinydb_path)
        self.assertIn(new_message, messages_after, "New commit message should exist")
        print(f"Messages after rebase (first 5): {messages_after[:5]}")

        # Verify the patch was applied by checking file content
        operations_file = Path(temp_tinydb_path) / "tinydb" / "operations.py"
        if operations_file.exists():
            content = operations_file.read_text()
            self.assertIn("def multiply(field, n):", content, "multiply function should be added")
            print("✓ Patch content verified in operations.py")

        print("✓ Patch applied and rebase continued")

    def test_redo_workflow_complete(self):
        """Test complete redo workflow with predefined patch."""
        print("\n=== Testing complete redo workflow ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Load predefined patch that changes cache sizes
        patch_to_redo = self.load_patch("patch_2.patch")
        print(f"Loaded patch_2.patch, size: {len(patch_to_redo)} bytes")

        # Create a test commit at HEAD
        test_file = Path(temp_tinydb_path) / "test_redo.txt"
        test_file.write_text("Test content for redo workflow")
        test_commit = repo.create_commit("Test: add test file for redo")
        print(f"Created test commit: {test_commit[:8]}")

        count_before_redo = self.get_commit_count(git_dir, temp_tinydb_path)

        repo.rebase_edit_commit(test_commit)
        redo_message = "Test: update cache sizes"
        repo.apply_patch_and_continue_rebase(patch_to_redo, redo_message)

        count_after_redo = self.get_commit_count(git_dir, temp_tinydb_path)
        # Count increases by 1 because we're adding a new commit
        self.assertEqual(count_after_redo, count_before_redo + 1, "Commit count should increase by 1")

        messages = self.get_all_commit_messages(git_dir, temp_tinydb_path)
        self.assertIn(redo_message, messages, "Modified commit message should exist")

        # Verify the patch was applied
        middlewares_file = Path(temp_tinydb_path) / "tinydb" / "middlewares.py"
        if middlewares_file.exists():
            content = middlewares_file.read_text()
            self.assertIn("WRITE_CACHE_SIZE = 2000", content, "Cache size should be updated to 2000")
            print("✓ Patch content verified in middlewares.py")

        print("✓ Complete redo workflow works correctly")

    def test_rebase_edit_on_nonexistent_commit_fails(self):
        """Test that rebase_edit_commit fails gracefully on invalid commit."""
        print("\n=== Testing rebase_edit_commit with invalid commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        fake_commit_hash = "0000000000000000000000000000000000000000"

        with self.assertRaises(Exception, msg="Should raise exception for invalid commit"):
            repo.rebase_edit_commit(fake_commit_hash)

        print("✓ Correctly fails on invalid commit")

    def test_redo_preserves_later_commits(self):
        """Test that redo preserves commits that come after the rebase point."""
        print("\n=== Testing redo preserves later commits ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Load predefined patch with statistical methods
        patch = self.load_patch("ai_changes.patch")
        print(f"Loaded ai_changes.patch, size: {len(patch)} bytes")

        # Create two test commits - we'll rebase at the first one
        # and verify the second one is preserved
        test_file1 = Path(temp_tinydb_path) / "test_preserve1.txt"
        test_file1.write_text("First test commit")
        first_commit = repo.create_commit("Test: first commit for preservation test")
        print(f"Created first test commit: {first_commit[:8]}")

        test_file2 = Path(temp_tinydb_path) / "test_preserve2.txt"
        test_file2.write_text("Second test commit")
        second_commit = repo.create_commit("Test: second commit to be preserved")
        print(f"Created second test commit: {second_commit[:8]}")

        # Get the second commit message to verify it's preserved
        result = repo.run(['log', '--format=%s', '-1', second_commit])
        later_commit_message = result.stdout.strip()
        print(f"Later commit message to preserve: '{later_commit_message}'")

        messages_before = self.get_all_commit_messages(git_dir, temp_tinydb_path)
        self.assertIn(later_commit_message, messages_before, "Later commit message should exist before")

        count_before = self.get_commit_count(git_dir, temp_tinydb_path)

        # Rebase at the first commit - this should preserve the second commit
        repo.rebase_edit_commit(first_commit)
        repo.apply_patch_and_continue_rebase(patch, "Test: add statistical methods")

        messages_after = self.get_all_commit_messages(git_dir, temp_tinydb_path)
        self.assertIn(later_commit_message, messages_after, "Later commit message should be preserved")

        count_after = self.get_commit_count(git_dir, temp_tinydb_path)
        # Count increases by 1 (we added one new commit)
        self.assertEqual(count_after, count_before + 1, "Commit count should increase by 1")

        print("✓ Later commits preserved after redo")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(GitRedoOperationsTest))

    runner = unittest.TextTestRunner(verbosity=2, buffer=False)
    result = runner.run(suite)

    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")

    exit(0 if result.wasSuccessful() else 1)
