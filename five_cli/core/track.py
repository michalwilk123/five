from pony.orm import db_session

from five_cli.db_models import CompletedTask
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager
from five_cli.managers.state_manager import StateManager
from five_cli.utils import LogFunction


def ensure_not_started(state_manager: StateManager, log: LogFunction):
    state_manager.require_not_started()
    log('Verified tracking has not started yet')


def ensure_started(state_manager: StateManager, log: LogFunction):
    state_manager.require_started()
    log('Verified tracking session is active')


def get_repository_status(git_manager: GitManager, log: LogFunction) -> dict:
    log('Checking git status')
    return git_manager.get_status()


def repository_has_changes(status: dict) -> bool:
    return bool(status.get('is_dirty'))


def create_user_commit_for_pending_changes(
    db_manager: DatabaseManager,
    git_manager: GitManager,
    log: LogFunction,
) -> str | None:
    status = get_repository_status(git_manager, log)
    if not repository_has_changes(status):
        return None
    log('Pending changes detected, creating user commit')
    commit_id = get_next_commit_id(db_manager, log)
    commit_hash = create_commit(git_manager, commit_id, log)
    record_user_commit(db_manager, commit_hash, log)
    return commit_hash


@db_session
def get_next_commit_id(db_manager: DatabaseManager, log: LogFunction) -> int:
    commit_id = db_manager.get_next_commit_id()
    log(f'Next commit ID: {commit_id}')
    return commit_id


def create_commit(git_manager: GitManager, commit_id: int, log: LogFunction) -> str:
    commit_message = build_commit_message(commit_id)
    log(f'Creating commit with message: {commit_message}')
    commit_hash = git_manager.create_commit(commit_message)
    log(f'Created commit: {commit_hash}')
    return commit_hash


def build_commit_message(commit_id: int) -> str:
    return f'five:{commit_id}'


@db_session
def record_user_commit(
    db_manager: DatabaseManager,
    commit_hash: str,
    log: LogFunction,
):
    user_commit = db_manager.create_user_commit(commit_hash, note=None)
    log(f'Saved commit to database with ID: {user_commit.id}')
    return user_commit


@db_session
def record_completed_task(
    db_manager: DatabaseManager,
    commit_id: int,
    prompt: str,
    temperature: float | None,
    model_name: str | None,
    reference_ids: list[int],
    project_path: str,
    log: LogFunction,
) -> CompletedTask:
    log('Creating completed task')
    project = db_manager.get_project_by_path(project_path)
    if not project:
        raise ValueError(f'Project not found for path: {project_path}')

    completed_task = db_manager.create_completed_task(
        commit_id,
        prompt,
        model_name,
        temperature,
        reference_ids,
        project,
    )
    log(f'Created completed task with ID: {completed_task.id}')
    return completed_task


@db_session
def record_assistant_commit(
    db_manager: DatabaseManager,
    commit_hash: str,
    completed_task_id: int,
    log: LogFunction,
):
    log('Creating assistant commit')
    assistant_commit = db_manager.create_assistant_commit(
        commit_hash,
        completed_task_id,
        note=None,
    )
    log(f'Created assistant commit with ID: {assistant_commit.id}')
    return assistant_commit


def mark_start(state_manager: StateManager, log: LogFunction):
    state_manager.save('start')
    log('Saved state: start')


def mark_stop(state_manager: StateManager, log: LogFunction):
    state_manager.save('stop')
    log('Saved state: stop')


def clear_state(state_manager: StateManager, log: LogFunction):
    state_manager.clear()
    log('Cleared state file')
