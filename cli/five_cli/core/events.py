import dataclasses
from datetime import datetime
import json
import os
from typing import Callable

from five_cli.core.config import get_five_paths
from five_cli.core.models import CompletedTask, Conversation, TaskChangePatch
from five_cli.vcs.git_utils import GitRepo


def NOOP_LOG(_msg: str) -> None:
    return None


def _handle_git_on_start(
    git_dir: str,
    project_path: str,
    logger: Callable[[str], None] | None,
) -> None:
    """Handle git operations on agent start."""
    log = logger or NOOP_LOG

    if not os.path.exists(git_dir):
        log(f'Git directory not found: {git_dir}')
        return

    log(f'Git directory found: {git_dir}')
    repo = GitRepo(git_dir, project_path)
    status = repo.get_status()
    log(f'Repository status: {status}')

    if status['is_dirty'] or status['untracked_files']:
        last_message = repo.get_last_commit_message()
        patch = TaskChangePatch.decode(last_message)
        last_type = patch.type if patch else 'unknown'
        log(f'Last commit type: {last_type}')
        if last_type == 'user':
            log('Amending last user commit')
            # Re-encode the message to ensure proper formatting
            new_message = patch.encode()
            repo.amend_last_commit(new_message)
        else:
            log('Creating new user commit')
            user_message = TaskChangePatch(id='0', type='user').encode()
            repo.create_commit(user_message)


def on_ai_agent_start(
    five_config_path: str,
    project_path: str,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None,
):
    log = logger or NOOP_LOG
    log('Entering the interface')
    sh('Entering the interface')

    _five_path, git_dir = get_five_paths(five_config_path)

    # Handle git operations
    _handle_git_on_start(git_dir, project_path, logger)


def _save_completed_task(
    five_path: str,
    completed_task: CompletedTask,
    logger: Callable[[str], None] | None,
) -> None:
    """Save completed task to config file."""
    log = logger or NOOP_LOG
    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')

    tasks = _load_completed_tasks(completed_tasks_file)
    tasks.append(dataclasses.asdict(completed_task))
    log(f'Added task to completed_tasks.json, total tasks: {len(tasks)}')

    with open(completed_tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2)


def _get_next_task_id_from_config(five_path: str) -> int:
    """Get next task ID from completed tasks config file."""
    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')
    tasks = _load_completed_tasks(completed_tasks_file)
    return _get_next_task_id(tasks)


def _handle_git_on_end(
    git_dir: str,
    project_path: str,
    task_id: str,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None,
) -> None:
    """Handle git operations on agent end."""
    log = logger or NOOP_LOG

    if not os.path.exists(git_dir):
        log(f'Git directory not found: {git_dir}')
        sh(f'Git directory not found: {git_dir}')
        return

    repo = GitRepo(git_dir, project_path)
    status = repo.get_status()
    if not status['is_dirty']:
        log('No changes detected, skipping commit')
        sh('No changes detected, skipping commit')
        return

    try:
        # Use TaskChangePatch to encode the commit message for codegen changes
        task_patch = TaskChangePatch(id=task_id, type='assistant')
        commit_message = task_patch.encode()
        commit_hash = repo.create_commit(commit_message)
        log(f'Created codegen commit: {commit_hash}')
        sh(f'Created codegen commit: {commit_hash[:8]}')
    except Exception as e:
        log(f'Failed to create codegen commit: {str(e)}')
        sh(f'Failed to create codegen commit: {str(e)}')


def on_ai_agent_stop(
    five_config_path: str,
    project_path: str,
    references: list[str],
    conversation: Conversation,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None,
) -> CompletedTask:
    log = logger or NOOP_LOG
    log('Exiting the interface')
    sh('Exiting the interface')

    five_path, git_dir = get_five_paths(five_config_path)
    next_id = _get_next_task_id_from_config(five_path)
    task_patch = TaskChangePatch(id=str(next_id), type='assistant')
    completed_task = CompletedTask(
        references=references,
        conversation=conversation,
        changes=task_patch,
        id=next_id,
        timestamp=datetime.now().isoformat(),
    )

    _handle_git_on_end(git_dir, project_path, str(next_id), sh, logger)
    _save_completed_task(five_path, completed_task, logger)

    return completed_task


def _load_completed_tasks(
    completed_tasks_file: str,
) -> list[dict]:
    try:
        with open(completed_tasks_file, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        tasks = []
    return tasks


def _get_next_task_id(tasks: list[dict]) -> int:
    if not tasks:
        return 0
    return tasks[-1]['id'] + 1
