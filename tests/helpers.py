from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Iterable

from click.testing import CliRunner, Result
from pony.orm import db_session

from five_cli.cli.main import cli
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager


class TestInvoker:
    def __init__(self, runner: CliRunner, project_dir: Path, config_dir: Path):
        self.runner = runner
        self.project_dir = project_dir
        self.config_dir = config_dir
    
    def run(self, command_parts: list[str], expect_failure: bool = False) -> Result:
        full_command = [command_parts[0]]

        full_command.extend(['--project', str(self.project_dir)])
        full_command.extend(['--config', str(self.config_dir)])
        full_command.extend(command_parts[1:])
        
        result = self.runner.invoke(cli, full_command)
        
        if not expect_failure:
            if result.exit_code != 0:
                print(f"\n=== COMMAND FAILED ===")
                print(f"Command: {' '.join(command_parts)}")
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    import traceback
                    traceback.print_exception(
                        type(result.exception),
                        result.exception,
                        result.exception.__traceback__,
                    )
            assert result.exit_code == 0
        
        return result

    def run_without_project(self, command_parts: list[str], expect_failure: bool = False) -> Result:
        full_command = [command_parts[0]]
        
        full_command.extend(['--config', str(self.config_dir)])
        full_command.extend(command_parts[1:])
        
        result = self.runner.invoke(cli, full_command)
        
        if not expect_failure:
            if result.exit_code != 0:
                print(f"\n=== COMMAND FAILED ===")
                print(f"Command: {' '.join(command_parts)}")
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                if result.exception:
                    import traceback
                    traceback.print_exception(
                        type(result.exception),
                        result.exception,
                        result.exception.__traceback__,
                    )
            assert result.exit_code == 0
        
        return result



def _git_manager(five_dir: Path) -> GitManager:
    git_dir = five_dir / '.git'
    return GitManager(five_dir, git_dir)


def _db_manager(five_dir: Path) -> DatabaseManager:
    return DatabaseManager(five_dir)


def git_log(five_dir: Path) -> str:
    git_manager = _git_manager(five_dir)
    result = git_manager.run(['log', '--oneline', '--all'])
    return result.stdout.strip()


def verify_git_commit_exists(five_dir: Path, commit_message: str) -> bool:
    return commit_message in git_log(five_dir)


def ensure_tables_exist(db_path: Path, expected_tables: Iterable[str]) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

    missing = set(expected_tables) - tables
    assert not missing, f'Missing tables: {", ".join(sorted(missing))}'


def get_commits(db_path: Path):
    five_dir = db_path.parent
    db_manager = _db_manager(five_dir)
    db_manager.connect(create_tables=False)

    from five_cli.db_models import Commit
    with db_session:
        commits = Commit.select()[:]
        return [(c.id, c.hash, c.type) for c in commits]


def get_commit_by_hash(db_path: Path, commit_hash: str):
    five_dir = db_path.parent
    db_manager = _db_manager(five_dir)
    db_manager.connect(create_tables=False)

    from five_cli.db_models import Commit
    with db_session:
        commit_entity = Commit.get(hash=commit_hash)
        if not commit_entity:
            return None
        return (
            commit_entity.id,
            commit_entity.hash,
            commit_entity.type,
            commit_entity.completed_task_id,
        )


def get_task_by_id(db_path: Path, task_id: int | None):
    if task_id is None:
        return None
    five_dir = db_path.parent
    db_manager = _db_manager(five_dir)
    db_manager.connect(create_tables=False)

    from five_cli.db_models import CompletedTask
    with db_session:
        task_entity = CompletedTask.get(id=task_id)
        if not task_entity:
            return None
        return (task_entity.id, task_entity.commit_id, task_entity.prompt, task_entity.model_name)


def get_task_with_revert(db_path: Path, task_id: int | None):
    if task_id is None:
        return None
    five_dir = db_path.parent
    db_manager = _db_manager(five_dir)
    db_manager.connect(create_tables=False)

    from five_cli.db_models import CompletedTask
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


def read_state(five_dir: Path) -> str | None:
    state_file = five_dir / 'state'
    if not state_file.exists():
        return None
    return state_file.read_text().strip()
