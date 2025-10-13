"""Common base class for git operation tests."""

from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from five_cli.vcs.git_utils import GitRepo

from tests.repo_test_case import RepoTestCaseWithDebug
from tests.test_paths import TINYDB_DIR


class FiveGitRepoTestCase(RepoTestCaseWithDebug):
    """Shared helpers for git-focused test cases operating on the TinyDB repo copy."""

    repo_paths: List[str] = [str(TINYDB_DIR)]
    tinydb_dir: Path = TINYDB_DIR

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tinydb_dir = TINYDB_DIR
        cls.repo_paths = [str(TINYDB_DIR)]

    def get_temp_tinydb_path(self) -> Path:
        """Return the isolated TinyDB repository path for the current test."""
        return Path(self.get_temp_repo_path(str(self.tinydb_dir)))

    def setup_five_repo(self, project_path: str):
        """Prepare the copied TinyDB repository for git operation tests.

        This method resets the working tree, creates a dedicated test branch and
        configures a local git identity so that git commands succeed without
        relying on global configuration.
        """

        project_path = Path(project_path)
        git_dir_path = project_path / ".git"

        git_dir = str(git_dir_path)
        work_tree = str(project_path)

        repo = GitRepo(git_dir, work_tree)

        # Ensure we start from a clean state before running git operations
        repo.run(["reset", "--hard", "HEAD"])
        repo.run(["clean", "-fd"])

        # Configure a local identity for commits made during the tests
        repo.run(["config", "user.email", "five-tests@example.com"])
        repo.run(["config", "user.name", "Five CLI Tests"])

        # Work on an isolated branch to keep the original history intact while
        # also ensuring commits can be created even if the original repository
        # contains unpublished history on master. We use a deterministic prefix
        # so branches from different tests are easy to identify when debugging.
        branch_name = f"five-tests/{uuid4().hex[:8]}"
        repo.run(["checkout", "-B", branch_name])

        initial_commit_hash = repo.run(["rev-parse", "HEAD"]).stdout.strip()

        return git_dir, initial_commit_hash

    def create_test_file(self, project_path: str, filename: str, content: str):
        file_path = Path(project_path) / filename
        file_path.write_text(content)

    def get_commit_count(self, git_dir: str, project_path: str) -> int:
        repo = GitRepo(git_dir, project_path)
        result = repo.run(["rev-list", "--count", "HEAD"])
        return int(result.stdout.strip())

    def get_all_commit_hashes(self, git_dir: str, project_path: str) -> List[str]:
        repo = GitRepo(git_dir, project_path)
        result = repo.run(["log", "--format=%H", "HEAD"])
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

    def get_all_commit_messages(self, git_dir: str, project_path: str) -> List[str]:
        repo = GitRepo(git_dir, project_path)
        result = repo.run(["log", "--format=%s", "HEAD"])
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]

    def get_file_content(self, project_path: str, filename: str) -> Optional[str]:
        file_path = Path(project_path) / filename
        if not file_path.exists():
            return None
        return file_path.read_text()
