import unittest
from pathlib import Path
from tests.git_operations.git_repo_test_case import FiveGitRepoTestCase
from five_cli.vcs.git_utils import GitRepo


class GitEditOperationsTest(FiveGitRepoTestCase):

    def test_start_interactive_rebase_at_commit(self):
        print("\n=== Testing start_interactive_rebase_at_commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())
        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Use hardcoded commit from TinyDB history
        # 3236d2c "docs: fix broken code example" - only docs/extend.rst
        target_commit = "3236d2cb6852d4781518066c73bc9d6172f596e4"

        self.assertFalse(repo.is_rebase_in_progress(), "No rebase should be in progress")

        repo.start_interactive_rebase_at_commit(target_commit)

        self.assertTrue(repo.is_rebase_in_progress(), "Rebase should be in progress")

        repo.abort_rebase()
        self.assertFalse(repo.is_rebase_in_progress(), "Rebase should be aborted")

        print("✓ start_interactive_rebase_at_commit works correctly")

    def test_reset_working_tree_changes(self):
        print("\n=== Testing reset_working_tree_changes ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())
        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Modify an existing file
        test_file = Path(temp_tinydb_path) / "README.rst"
        self.assertTrue(test_file.exists(), "README.rst should exist in TinyDB repo")
        original_content = test_file.read_text()

        # Make changes
        test_file.write_text(original_content + "\n.. Test modification")
        modified_content = test_file.read_text()
        self.assertNotEqual(original_content, modified_content, "File should be modified")

        # Reset changes
        repo.reset_working_tree_changes()

        # Verify file is restored
        restored_content = test_file.read_text()
        self.assertEqual(restored_content, original_content, "File should be restored to original")

        print("✓ reset_working_tree_changes works correctly")

    def test_amend_commit(self):
        print("\n=== Testing amend_commit ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())
        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Use hardcoded commit from TinyDB history
        # c4105cf "docs: fix changelog pull request reference" - only CHANGELOG.rst
        target_commit = "c4105cfcefb56edb1ca2f1048ed8229422ff6c32"

        repo.start_interactive_rebase_at_commit(target_commit)

        initial_count = self.get_commit_count(git_dir, temp_tinydb_path)

        # Modify a file to amend the commit
        test_file = Path(temp_tinydb_path) / "CHANGELOG.rst"
        if test_file.exists():
            content = test_file.read_text()
            test_file.write_text(content + "\n# Test amendment")

        repo.amend_commit("Test: amended commit")

        amended_count = self.get_commit_count(git_dir, temp_tinydb_path)
        self.assertEqual(amended_count, initial_count, "Commit count should not change")

        repo.abort_rebase()

        print("✓ amend_commit works correctly")

    def test_continue_rebase(self):
        print("\n=== Testing continue_rebase ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())
        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Use hardcoded commit from TinyDB history
        # b8ffbfe "docs: document Table.get" - only docs/usage.rst
        target_commit = "b8ffbfece5a4ddf382ae8db52896173511946279"

        repo.start_interactive_rebase_at_commit(target_commit)
        self.assertTrue(repo.is_rebase_in_progress(), "Rebase should be in progress")

        # Modify a file to amend the commit
        test_file = Path(temp_tinydb_path) / "docs" / "usage.rst"
        if test_file.exists():
            content = test_file.read_text()
            test_file.write_text(content + "\n.. Continue test")

        repo.amend_commit("Test: continue rebase")

        repo.continue_rebase()
        self.assertFalse(repo.is_rebase_in_progress(), "Rebase should be completed")

        print("✓ continue_rebase works correctly")

    def test_is_rebase_in_progress(self):
        print("\n=== Testing is_rebase_in_progress ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())
        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Use hardcoded commit from TinyDB history
        # ecf4448 "docs: update status of TinyMP extension" - only docs/extensions.rst
        target_commit = "ecf4448fdae98c43b886e75e360c38bbbc240851"

        self.assertFalse(repo.is_rebase_in_progress(), "No rebase should be in progress initially")

        repo.start_interactive_rebase_at_commit(target_commit)
        self.assertTrue(repo.is_rebase_in_progress(), "Rebase should be detected")

        repo.abort_rebase()
        self.assertFalse(repo.is_rebase_in_progress(), "Rebase should no longer be in progress")

        print("✓ is_rebase_in_progress works correctly")

    def test_full_edit_workflow(self):
        print("\n=== Testing full edit workflow ===")
        temp_tinydb_path = str(self.get_temp_tinydb_path())
        git_dir, initial_commit = self.setup_five_repo(temp_tinydb_path)

        repo = GitRepo(git_dir, temp_tinydb_path)

        # Use hardcoded commit from TinyDB history
        # 3dc6a95 "docs: mention multithreading issues with flask" - only docs/intro.rst
        target_commit = "3dc6a952ef8700706909bf60a1b15cf21af47608"

        initial_count = self.get_commit_count(git_dir, temp_tinydb_path)

        repo.start_interactive_rebase_at_commit(target_commit)
        self.assertTrue(repo.is_rebase_in_progress())

        repo.reset_working_tree_changes()

        # Modify an existing file
        test_file = Path(temp_tinydb_path) / "docs" / "intro.rst"
        if test_file.exists():
            content = test_file.read_text()
            test_file.write_text(content + "\n.. Workflow test modification")

        repo.amend_commit("Test: full workflow edit")

        repo.continue_rebase()
        self.assertFalse(repo.is_rebase_in_progress())

        final_count = self.get_commit_count(git_dir, temp_tinydb_path)
        self.assertEqual(final_count, initial_count, "Commit count should remain the same")

        print("✓ Full edit workflow completed successfully")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(GitEditOperationsTest))

    runner = unittest.TextTestRunner(verbosity=2, buffer=False)
    result = runner.run(suite)

    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")

    exit(0 if result.wasSuccessful() else 1)
