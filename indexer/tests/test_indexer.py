import os
import unittest

from indexer.files import filter_unignored_files, get_project_files

# Constants for test paths
TEST_REPOSITORIES_PATH = "test_repositories"


class TestIndexer(unittest.TestCase):
    def test_filter_unignored_files_babi(self):
        """Test filter_unignored_files with babi repository .gitignore rules"""
        # Get the path to the babi test repo
        babi_repo_path = os.path.join(TEST_REPOSITORIES_PATH, "babi")

        # Test files that should be ignored based on babi's .gitignore
        test_files = [
            "babi.egg-info",  # *.egg-info
            "some_file.pyc",  # *.pyc
            ".coverage",  # /.coverage
            ".coverage.123",  # /.coverage.*
            ".tox",  # /.tox
            "build",  # /build
            "dist",  # /dist
            "babi/babi.py",  # Should NOT be ignored
            "README.md",  # Should NOT be ignored
            "setup.py",  # Should NOT be ignored
        ]

        # Filter the files
        non_ignored = filter_unignored_files(babi_repo_path, test_files)

        # Files that should NOT be ignored
        expected_non_ignored = ["babi/babi.py", "README.md", "setup.py"]

        self.assertEqual(set(non_ignored), set(expected_non_ignored))

    def test_filter_unignored_files_flask(self):
        """Test filter_unignored_files with flask repository .gitignore rules"""
        # Get the path to the flask test repo
        flask_repo_path = os.path.join(TEST_REPOSITORIES_PATH, "flask")

        # Test files that should be ignored based on flask's .gitignore
        test_files = [
            ".idea/settings.xml",  # .idea/
            ".vscode/settings.json",  # .vscode/
            "__pycache__/file.py",  # __pycache__/
            "dist/flask.whl",  # dist/
            ".coverage",  # .coverage*
            ".coverage.123",  # .coverage*
            "htmlcov/index.html",  # htmlcov/
            ".tox/py39",  # .tox/
            "docs/_build/index.html",  # docs/_build/
            "src/flask/__init__.py",  # Should NOT be ignored
            "README.md",  # Should NOT be ignored
            "pyproject.toml",  # Should NOT be ignored
        ]

        # Filter the files
        non_ignored = filter_unignored_files(flask_repo_path, test_files)

        # Files that should NOT be ignored
        expected_non_ignored = ["src/flask/__init__.py", "README.md", "pyproject.toml"]

        self.assertEqual(set(non_ignored), set(expected_non_ignored))

    def test_filter_unignored_files_pre_commit(self):
        """Test filter_unignored_files with pre-commit repository .gitignore rules"""
        # Get the path to the pre-commit test repo
        pre_commit_repo_path = os.path.join(TEST_REPOSITORIES_PATH, "pre-commit")

        # Test files that should be ignored based on pre-commit's .gitignore
        test_files = [
            "pre_commit.egg-info",  # *.egg-info
            "file.pyc",  # *.py[co]
            "file.pyo",  # *.py[co]
            ".coverage",  # /.coverage
            ".tox",  # /.tox
            "dist/pre_commit.whl",  # /dist
            ".vscode/settings.json",  # .vscode/
            "pre_commit/__init__.py",  # Should NOT be ignored
            "README.md",  # Should NOT be ignored
            "setup.py",  # Should NOT be ignored
        ]

        # Filter the files
        non_ignored = filter_unignored_files(pre_commit_repo_path, test_files)

        # Files that should NOT be ignored
        expected_non_ignored = ["pre_commit/__init__.py", "README.md", "setup.py"]

        self.assertEqual(set(non_ignored), set(expected_non_ignored))

    def test_filter_unignored_files_empty_list(self):
        """Test filter_unignored_files with empty file list"""
        babi_repo_path = os.path.join(TEST_REPOSITORIES_PATH, "babi")
        result = filter_unignored_files(babi_repo_path, [])
        self.assertEqual(result, [])

    def test_filter_unignored_files_all_ignored(self):
        """Test filter_unignored_files when all files are ignored"""
        babi_repo_path = os.path.join(TEST_REPOSITORIES_PATH, "babi")
        test_files = [
            "babi.egg-info",
            "some_file.pyc",
            ".coverage",
            ".tox",
            "build",
            "dist",
        ]
        result = filter_unignored_files(babi_repo_path, test_files)
        self.assertEqual(result, [])

    def test_get_project_files_babi(self):
        """Test get_project_files with babi repository"""
        babi_repo_path = os.path.join(TEST_REPOSITORIES_PATH, "babi")
        files = get_project_files(babi_repo_path)

        # Should return a list of files
        self.assertIsInstance(files, list)

        # Should contain some expected files
        expected_files = ["README.md", "setup.py", "babi/__init__.py"]
        for expected_file in expected_files:
            self.assertIn(expected_file, files)

        # Should not contain ignored files
        ignored_files = ["babi.egg-info", "*.pyc", ".coverage", ".tox"]
        for ignored_file in ignored_files:
            self.assertNotIn(ignored_file, files)

    def test_get_project_files_non_git_directory(self):
        """Test get_project_files with a non-git directory"""
        # Use a temporary directory that's not a git repo
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            result = get_project_files(temp_dir)
            self.assertEqual(result, [])
