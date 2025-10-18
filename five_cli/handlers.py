from __future__ import annotations

from pathlib import Path

from five_cli.core import get as get_core
from five_cli.core import redo as redo_core
from five_cli.core import track
from five_cli.core import undo as undo_core
from five_cli.core.common import connect_database, format_json_output
from five_cli.core.config import (
    ensure_five_dir,
    get_db_path,
)
from five_cli.managers import GitManager, get_git_config_value, init_git_repo
from five_cli.managers.common import ManagerFactory
from five_cli.managers.db_manager import DatabaseManager
from five_cli.utils import (
    NOOP_LOG,
    LogFunction,
    find_git_repo_path,
    generate_unique_project_name,
)

__all__ = [
    'setup_handler',
    'init_handler',
    'track_start_handler',
    'track_stop_handler',
    'track_cancel_handler',
    'handle_get_completed_tasks',
    'handle_get_commits',
    'undo_handler',
    'redo_handler',
]


def setup_handler(config_path: Path, logger: LogFunction | None):
    log = logger or NOOP_LOG

    log(f'Setting up five at {config_path}')

    log('Creating five directory structure')
    ensure_five_dir(config_path)

    log('Initializing database')
    db_manager = DatabaseManager(config_path, logger)
    db_manager.connect(create_tables=True)
    log(f'Database created at {db_manager.db_path}')

    git_dir = config_path / '.git'
    log(f'Initializing git repository at {git_dir}')
    init_git_repo(config_path, git_dir)

    git_manager = GitManager(config_path, git_dir, logger=logger)

    author = get_git_config_value('user.name') or 'Unknown'
    log(f'Creating initial commit by {author}')
    git_manager.create_initial_commit(f'Initial commit by {author}')

    log('Five setup completed')
    return config_path


def init_handler(
    project_path: Path,
    config_path: Path,
    interactive: bool,
    logger: LogFunction | None,
    prompt_func=None,
):
    log = logger or NOOP_LOG

    log(f'Initializing project at {project_path}')

    db_path = get_db_path(config_path)
    setup_exists = db_path.exists()

    if not setup_exists:
        if interactive:
            if prompt_func is None:
                import click

                prompt_func = click.confirm

            log(f'Five is not set up at {config_path}')
            should_setup = prompt_func('Would you like to set up five now?', default=True)
            if should_setup:
                setup_handler(config_path, logger)
            else:
                raise ValueError('Five setup is required before initializing a project')
        else:
            raise ValueError(
                f'Five is not set up at {config_path}. Run "five setup" first or use --interactive flag.'
            )

    log('Creating project entry in database')
    db_manager = DatabaseManager(config_path, logger)
    db_manager.connect(create_tables=False)

    project_path_str = str(project_path.resolve())
    base_project_name = project_path.name
    existing_project_names = db_manager.get_all_project_names()
    unique_project_name = generate_unique_project_name(base_project_name, existing_project_names)
    git_repo_path = find_git_repo_path(project_path)
    author = get_git_config_value('user.name') or 'Unknown'

    db_manager.create_project(
        name=unique_project_name,
        path=project_path_str,
        git_repo_path=git_repo_path,
        author=author,
    )
    log(f'Project "{unique_project_name}" initialized')

    return unique_project_name


def track_start_handler(
    project_path: Path, config_path: Path, logger: LogFunction | None
) -> str | None:
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    git_manager = factory.create_git_manager()
    db_manager = factory.create_db_manager()
    state_manager = factory.create_state_manager()

    track.ensure_not_started(state_manager, log)

    status = track.get_repository_status(git_manager, log)
    if not track.repository_has_changes(status):
        log('No changes detected, skipping commit creation')
        track.mark_start(state_manager, log)
        return None

    log('Changes detected, preparing commit')
    connect_database(db_manager, log)
    commit_id = track.get_next_commit_id(db_manager, log)
    commit_hash = track.create_commit(git_manager, commit_id, log)
    track.record_user_commit(db_manager, commit_hash, log)
    track.mark_start(state_manager, log)
    return commit_hash


