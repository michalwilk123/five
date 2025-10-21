from __future__ import annotations

from pathlib import Path
import subprocess

from five.managers.base import BaseManager
from five.utils import LogFunction


class GitCommandChain:
    """Fluent interface for sequencing git operations."""

    def __init__(self, manager: GitManager):
        self._manager = manager
        self._last_result: subprocess.CompletedProcess | None = None

    def _run(self, args: list[str]) -> 'GitCommandChain':
        self._last_result = self._manager.run(args)
        return self

    def stage_all(self) -> GitCommandChain:
        self._manager._log('Staging all changes')
        self._run(['add', '-A'])
        self._manager._log('Unstaging state file')
        try:
            self._run(['reset', 'HEAD', 'state'])
        except Exception:
            pass
        return self

    def add_all(self) -> 'GitCommandChain':
        """Alias for stage_all to keep terminology flexible."""
        return self.stage_all()

    def commit(self, message: str) -> 'GitCommandChain':
        self._manager._log(f'Creating commit with message: {message}')
        return self._run(['commit', '-m', message])

    def initial_commit(self, message: str) -> 'GitCommandChain':
        self._manager._log('Creating initial commit')
        self._run(['add', '.'])
        return self._run(['commit', '-m', message, '--allow-empty'])

    def capture(self, args: list[str]) -> 'GitCommandChain':
        return self._run(args)

    def get_result(self) -> subprocess.CompletedProcess | None:
        return self._last_result

    def output(self) -> str:
        if self._last_result and self._last_result.stdout:
            return self._last_result.stdout.strip()
        return ''


class GitManager(BaseManager):
    def __init__(
        self,
        logger: LogFunction,
        git_path: Path,
        work_tree: Path,
    ):
        super().__init__(logger)
        self.git_path = git_path
        self.work_tree = work_tree

    def run(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = ['git', f'--git-dir={self.git_path}', f'--work-tree={self.work_tree}', *args]
        self._log(f'Running git command: {" ".join(cmd)}')
        try:
            return subprocess.run(cmd, capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = (
                f'Git command failed: {" ".join(cmd)}\nstdout: {e.stdout}\nstderr: {e.stderr}'
            )
            raise subprocess.CalledProcessError(
                e.returncode, e.cmd, e.stdout, e.stderr
            ) from Exception(error_msg)

    def chain(self) -> GitCommandChain:
        return GitCommandChain(self)

    def stage_all_changes(self):
        self.chain().stage_all()

    def get_status(self) -> dict[str, list[str] | bool]:
        status_result = self.run(['status', '--porcelain'])
        lines = status_result.stdout.strip().splitlines()

        untracked_files: list[str] = []
        modified_files: list[str] = []
        staged_files: list[str] = []

        for line in lines:
            if len(line) < 3:
                continue
            status_code = line[:2]
            file_path = line[2:].lstrip()

            if status_code[0] not in {' ', '?'}:
                staged_files.append(file_path)
            if status_code[1] != ' ':
                modified_files.append(file_path)
            if status_code == '??':
                untracked_files.append(file_path)

        is_dirty = bool(untracked_files or modified_files or staged_files)

        return {
            'untracked_files': untracked_files,
            'modified_files': modified_files,
            'staged_files': staged_files,
            'is_dirty': is_dirty,
        }

    def create_commit(self, message: str) -> str:
        chain = self.chain()
        commit_hash = chain.stage_all().commit(message).capture(['rev-parse', 'HEAD']).output()
        self._log(f'Created commit {commit_hash}')
        return commit_hash

    def create_initial_commit(self, message: str):
        self.chain().initial_commit(message)

    def set_config(self, key: str, value: str):
        self._log(f'Setting git config {key} to {value}')
        self.run(['config', key, value])

    def get_diff(self, commit_hash: str) -> str:
        self._log(f'Getting diff for commit {commit_hash}')
        result = self.run(['show', commit_hash])
        return result.stdout

    def get_all_commit_hashes(self) -> set[str]:
        self._log('Getting all commit hashes')
        result = self.run(['log', '--all', '--format=%H'])
        lines = result.stdout.strip().splitlines()
        return {line.strip() for line in lines if line.strip()}

    def get_current_head(self) -> str:
        self._log('Getting current HEAD')
        result = self.run(['rev-parse', 'HEAD'])
        return result.stdout.strip()

    def revert_commit(self, commit_hash: str) -> str:
        self._log(f'Reverting commit {commit_hash}')
        try:
            self.run(['revert', commit_hash, '--no-commit'])
        except subprocess.CalledProcessError:
            self._log('Revert failed, likely due to conflicts. Resolving database conflicts.')

        # Always reset the database to HEAD to avoid conflicts and maintain metadata integrity
        self._log('Resetting database file to current HEAD')
        try:
            self.run(['reset', 'HEAD', 'data.db'])
            self.run(['checkout', 'data.db'])
        except subprocess.CalledProcessError:
            # If reset fails, the database might not be in the index, which is fine
            pass

        self._log('Committing revert changes')
        self.run(['commit', '--no-edit', '-m', f'Revert "{commit_hash}"'])
        revert_hash = self.get_current_head()
        self._log(f'Created revert commit {revert_hash}')
        return revert_hash


def init_git_repo_in_dir(work_tree: Path, git_path: Path):
    cmd = ['git', f'--git-dir={git_path}', f'--work-tree={work_tree}', 'init']
    subprocess.run(cmd, check=True, capture_output=True)


def get_git_config_value(key: str) -> str:
    result = subprocess.run(
        ['git', 'config', key],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
