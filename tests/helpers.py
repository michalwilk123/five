from pathlib import Path
import sqlite3
import traceback
from typing import Iterable

from click.testing import CliRunner, Result
from pony.orm import db_session

from five.cli.main import cli
from five.core.config import get_db_path
from five.db_models import Commit, CompletedTask
from five.managers.db_manager import DatabaseManager
from five.managers.git_manager import GitManager
from five.utils import NOOP_LOG


class TestInvoker:
    def __init__(
        self,
        runner: CliRunner,
        project_dir: Path,
        project_config_dir: Path,
        global_config_dir: Path,
    ):
        self.runner = runner
        self.project_dir = project_dir
        self.project_config_dir = project_config_dir
        self.global_config_dir = global_config_dir

    def _run_command(
        self, command_parts: list[str], expect_failure: bool = False, include_project: bool = True
    ) -> Result:
        full_command = list(command_parts)

        if include_project:
            full_command.extend(['--project', str(self.project_dir)])
            full_command.extend(['--global-config', str(self.global_config_dir)])
            full_command.extend(['--config', str(self.project_config_dir)])
        else:
            full_command.extend(['--global-config', str(self.global_config_dir)])

        result = self.runner.invoke(cli, full_command)

        if not expect_failure:
            if result.exit_code != 0:
                print('\n=== COMMAND FAILED ===')
                print(f'Command: {" ".join(command_parts)}')
                print(f'Exit code: {result.exit_code}')
                print(f'Output: {result.output}')
                if result.exception:
                    traceback.print_exception(
                        type(result.exception),
                        result.exception,
                        result.exception.__traceback__,
                    )
            assert result.exit_code == 0

        return result

    def run(self, command_parts: list[str], expect_failure: bool = False) -> Result:
        return self._run_command(command_parts, expect_failure, include_project=True)

    def run_without_project(self, command_parts: list[str], expect_failure: bool = False) -> Result:
        return self._run_command(command_parts, expect_failure, include_project=False)


def _git_manager(project_dir: Path, project_config_path: Path) -> GitManager:
    git_path = project_config_path / '.git'
    work_tree = project_dir
    return GitManager(NOOP_LOG, git_path, work_tree)


def _db_manager(global_config_path: Path) -> DatabaseManager:
    db_path = get_db_path(global_config_path)
    return DatabaseManager(NOOP_LOG, db_path)


def git_log(project_dir: Path, project_config_path: Path) -> str:
    git_manager = _git_manager(project_dir, project_config_path)
    result = git_manager.run(['log', '--oneline', '--all'])
    return result.stdout.strip()


def verify_git_commit_exists(
    project_dir: Path, project_config_path: Path, commit_message: str
) -> bool:
    return commit_message in git_log(project_dir, project_config_path)


def ensure_tables_exist(db_path: Path, expected_tables: Iterable[str]) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

    missing = set(expected_tables) - tables
    assert not missing, f'Missing tables: {", ".join(sorted(missing))}'


def get_commits(db_path: Path):
    global_config_path = db_path.parent
    db_manager = _db_manager(global_config_path)
    db_manager.connect(create_tables=False)

    with db_session:
        commits = Commit.select()[:]
        return [(c.id, c.hash, c.type) for c in commits]


def get_commit_by_hash(db_path: Path, commit_hash: str):
    global_config_path = db_path.parent
    db_manager = _db_manager(global_config_path)
    db_manager.connect(create_tables=False)

    from five.db_models import Commit

    with db_session:
        commit_entity = Commit.get(hash=commit_hash)
        if not commit_entity:
            return None
        return (
            commit_entity.id,
            commit_entity.hash,
            commit_entity.type,
            commit_entity.completed_task.id if commit_entity.completed_task else None,
        )


def get_task_by_id(db_path: Path, task_id: int | None):
    if task_id is None:
        return None
    global_config_path = db_path.parent
    db_manager = _db_manager(global_config_path)
    db_manager.connect(create_tables=False)

    with db_session:
        task_entity = CompletedTask.get(id=task_id)
        if not task_entity:
            return None
        return (task_entity.id, task_entity.commit_id, task_entity.prompt, task_entity.model_name)


def get_task_with_revert(db_path: Path, task_id: int | None):
    if task_id is None:
        return None
    global_config_path = db_path.parent
    db_manager = _db_manager(global_config_path)
    db_manager.connect(create_tables=False)

    with db_session:
        task_entity = CompletedTask.get(id=task_id)
        if not task_entity:
            return None
        return (
            task_entity.id,
            task_entity.commit_id,
            task_entity.prompt,
            task_entity.model_name,
            task_entity.revert_commit_id,
            task_entity.is_deleted(),
        )


def read_state(project_config_path: Path) -> str | None:
    state_file = project_config_path / 'state'
    if not state_file.exists():
        return None
    return state_file.read_text().strip()
