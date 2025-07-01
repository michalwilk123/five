import os
import shutil
import tempfile
import unittest

from tqdm import tqdm

from indexer.files import (
    FileOperation,
    get_file_hashes,
    get_merkle_diff,
    get_merkle_hashes,
)


class FileChangeDetectionTestCase(unittest.TestCase):
    """Test cases for file change detection functions."""

    def setUp(self):
        """Set up test using an existing test repository."""
        self.project_path = "test_repositories/tinydb"

    def test_get_file_hashes_returns_dict(self):
        """Test that get_file_hashes returns a dictionary of file paths to hashes."""
        file_hashes = get_file_hashes(self.project_path)

        self.assertIsInstance(file_hashes, dict)
        self.assertGreater(len(file_hashes), 0)

        for file_path, file_hash in file_hashes.items():
            self.assertIsInstance(file_path, str)
            self.assertIsInstance(file_hash, str)
            self.assertTrue(file_path.endswith((".py", ".js", ".ts", ".tsx", ".jsx")))
            self.assertEqual(len(file_hash), 32)  # MD5 hash length

    def test_get_merkle_hashes_returns_dict(self):
        """Test that get_merkle_hashes returns a dictionary of directory paths to hashes."""
        file_hashes = get_file_hashes(self.project_path)
        merkle_hashes = get_merkle_hashes(file_hashes)

        self.assertIsInstance(merkle_hashes, dict)
        self.assertGreater(len(merkle_hashes), 0)

        for dir_path, merkle_hash in merkle_hashes.items():
            self.assertIsInstance(dir_path, str)
            self.assertIsInstance(merkle_hash, str)
            self.assertEqual(len(merkle_hash), 32)  # MD5 hash length

    def test_get_merkle_diff_no_changes(self):
        """Test that get_merkle_diff returns empty dict when no files changed."""
        file_hashes = get_file_hashes(self.project_path)
        merkle_hashes = get_merkle_hashes(file_hashes)

        changes = get_merkle_diff(merkle_hashes, merkle_hashes, file_hashes, file_hashes)

        self.assertIsInstance(changes, dict)
        self.assertEqual(len(changes), 0)

    def test_get_merkle_diff_added_files(self):
        """Test that get_merkle_diff detects added files."""
        file_hashes = get_file_hashes(self.project_path)
        merkle_hashes = get_merkle_hashes(file_hashes)

        # Simulate adding a new file
        new_file_hashes = file_hashes.copy()
        new_file_hashes["new_file.py"] = "d41d8cd98f00b204e9800998ecf8427e"
        new_merkle_hashes = get_merkle_hashes(new_file_hashes)

        changes = get_merkle_diff(
            merkle_hashes, new_merkle_hashes, file_hashes, new_file_hashes
        )

        self.assertIn("new_file.py", changes)
        self.assertEqual(changes["new_file.py"], FileOperation.ADDED)

    def test_get_merkle_diff_modified_files(self):
        """Test that get_merkle_diff detects modified files."""
        file_hashes = get_file_hashes(self.project_path)
        merkle_hashes = get_merkle_hashes(file_hashes)

        # Simulate modifying a file
        new_file_hashes = file_hashes.copy()
        if new_file_hashes:
            first_file = list(new_file_hashes.keys())[0]
            new_file_hashes[first_file] = "d41d8cd98f00b204e9800998ecf8427e"
            new_merkle_hashes = get_merkle_hashes(new_file_hashes)

            changes = get_merkle_diff(
                merkle_hashes, new_merkle_hashes, file_hashes, new_file_hashes
            )

            self.assertIn(first_file, changes)
            self.assertEqual(changes[first_file], FileOperation.MODIFIED)

    def test_get_merkle_diff_deleted_files(self):
        """Test that get_merkle_diff detects deleted files."""
        file_hashes = get_file_hashes(self.project_path)
        merkle_hashes = get_merkle_hashes(file_hashes)

        # Simulate deleting a file
        new_file_hashes = file_hashes.copy()
        if new_file_hashes:
            first_file = list(new_file_hashes.keys())[0]
            del new_file_hashes[first_file]
            new_merkle_hashes = get_merkle_hashes(new_file_hashes)

            changes = get_merkle_diff(
                merkle_hashes, new_merkle_hashes, file_hashes, new_file_hashes
            )

            self.assertIn(first_file, changes)
            self.assertEqual(changes[first_file], FileOperation.DELETED)


class AllRepositoriesFileChangeTestCase(unittest.TestCase):
    """Test file change detection on all test repositories."""

    def test_all_repositories_file_hashes(self):
        """Test that get_file_hashes works on all test repositories."""
        test_repositories = [
            "test_repositories/tinydb",
            "test_repositories/pre-commit",
            "test_repositories/babi",
            "test_repositories/flask",
        ]

        for repo_path in test_repositories:
            with self.subTest(repository=repo_path):
                self.assertTrue(
                    os.path.exists(repo_path), f"Repository {repo_path} does not exist"
                )

                file_hashes = get_file_hashes(repo_path)
                self.assertIsInstance(file_hashes, dict)

                # Test merkle hashes
                merkle_hashes = get_merkle_hashes(file_hashes)
                self.assertIsInstance(merkle_hashes, dict)
                self.assertGreater(len(merkle_hashes), 0)

    def test_all_repositories_merkle_diff_consistency(self):
        """Test that merkle diff is consistent across all repositories."""
        test_repositories = [
            "test_repositories/tinydb",
            "test_repositories/pre-commit",
            "test_repositories/babi",
            "test_repositories/flask",
        ]

        for repo_path in tqdm(test_repositories, desc="Testing repositories"):
            with self.subTest(repository=repo_path):
                self.assertTrue(
                    os.path.exists(repo_path), f"Repository {repo_path} does not exist"
                )

                file_hashes = get_file_hashes(repo_path)
                merkle_hashes = get_merkle_hashes(file_hashes)

                # No changes should be detected when comparing same state
                changes = get_merkle_diff(
                    merkle_hashes, merkle_hashes, file_hashes, file_hashes
                )
                self.assertEqual(len(changes), 0)
