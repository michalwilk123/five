"""
Test case for Five CLI undo functionality.
Tests that undo command correctly removes commits from git history.
"""

import unittest
import os
import json
import subprocess
from pathlib import Path
from click.testing import CliRunner
from tests.repo_test_case import RepoTestCaseWithDebug
from tests.test_paths import SYSTEST_DIR, TINYDB_DIR, USER_CHANGES_DIR
from five_cli.cli.app import cli


class FiveUndoFunctionalityTest(RepoTestCaseWithDebug):
    """Test undo command removes commits from git history correctly."""

    TASK_JSON_1 = {
        "referred_by": [],
        "conversation": {
            "user_prompt": "Add feature A",
            "messages": [
                {
                    "role": "user",
                    "content": "Add feature A",
                    "arguments": None,
                    "results": None,
                    "type": "text"
                }
            ],
            "temperature": 0.7,
            "model_name": "claude-3-sonnet"
        }
    }

    TASK_JSON_2 = {
        "referred_by": [],
        "conversation": {
            "user_prompt": "Add feature B",
            "messages": [
                {
                    "role": "user",
                    "content": "Add feature B",
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
        cls.systest_dir = SYSTEST_DIR
        cls.tinydb_dir = TINYDB_DIR
        cls.user_changes_dir = USER_CHANGES_DIR
        cls.repo_paths = [str(cls.tinydb_dir)]

        cls.PATCH_1_PATH = cls.user_changes_dir / "patch_1.patch"
        cls.AI_CHANGES_PATH = cls.user_changes_dir / "ai_changes.patch"

    def five_command(self, subcommand, project_path=None, extra_args=None):
        """Run a five CLI command using Click's CliRunner."""
        runner = CliRunner()
        args = ["project", subcommand]
        if project_path:
            args.extend(["--project-path", str(project_path)])
        if extra_args:
            args.extend(extra_args)

        result = runner.invoke(cli, args, catch_exceptions=False)

        class SubprocessResult:
            def __init__(self, click_result):
                self.returncode = click_result.exit_code
                self.stdout = click_result.output
                self.stderr = ""

        return SubprocessResult(result)

    def apply_patch(self, patch_file: str, repo_path: str):
        """Apply a patch file to a repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = subprocess.run(
                ['git', 'apply', patch_file],
                capture_output=True,
                text=True,
                check=True
            )
            return result
        finally:
            os.chdir(original_cwd)

    def get_commit_count(self, repo_path: str) -> int:
        """Get number of commits in repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                capture_output=True,
                text=True,
                check=True
            )
            return int(result.stdout.strip())
        finally:
            os.chdir(original_cwd)

    def get_commit_messages(self, repo_path: str) -> list:
        """Get all commit messages from the repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = subprocess.run(
                ['git', 'log', '--format=%s', '--all'],
                capture_output=True,
                text=True,
                check=True
            )
            return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        finally:
            os.chdir(original_cwd)

    def get_commit_hashes(self, repo_path: str) -> list:
        """Get all commit hashes from the repository."""
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            result = subprocess.run(
                ['git', 'log', '--format=%H', '--all'],
                capture_output=True,
                text=True,
                check=True
            )
            return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        finally:
            os.chdir(original_cwd)

    def get_completed_tasks(self, repo_path: str) -> list:
        """Load completed tasks from .five/completed_tasks.json."""
        completed_tasks_file = Path(repo_path) / ".five" / "completed_tasks.json"
        if not completed_tasks_file.exists():
            return []
        with open(completed_tasks_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_undo_items(self, repo_path: str) -> list:
        """Load undo items from .five/undo_items.json."""
        undo_items_file = Path(repo_path) / ".five" / "undo_items.json"
        if not undo_items_file.exists():
            return []
        with open(undo_items_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_undo_removes_commit_from_history(self):
        """Test that undo removes a commit from git history."""
        print("\n=== Testing Undo Removes Commit ==")
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Step 1: Initialize five project
        print("Step 1: Initializing five project...")
        result = self.five_command("init", project_path=temp_tinydb_path)
        self.assertEqual(result.returncode, 0, "Five init should succeed")

        initial_commit_count = self.get_commit_count(temp_tinydb_path)
        print(f"Initial commit count: {initial_commit_count}")

        # Step 2: Apply patch and start conversation
        print("Step 2: Applying patch and starting conversation...")
        self.apply_patch(str(self.PATCH_1_PATH), temp_tinydb_path)
        result = self.five_command("start-conversation", project_path=temp_tinydb_path)
        self.assertEqual(result.returncode, 0, "Start conversation should succeed")

        # Step 3: Apply AI changes and stop conversation
        print("Step 3: Applying AI changes and stopping conversation...")
        self.apply_patch(str(self.AI_CHANGES_PATH), temp_tinydb_path)
        task_json_str = json.dumps(self.TASK_JSON_1)
        result = self.five_command(
            "stop-conversation",
            project_path=temp_tinydb_path,
            extra_args=["--task-json", task_json_str]
        )
        self.assertEqual(result.returncode, 0, "Stop conversation should succeed")

        after_first_task_count = self.get_commit_count(temp_tinydb_path)
        print(f"Commit count after first task: {after_first_task_count}")

        # Get commit hashes before undo
        commit_hashes_before = self.get_commit_hashes(temp_tinydb_path)
        print(f"Commit hashes before undo: {commit_hashes_before[:3]}...")

        # Get completed tasks before undo
        completed_tasks_before = self.get_completed_tasks(temp_tinydb_path)
        self.assertEqual(len(completed_tasks_before), 1, "Should have 1 completed task")
        task_id_to_undo = completed_tasks_before[0]['id']
        print(f"Task to undo: {task_id_to_undo}")

        # Step 4: Undo the last task
        print("Step 4: Undoing last task...")
        result = self.five_command("undo", project_path=temp_tinydb_path)
        self.assertEqual(result.returncode, 0, f"Undo should succeed: {result.stderr}")

        # Verify commit was removed from history
        after_undo_count = self.get_commit_count(temp_tinydb_path)
        print(f"Commit count after undo: {after_undo_count}")
        self.assertEqual(
            after_undo_count,
            after_first_task_count - 1,
            "Commit count should decrease by 1 after undo"
        )

        # Get commit hashes after undo
        commit_hashes_after = self.get_commit_hashes(temp_tinydb_path)
        print(f"Commit hashes after undo: {commit_hashes_after[:3]}...")

        # Verify the specific commit was removed
        self.assertLess(
            len(commit_hashes_after),
            len(commit_hashes_before),
            "Should have fewer commits after undo"
        )

        # Verify completed tasks was updated
        completed_tasks_after = self.get_completed_tasks(temp_tinydb_path)
        self.assertEqual(len(completed_tasks_after), 0, "Should have 0 completed tasks after undo")

        # Verify undo_items.json was created and contains the undone task
        undo_items = self.get_undo_items(temp_tinydb_path)
        self.assertEqual(len(undo_items), 1, "Should have 1 undo item")
        self.assertEqual(undo_items[0]['id'], task_id_to_undo, "Undo item should have correct ID")
        self.assertIn('changes', undo_items[0], "Undo item should contain changes field")
        self.assertIsInstance(undo_items[0]['changes'], str, "Changes should be a string (patch)")
        self.assertGreater(len(undo_items[0]['changes']), 0, "Changes should not be empty")

        print(f"Undo item patch preview: {undo_items[0]['changes'][:200]}...")

    def test_undo_specific_task_by_id(self):
        """Test that undo can remove a specific task by ID."""
        print("\n=== Testing Undo Specific Task by ID ===")
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Step 1: Initialize five project
        print("Step 1: Initializing five project...")
        result = self.five_command("init", project_path=temp_tinydb_path)
        self.assertEqual(result.returncode, 0, "Five init should succeed")

        # Step 2: Create first task
        print("Step 2: Creating first task...")
        self.apply_patch(str(self.PATCH_1_PATH), temp_tinydb_path)
        self.five_command("start-conversation", project_path=temp_tinydb_path)
        self.apply_patch(str(self.AI_CHANGES_PATH), temp_tinydb_path)
        task_json_str_1 = json.dumps(self.TASK_JSON_1)
        result = self.five_command(
            "stop-conversation",
            project_path=temp_tinydb_path,
            extra_args=["--task-json", task_json_str_1]
        )
        self.assertEqual(result.returncode, 0, "First stop conversation should succeed")

        # Step 3: Create a new file for second task
        print("Step 3: Creating second task...")
        test_file = Path(temp_tinydb_path) / "test_feature_b.txt"
        test_file.write_text("Feature B content")

        self.five_command("start-conversation", project_path=temp_tinydb_path)
        task_json_str_2 = json.dumps(self.TASK_JSON_2)
        result = self.five_command(
            "stop-conversation",
            project_path=temp_tinydb_path,
            extra_args=["--task-json", task_json_str_2]
        )
        self.assertEqual(result.returncode, 0, "Second stop conversation should succeed")

        # Verify we have 2 tasks
        completed_tasks = self.get_completed_tasks(temp_tinydb_path)
        self.assertEqual(len(completed_tasks), 2, "Should have 2 completed tasks")
        first_task_id = completed_tasks[0]['id']
        print(f"First task ID: {first_task_id}, Second task ID: {completed_tasks[1]['id']}")

        commit_count_before = self.get_commit_count(temp_tinydb_path)
        print(f"Commit count before undo: {commit_count_before}")

        # Step 4: Undo the first task (not the last one)
        print(f"Step 4: Undoing first task (ID: {first_task_id})...")
        result = self.five_command(
            "undo",
            project_path=temp_tinydb_path,
            extra_args=[str(first_task_id)]
        )
        self.assertEqual(result.returncode, 0, f"Undo should succeed: {result.stderr}")

        # Verify commit was removed
        commit_count_after = self.get_commit_count(temp_tinydb_path)
        print(f"Commit count after undo: {commit_count_after}")
        self.assertEqual(
            commit_count_after,
            commit_count_before - 1,
            "Commit count should decrease by 1"
        )

        # Verify completed tasks was updated (first task removed)
        completed_tasks_after = self.get_completed_tasks(temp_tinydb_path)
        self.assertEqual(len(completed_tasks_after), 1, "Should have 1 completed task after undo")
        self.assertNotEqual(
            completed_tasks_after[0]['id'],
            first_task_id,
            "First task should be removed"
        )

    def test_undo_creates_correct_patch(self):
        """Test that undo saves the correct patch in undo_items.json."""
        print("\n=== Testing Undo Creates Correct Patch ===")
        temp_tinydb_path = self.get_temp_repo_path(str(self.tinydb_dir))

        # Step 1: Initialize and create a task
        print("Step 1: Initializing and creating task...")
        self.five_command("init", project_path=temp_tinydb_path)
        self.apply_patch(str(self.PATCH_1_PATH), temp_tinydb_path)
        self.five_command("start-conversation", project_path=temp_tinydb_path)
        self.apply_patch(str(self.AI_CHANGES_PATH), temp_tinydb_path)
        task_json_str = json.dumps(self.TASK_JSON_1)
        self.five_command(
            "stop-conversation",
            project_path=temp_tinydb_path,
            extra_args=["--task-json", task_json_str]
        )

        # Get the commit diff before undo
        completed_tasks = self.get_completed_tasks(temp_tinydb_path)
        task_id = completed_tasks[0]['id']

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_tinydb_path)
            # Find commit by task ID
            result = subprocess.run(
                ['git', 'log', '--format=%H|%s', '--all'],
                capture_output=True,
                text=True,
                check=True
            )
            commit_hash = None
            for line in result.stdout.split('\n'):
                if f'id={task_id}' in line:
                    commit_hash = line.split('|')[0]
                    break

            self.assertIsNotNone(commit_hash, "Should find commit with task ID")

            # Get the diff for this commit
            result = subprocess.run(
                ['git', 'show', '--format=', commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            expected_patch = result.stdout
        finally:
            os.chdir(original_cwd)

        # Step 2: Undo the task
        print("Step 2: Undoing task...")
        self.five_command("undo", project_path=temp_tinydb_path)

        # Step 3: Verify the patch in undo_items.json matches
        undo_items = self.get_undo_items(temp_tinydb_path)
        self.assertEqual(len(undo_items), 1, "Should have 1 undo item")

        saved_patch = undo_items[0]['changes']
        self.assertEqual(
            saved_patch,
            expected_patch,
            "Saved patch should match the original commit diff"
        )
        print(f"Patch verification successful! Patch size: {len(saved_patch)} bytes")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(FiveUndoFunctionalityTest))

    runner = unittest.TextTestRunner(verbosity=2, buffer=False)
    result = runner.run(suite)

    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")

    exit(0 if result.wasSuccessful() else 1)