def track_stop_handler(
    project_path: Path,
    config_path: Path,
    logger: LogFunction | None,
    prompt: str,
    temperature: float | None,
    model_name: str | None,
    reference_ids: list[int],
) -> str:
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    git_manager = factory.create_git_manager()
    db_manager = factory.create_db_manager()
    state_manager = factory.create_state_manager()

    track.ensure_started(state_manager, log)

    connect_database(db_manager, log)
    commit_id = track.get_next_commit_id(db_manager, log)

    completed_task = track.record_completed_task(
        db_manager,
        commit_id,
        prompt,
        temperature,
        model_name,
        reference_ids,
        str(project_path.resolve()),
        log,
    )

    log('Staging all changes')
    git_manager.stage_all_changes()

    commit_hash = track.create_commit(git_manager, commit_id, log)

    track.record_assistant_commit(db_manager, commit_hash, completed_task.id, log)

    git_manager.stage_all_changes()
    log('Committing database metadata changes')
    git_manager.run(['commit', '--amend', '--no-edit'])

    track.clear_state(state_manager, log)

    return commit_hash


def track_cancel_handler(project_path: Path, config_path: Path, logger: LogFunction | None) -> None:
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    state_manager = factory.create_state_manager()

    track.ensure_started(state_manager, log)
    track.clear_state(state_manager, log)


def handle_get_completed_tasks(
    project_path: Path,
    config_path: Path,
    logger: LogFunction | None,
    task_id: int | None,
    pretty_print: bool,
):
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    db_manager = factory.create_db_manager()
    git_manager = factory.create_git_manager()

    connect_database(db_manager, log)

    if task_id is None:
        tasks = get_core.fetch_completed_tasks_list(db_manager, log)
        return format_json_output(tasks, pretty_print)

    task = get_core.fetch_completed_task_with_diff(db_manager, git_manager, task_id, log)
    if task is None:
        raise ValueError(f'Completed task with ID {task_id} not found')
    return format_json_output(task, pretty_print)


def handle_get_commits(
    project_path: Path,
    config_path: Path,
    logger: LogFunction | None,
    commit_id: int | None,
    pretty_print: bool,
):
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    db_manager = factory.create_db_manager()
    git_manager = factory.create_git_manager()

    connect_database(db_manager, log)

    if commit_id is None:
        commits = get_core.fetch_commits_list(db_manager, log)
        return format_json_output(commits, pretty_print)

    commit = get_core.fetch_commit_with_diff(db_manager, git_manager, commit_id, log)
    if commit is None:
        raise ValueError(f'Commit with ID {commit_id} not found')
    return format_json_output(commit, pretty_print)


def undo_handler(
    project_path: Path, config_path: Path, task_id: int, logger: LogFunction | None
) -> str:
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    git_manager = factory.create_git_manager()
    db_manager = factory.create_db_manager()

    connect_database(db_manager, log)

    task = undo_core.fetch_task(db_manager, task_id, log)
    undo_core.validate_task_not_deleted(task, log)

    commit_hash = undo_core.get_commit_hash_for_task(db_manager, task, log)

    next_commit_id = undo_core.get_next_commit_id(db_manager, log)
    undo_core.check_and_commit_user_changes(git_manager, db_manager, next_commit_id, log)

    revert_hash = undo_core.revert_task_commit(git_manager, commit_hash, log)

    revert_commit = undo_core.record_revert_commit(db_manager, revert_hash, log)
    undo_core.update_task_with_revert(db_manager, task_id, revert_commit.id, log)

    git_manager.stage_all_changes()
    log('Committing database metadata changes')
    git_manager.run(['commit', '--amend', '--no-edit'])

    return revert_hash


def redo_handler(
    project_path: Path, config_path: Path, task_id: int, logger: LogFunction | None
) -> str:
    log = logger or NOOP_LOG
    factory = ManagerFactory(project_path, config_path, logger)
    git_manager = factory.create_git_manager()
    db_manager = factory.create_db_manager()

    connect_database(db_manager, log)

    task = redo_core.fetch_task(db_manager, task_id, log)
    redo_core.validate_task_is_deleted(task, log)

    revert_commit_hash = redo_core.get_revert_commit_hash(db_manager, task, log)

    next_commit_id = redo_core.get_next_commit_id(db_manager, log)
    redo_core.check_and_commit_user_changes(git_manager, db_manager, next_commit_id, log)

    redo_hash = redo_core.revert_revert_commit(git_manager, revert_commit_hash, log)

    redo_core.record_redo_commit(db_manager, redo_hash, log)
    redo_core.clear_task_revert(db_manager, task_id, log)

    git_manager.stage_all_changes()
    log('Committing database metadata changes')
    git_manager.run(['commit', '--amend', '--no-edit'])

    return redo_hash
