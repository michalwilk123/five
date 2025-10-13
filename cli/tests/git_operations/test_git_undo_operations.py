"""
Test git operations for undo functionality.
Tests only the git utility functions in git_utils.py without touching CLI or high-level logic.
"""

import unittest
from pathlib import Path
from tests.git_operations.git_repo_test_case import FiveGitRepoTestCase
from five_cli.vcs.git_utils import GitRepo


class GitUndoOperationsTest(FiveGitRepoTestCase):
    """Test git utility functions for undo operations."""

    def test_rebase_drop_commit_removes_from_history(self):
        """Test that rebase_drop_commit actually removes a commit from git history."""
        print("\n=== Testing rebase_drop_commit removes commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        print(f"Initial commit: {initial_commit[:8]}")

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Use hardcoded commits from TinyDB history
        # 3236d2c docs: fix broken code example (to drop) - only docs/extend.rst
        # 1138fab docs: fix broken link (should remain after) - only README.rst
        # f3caf6a infra(ci): test with Python 3.12 (should remain before)
        commit_to_drop = "3236d2cb6852d4781518066c73bc9d6172f596e4"
        commit_after = "1138fab13532e64b745e5c003fa0171ec6e7663a"
        commit_before = "f3caf6a6c9bf6bb585532af357d2294ce81ae9bd"

        count_before_drop = self.get_commit_count(git_dir, temp_tinydb_path)
        print(f"Commit count before drop: {count_before_drop}")

        commits_before = self.get_all_commit_hashes(git_dir, temp_tinydb_path)
        print(f"Commits before drop (first 5): {[c[:8] for c in commits_before[:5]]}")
        self.assertIn(commit_to_drop, commits_before, "Commit to drop should exist before dropping")

        print(f"Dropping commit: {commit_to_drop[:8]}")
        repo.rebase_drop_commit(commit_to_drop)

        count_after_drop = self.get_commit_count(git_dir, temp_tinydb_path)
        print(f"Commit count after drop: {count_after_drop}")
        self.assertEqual(count_after_drop, count_before_drop - 1, "Commit count should decrease by 1")

        commits_after = self.get_all_commit_hashes(git_dir, temp_tinydb_path)
        print(f"Commits after drop (first 5): {[c[:8] for c in commits_after[:5]]}")

        self.assertNotIn(commit_to_drop, commits_after, "Dropped commit should not be in history")
        self.assertIn(commit_before, commits_after, "Commit before should still exist")

        print("✓ Commit successfully removed from history")

    def test_rebase_drop_commit_preserves_files(self):
        """Test that dropping a commit removes only that commit's changes but preserves others."""
        print("\n=== Testing rebase_drop_commit preserves other files ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Drop commit 1138fab "docs: fix broken link" - only README.rst
        # This should remove changes to README.rst but keep other files
        commit_to_drop = "1138fab13532e64b745e5c003fa0171ec6e7663a"

        # Check the file exists before drop
        readme = Path(temp_tinydb_path) / "README.rst"
        self.assertTrue(readme.exists(), "README.rst should exist")

        # Get the content before dropping
        content_before = readme.read_text()

        repo.rebase_drop_commit(commit_to_drop)

        # File should still exist but content should be reverted
        self.assertTrue(readme.exists(), "README.rst should still exist after drop")
        content_after = readme.read_text()

        # Content should be different (the dropped commit's changes should be reverted)
        self.assertNotEqual(content_before, content_after, "File content should be reverted")

        print("✓ File changes correctly reverted")

    def test_get_commit_diff_with_hardcoded_hash(self):
        """Test get_commit_diff works with a commit from TinyDB history."""
        print("\n=== Testing get_commit_diff with hardcoded hash ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Get the most recent commits
        all_commits = self.get_all_commit_hashes(git_dir, temp_tinydb_path)
        if len(all_commits) < 2:
            self.skipTest("Not enough commits in TinyDB repo for this test")

        # Use the second commit from HEAD (skip the HEAD commit as it might be our test branch creation)
        test_commit = all_commits[1]
        print(f"Testing with commit: {test_commit[:8]}")

        diff = repo.get_commit_diff(test_commit)
        self.assertIsNotNone(diff, "Should get commit diff")
        self.assertGreater(len(diff), 0, "Diff should not be empty")
        print(f"Diff size: {len(diff)} bytes")
        print(f"Diff preview: {diff[:200]}...")

        print("✓ get_commit_diff works correctly with hardcoded hash")

    def test_rebase_drop_on_nonexistent_commit_fails(self):
        """Test that rebase_drop_commit fails gracefully on invalid commit."""
        print("\n=== Testing rebase_drop_commit with invalid commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        fake_commit_hash = "0000000000000000000000000000000000000000"

        with self.assertRaises(Exception, msg="Should raise exception for invalid commit"):
            repo.rebase_drop_commit(fake_commit_hash)

        print("✓ Correctly fails on invalid commit")

    def test_drop_oldest_accessible_commit(self):
        """Test dropping one of the oldest commits in the history."""
        print("\n=== Testing drop oldest accessible commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Get all commits and try to drop one near the end
        all_commits = self.get_all_commit_hashes(git_dir, temp_tinydb_path)

        # Skip if not enough commits
        if len(all_commits) < 10:
            self.skipTest("Not enough commits in TinyDB repo")

        # Drop a commit from deeper in history (10th from HEAD)
        commit_to_drop = all_commits[9]

        count_before = self.get_commit_count(git_dir, temp_tinydb_path)
        print(f"Dropping commit {commit_to_drop[:8]} (10th from HEAD)")

        repo.rebase_drop_commit(commit_to_drop)

        count_after = self.get_commit_count(git_dir, temp_tinydb_path)
        self.assertEqual(count_after, count_before - 1, "Should have one less commit")

        commits_after = self.get_all_commit_hashes(git_dir, temp_tinydb_path)
        self.assertNotIn(commit_to_drop, commits_after, "Dropped commit should not exist")

        print("✓ Old commit successfully dropped")

    def test_drop_recent_commit(self):
        """Test dropping a recent commit from TinyDB history."""
        print("\n=== Testing drop recent commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())

        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)
        repo = GitRepo(git_dir, temp_tinydb_path)

        # Drop commit 3dc6a95 "docs: mention multithreading issues with flask" - only docs/intro.rst
        commit_to_drop = "3dc6a952ef8700706909bf60a1b15cf21af47608"

        count_before = self.get_commit_count(git_dir, temp_tinydb_path)
        print(f"Dropping commit {commit_to_drop[:8]}")

        repo.rebase_drop_commit(commit_to_drop)

        count_after = self.get_commit_count(git_dir, temp_tinydb_path)
        self.assertEqual(count_after, count_before - 1, "Should have one less commit")

        commits_after = self.get_all_commit_hashes(git_dir, temp_tinydb_path)
        self.assertNotIn(commit_to_drop, commits_after, "Dropped commit should not exist")

        print("✓ Recent commit successfully dropped")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(GitUndoOperationsTest))

    runner = unittest.TextTestRunner(verbosity=2, buffer=False)
    result = runner.run(suite)

    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")

    exit(0 if result.wasSuccessful() else 1)
