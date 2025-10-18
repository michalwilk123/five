from __future__ import annotations

from pony.orm import db_session

from five_cli.db_models import CompletedTask
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager
from five_cli.utils import LogFunction


@db_session
def fetch_task(db_manager: DatabaseManager, task_id: int, log: LogFunction) -> CompletedTask:
    log(f'Fetching task with ID: {task_id}')
    task = db_manager.get_completed_task_entity_by_id(task_id)
    if task is None:
        raise ValueError(f'Task with ID {task_id} not found')
    return task


def validate_task_not_deleted(task: CompletedTask, log: LogFunction):
    if task.is_deleted():
        raise ValueError(f'Task {task.id} has already been reverted')
    log(f'Task {task.id} is valid for undo')


@db_session
def get_commit_hash_for_task(
    db_manager: DatabaseManager, task: CompletedTask, log: LogFunction
) -> str:
    log(f'Fetching commit for task {task.id}')
    commit = db_manager.get_commit_entity_by_id(task.commit_id)
    if commit is None:
        raise ValueError(f'Commit with ID {task.commit_id} not found')
    log(f'Found commit hash: {commit.hash}')
    return commit.hash


def check_and_commit_user_changes(
    git_manager: GitManager, db_manager: DatabaseManager, commit_id: int, log: LogFunction
):
    log('Checking for user changes')
    status = git_manager.get_status()
    if not status.get('is_dirty'):
        log('No user changes to commit')
        return

    log('User changes detected, creating commit')
    commit_message = f'five:{commit_id}'
    git_manager.stage_all_changes()
    commit_hash = git_manager.create_commit(commit_message)
    log('User changes committed')

    log('Recording user commit in database')
    with db_session:
        db_manager.create_user_commit(commit_hash, note=None)
    log('User commit recorded in database')

    git_manager.stage_all_changes()
    log('Amending commit with database changes')
    git_manager.run(['commit', '--amend', '--no-edit'])


def revert_task_commit(git_manager: GitManager, commit_hash: str, log: LogFunction) -> str:
    log(f'Reverting commit {commit_hash}')
    revert_hash = git_manager.revert_commit(commit_hash)
    log(f'Created revert commit: {revert_hash}')
    return revert_hash


@db_session
def record_revert_commit(
    db_manager: DatabaseManager,
    revert_hash: str,
    log: LogFunction,
):
    log('Recording revert commit in database')
    revert_commit = db_manager.create_user_commit(revert_hash, note='revert')
    log(f'Saved revert commit with ID: {revert_commit.id}')
    return revert_commit


@db_session
def update_task_with_revert(
    db_manager: DatabaseManager,
    task_id: int,
    revert_commit_id: int,
    log: LogFunction,
):
    log(f'Updating task {task_id} with revert commit ID {revert_commit_id}')
    db_manager.update_task_revert_commit_id(task_id, revert_commit_id)
    log('Task updated successfully')


@db_session
def get_next_commit_id(db_manager: DatabaseManager, log: LogFunction) -> int:
    commit_id = db_manager.get_next_commit_id()
    log(f'Next commit ID: {commit_id}')
    return commit_id
