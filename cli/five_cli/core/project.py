import json
import os
from typing import Callable

from five_cli.core.config import detect_if_five_initialized, get_five_paths
from five_cli.core.events import _load_completed_tasks
from five_cli.core.models import TaskChangePatch
from five_cli.vcs.git_utils import (
    GitRepo,
    configure_git_excludes_file,
    create_initial_commit,
    init_five_git_repo,
    is_rebase_in_progress,
    setup_five_gitignore,
)


def NOOP_LOG(_msg: str) -> None:
    return None


def _create_task_id_matcher(task_id: str):
    """Create a predicate function to match commits by TaskChangePatch ID."""
    def matches(message: str) -> bool:
        patch = TaskChangePatch.decode(message)
        return patch is not None and patch.id == task_id
    return matches


def five_init(
    five_config_path: str,
    project_path: str,
    dont_track: bool,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log(f'Initializing Five in project: {project_path}')
    if detect_if_five_initialized(five_config_path, project_path):
        log('Five already initialized')
        return {'error': 'Five is already initialized in this project', 'already_initialized': True}

    five_path = os.path.dirname(five_config_path)
    os.makedirs(five_path, exist_ok=True)

    files_created = _create_five_files(five_path)
    git_dir = init_five_git_repo(five_path)
    five_gitignore_path = setup_five_gitignore(five_path, project_path, dont_track=dont_track)
    configure_git_excludes_file(git_dir, project_path, five_gitignore_path)
    initial_message = TaskChangePatch(id='0', type='user').encode()
    initial_commit_hash = create_initial_commit(git_dir, project_path, initial_message)

    log(f'Five initialized with commit: {initial_commit_hash}')
    sh('Five initialized successfully!')
    sh(f'Five directory: {five_path}')
    sh(f'Project directory: {project_path}')
    sh(f'Initial commit: {initial_commit_hash[:8]}')

    return {
        'five_path': five_path,
        'project_path': project_path,
        'initial_commit': initial_commit_hash,
        'files_created': files_created + [five_gitignore_path],
    }


def _create_five_files(five_path: str):
    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')
    config_file = os.path.join(five_path, 'config.json')

    with open(completed_tasks_file, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2)

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump({}, f, indent=2)

    return [completed_tasks_file, config_file]


def five_status(
    five_config_path: str,
    project_path: str,
    max_count: int,
    sh: Callable[[str], None] | None = None,
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log(f'Checking Five status for project: {project_path}')
    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {
            'error': 'Five not initialized in this project. Run "five project init" first.',
            'initialized': False,
        }

    five_path = os.path.dirname(five_config_path)
    git_dir = os.path.join(five_path, '.git')
    work_tree = project_path
    repo = GitRepo(git_dir, work_tree)
    raw_commits = repo.get_log(max_count)

    # Decode TaskChangePatch from commit messages
    commits = []
    for commit in raw_commits:
        patch = TaskChangePatch.decode(commit['message'])
        commit_info = {
            'hash': commit['hash'],
            'full_hash': commit['full_hash'],
            'type': patch.type if patch else 'unknown',
            'timestamp': commit['timestamp'],
            'author': commit['author'],
            'date': commit['date'],
            'conversation_hash': patch.id if patch else None,
            'reference_hash': patch.id if patch else None,
            'is_init': (patch.id == '0') if patch else False,
        }
        commits.append(commit_info)

    log(f'Retrieved {len(commits)} commits')

    detailed_changes = repo.get_detailed_changes()
    log(f'Retrieved {len(detailed_changes)} file changes')

    return {
        'initialized': True,
        'commits': commits,
        'total_commits': len(commits),
        'uncommitted_changes': detailed_changes,
    }


def _load_undo_items(undo_items_file: str) -> list[dict]:
    try:
        with open(undo_items_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_undo_items(undo_items_file: str, undo_items: list[dict]):
    with open(undo_items_file, 'w', encoding='utf-8') as f:
        json.dump(undo_items, f, indent=2)


def _save_completed_tasks(completed_tasks_file: str, tasks: list[dict]):
    with open(completed_tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2)


def _handle_uncommitted_changes_before_undo(git_dir: str, project_path: str, logger: Callable[[str], None]):
    log = logger or NOOP_LOG
    repo = GitRepo(git_dir, project_path)
    status = repo.get_status()

    if status['is_dirty'] or status['untracked_files']:
        last_message = repo.get_last_commit_message()
        patch = TaskChangePatch.decode(last_message)
        last_type = patch.type if patch else 'unknown'
        log(f'Uncommitted changes detected. Last commit type: {last_type}')
        if last_type == 'user':
            log('Amending last user commit')
            # Re-encode the message to ensure proper formatting
            new_message = patch.encode()
            repo.amend_last_commit(new_message)
        else:
            log('Creating new user commit')
            user_message = TaskChangePatch(id='0', type='user').encode()
            repo.create_commit(user_message)


def five_undo(
    five_config_path: str,
    project_path: str,
    task_id: int | None,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log(f'Undoing task in project: {project_path}')

    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {'error': 'Five not initialized in this project. Run "five project init" first.'}

    five_path, git_dir = get_five_paths(five_config_path)
    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')
    undo_items_file = os.path.join(five_path, 'undo_items.json')

    tasks = _load_completed_tasks(completed_tasks_file)

    if not tasks:
        log('No completed tasks to undo')
        return {'error': 'No completed tasks to undo'}

    if task_id is None:
        task_to_undo = tasks[-1]
    else:
        task_to_undo = None
        for task in tasks:
            if task['id'] == task_id:
                task_to_undo = task
                break

        if task_to_undo is None:
            log(f'Task with ID {task_id} not found')
            return {'error': f'Task with ID {task_id} not found'}

    # NOTE: In the future, this should check if any later tasks reference this task
    # and handle those dependencies appropriately (e.g., refresh/update those commits)

    _handle_uncommitted_changes_before_undo(git_dir, project_path, logger)

    repo = GitRepo(git_dir, project_path)
    encoded_id = str(task_to_undo['id'])

    # Find commit by matching TaskChangePatch ID
    matcher = _create_task_id_matcher(encoded_id)
    commit_hash = repo.find_commit_by_message_match(matcher)

    if commit_hash is None:
        log(f'Commit for task {encoded_id} not found')
        return {'error': f'Commit for task {encoded_id} not found in git history'}

    commit_diff = repo.get_commit_diff(commit_hash)

    undo_item = task_to_undo.copy()
    undo_item['changes'] = commit_diff

    try:
        repo.rebase_drop_commit(commit_hash)
    except RuntimeError as e:
        log(f'Failed to undo commit: {str(e)}')
        return {'error': f'Failed to undo commit: {str(e)}'}

    undo_items = _load_undo_items(undo_items_file)
    undo_items.append(undo_item)
    _save_undo_items(undo_items_file, undo_items)

    tasks.remove(task_to_undo)
    _save_completed_tasks(completed_tasks_file, tasks)

    log(f'Successfully undone task {task_to_undo["id"]}')
    sh(f'Successfully undone task {task_to_undo["id"]}')

    return {
        'success': True,
        'undone_task_id': task_to_undo['id'],
        'commit_hash': commit_hash[:8],
    }


def _find_commit_before_task(tasks: list[dict], target_task_id: int) -> int | None:
    for i, task in enumerate(tasks):
        if task['id'] == target_task_id:
            if i == 0:
                return None
            return tasks[i - 1]['id']
    return None


def five_redo(
    five_config_path: str,
    project_path: str,
    task_id: int | None,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log(f'Redoing task in project: {project_path}')

    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {'error': 'Five not initialized in this project. Run "five project init" first.'}

    five_path, git_dir = get_five_paths(five_config_path)
    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')
    undo_items_file = os.path.join(five_path, 'undo_items.json')

    undo_items = _load_undo_items(undo_items_file)

    if not undo_items:
        log('No undone tasks to redo')
        return {'error': 'No undone tasks to redo'}

    if task_id is None:
        task_to_redo = undo_items[-1]
    else:
        task_to_redo = None
        for item in undo_items:
            if item['id'] == task_id:
                task_to_redo = item
                break

        if task_to_redo is None:
            log(f'Undone task with ID {task_id} not found')
            return {'error': f'Undone task with ID {task_id} not found'}

    _handle_uncommitted_changes_before_undo(git_dir, project_path, logger)

    tasks = _load_completed_tasks(completed_tasks_file)
    commit_before_id = _find_commit_before_task(tasks, task_to_redo['id'])

    if commit_before_id is None:
        log('Cannot redo: task was first in history')
        return {'error': 'Cannot redo: task was first in history, no commit to rebase onto'}

    repo = GitRepo(git_dir, project_path)

    # Find commit before by matching TaskChangePatch ID
    matcher = _create_task_id_matcher(str(commit_before_id))
    commit_before_hash = repo.find_commit_by_message_match(matcher)

    if commit_before_hash is None:
        log(f'Commit before task not found: {commit_before_id}')
        return {'error': f'Commit before task not found in git history'}

    task_patch = TaskChangePatch(id=str(task_to_redo['id']), type='assistant')
    task_message = task_patch.encode()

    try:
        repo.rebase_edit_commit(commit_before_hash)
        repo.apply_patch_and_continue_rebase(task_to_redo['changes'], task_message)
    except RuntimeError as e:
        log(f'Failed to redo commit: {str(e)}')
        return {'error': f'Failed to redo commit: {str(e)}'}

    undo_items.remove(task_to_redo)
    _save_undo_items(undo_items_file, undo_items)

    task_without_changes = task_to_redo.copy()
    del task_without_changes['changes']
    tasks.append(task_without_changes)
    _save_completed_tasks(completed_tasks_file, tasks)

    log(f'Successfully redone task {task_to_redo["id"]}')
    sh(f'Successfully redone task {task_to_redo["id"]}')

    return {
        'success': True,
        'redone_task_id': task_to_redo['id'],
    }


def _load_edit_state(edit_state_file: str) -> dict | None:
    try:
        with open(edit_state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_edit_state(edit_state_file: str, state: dict):
    with open(edit_state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def _clear_edit_state(edit_state_file: str):
    if os.path.exists(edit_state_file):
        os.remove(edit_state_file)


def five_edit_start(
    five_config_path: str,
    project_path: str,
    task_id: int,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log(f'Starting edit for task {task_id}')

    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {'error': 'Five not initialized in this project. Run "five project init" first.'}

    five_path, git_dir = get_five_paths(five_config_path)
    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')
    edit_state_file = os.path.join(five_path, 'edit_state.json')

    if is_rebase_in_progress(git_dir):
        existing_state = _load_edit_state(edit_state_file)
        if existing_state:
            return {'error': f'Edit already in progress for task {existing_state["task_id"]}'}
        return {'error': 'Rebase already in progress. Please resolve or abort it first.'}

    tasks = _load_completed_tasks(completed_tasks_file)

    task_to_edit = None
    for task in tasks:
        if task['id'] == task_id:
            task_to_edit = task
            break

    if task_to_edit is None:
        log(f'Task with ID {task_id} not found')
        return {'error': f'Task with ID {task_id} not found'}

    _handle_uncommitted_changes_before_undo(git_dir, project_path, logger)

    repo = GitRepo(git_dir, project_path)
    encoded_id = str(task_to_edit['id'])

    # Find commit by matching TaskChangePatch ID
    matcher = _create_task_id_matcher(encoded_id)
    commit_hash = repo.find_commit_by_message_match(matcher)

    if commit_hash is None:
        log(f'Commit for task {encoded_id} not found')
        return {'error': f'Commit for task {encoded_id} not found in git history'}

    try:
        repo.start_interactive_rebase_at_commit(commit_hash)
    except RuntimeError as e:
        log(f'Failed to start rebase: {str(e)}')
        return {'error': f'Failed to start rebase: {str(e)}'}

    edit_state = {
        'task_id': task_id,
        'task': task_to_edit,
        'commit_hash': commit_hash,
    }
    _save_edit_state(edit_state_file, edit_state)

    log(f'Edit started for task {task_id}')
    sh(f'Edit mode started for task {task_id}')

    return {
        'success': True,
        'task_id': task_id,
        'task': task_to_edit,
    }


def five_edit_current(
    five_config_path: str,
    project_path: str,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log('Getting current edit state')

    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {'error': 'Five not initialized in this project. Run "five project init" first.'}

    five_path, git_dir = get_five_paths(five_config_path)
    edit_state_file = os.path.join(five_path, 'edit_state.json')

    if not is_rebase_in_progress(git_dir):
        return {'error': 'No edit in progress. Run "five project edit <task_id>" first.'}

    edit_state = _load_edit_state(edit_state_file)
    if not edit_state:
        return {'error': 'No edit state found. Run "five project edit <task_id>" first.'}

    return {
        'success': True,
        'task_id': edit_state['task_id'],
        'task': edit_state['task'],
    }


def five_edit_run(
    five_config_path: str,
    project_path: str,
    prompt: str,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log(f'Running edit with prompt: {prompt[:50]}...')

    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {'error': 'Five not initialized in this project. Run "five project init" first.'}

    five_path, git_dir = get_five_paths(five_config_path)
    edit_state_file = os.path.join(five_path, 'edit_state.json')

    if not is_rebase_in_progress(git_dir):
        return {'error': 'No edit in progress. Run "five project edit <task_id>" first.'}

    edit_state = _load_edit_state(edit_state_file)
    if not edit_state:
        return {'error': 'No edit state found. Run "five project edit <task_id>" first.'}

    repo = GitRepo(git_dir, project_path)
    repo.reset_working_tree_changes()
    log('Cleared all unstaged changes')

    return {
        'success': True,
        'task_id': edit_state['task_id'],
        'prompt': prompt,
        'message': 'Ready to run claude command. Execute: claude -m "{}"'.format(prompt),
    }


def five_edit_confirm(
    five_config_path: str,
    project_path: str,
    sh: Callable[[str], None],
    logger: Callable[[str], None] | None = None,
):
    log = logger or NOOP_LOG
    log('Confirming edit changes')

    if not detect_if_five_initialized(five_config_path, project_path):
        log('Five not initialized')
        return {'error': 'Five not initialized in this project. Run "five project init" first.'}

    five_path, git_dir = get_five_paths(five_config_path)
    edit_state_file = os.path.join(five_path, 'edit_state.json')

    if not is_rebase_in_progress(git_dir):
        return {'error': 'No edit in progress. Run "five project edit <task_id>" first.'}

    edit_state = _load_edit_state(edit_state_file)
    if not edit_state:
        return {'error': 'No edit state found. Run "five project edit <task_id>" first.'}

    task_patch = TaskChangePatch(id=str(edit_state['task_id']), type='assistant')
    task_message = task_patch.encode()
    repo = GitRepo(git_dir, project_path)

    try:
        repo.amend_commit(task_message)
        log('Amended commit with changes')

        repo.continue_rebase()
        log('Rebase continued successfully')
    except Exception as e:
        log(f'Failed to confirm edit: {str(e)}')
        repo.abort_rebase()
        _clear_edit_state(edit_state_file)
        return {'error': f'Failed to confirm edit: {str(e)}'}

    _clear_edit_state(edit_state_file)
    sh(f'Edit confirmed for task {edit_state["task_id"]}')

    return {
        'success': True,
        'task_id': edit_state['task_id'],
    }
