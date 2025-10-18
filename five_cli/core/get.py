from __future__ import annotations

from pony.orm import db_session

from five_cli.core.common import get_diff_for_commit
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager
from five_cli.utils import LogFunction


@db_session
def fetch_completed_tasks_list(
    db_manager: DatabaseManager,
    log: LogFunction,
) -> list[dict]:
    log('Fetching all completed tasks')
    tasks = db_manager.get_all_completed_tasks()
    log(f'Found {len(tasks)} completed tasks')
    return tasks


@db_session
def fetch_completed_task_with_diff(
    db_manager: DatabaseManager,
    git_manager: GitManager,
    task_id: int,
    log: LogFunction,
) -> dict | None:
    log(f'Fetching completed task {task_id}')
    task = db_manager.get_completed_task_by_id(task_id)

    if not task:
        log(f'Completed task {task_id} not found')
        return None

    commit_id = task.get('commit_id')
    if not commit_id:
        log(f'No commit_id associated with task {task_id}')
        return task

    diff = get_diff_for_commit(db_manager, git_manager, commit_id, log)
    if diff:
        task['diff'] = diff

    return task


@db_session
def fetch_commits_list(
    db_manager: DatabaseManager,
    log: LogFunction,
) -> list[dict]:
    log('Fetching all commits')
    commits = db_manager.get_all_commits()
    log(f'Found {len(commits)} commits')
    return commits


@db_session
def fetch_commit_with_diff(
    db_manager: DatabaseManager,
    git_manager: GitManager,
    commit_id: int,
    log: LogFunction,
) -> dict | None:
    log(f'Fetching commit {commit_id}')
    commit = db_manager.get_commit_by_id(commit_id)

    if not commit:
        log(f'Commit {commit_id} not found')
        return None

    diff = get_diff_for_commit(db_manager, git_manager, commit_id, log)
    if diff:
        commit['diff'] = diff

    return commit
