from pathlib import Path

from five_cli.core import get as get_core
from five_cli.core import init as init_core
from five_cli.core import redo as redo_core
from five_cli.core import track
from five_cli.core import undo as undo_core
from five_cli.core.common import connect_database
from five_cli.core.config import ensure_global_config_path, get_db_path
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.factory import ManagerFactory
from five_cli.utils import LogFunction

__all__ = [
    'setup_handler',
    'init_handler',
    'track_start_handler',
    'track_stop_handler',
    'track_cancel_handler',
    'handle_get_completed_tasks',
    'handle_get_commits',
    'handle_get_projects',
    'undo_handler',
    'redo_handler',
]


def setup_handler(global_config_path: Path, log: LogFunction):
    log(f'Setting up five at {global_config_path}')

    log('Creating five directory structure')
    ensure_global_config_path(global_config_path)

    log('Initializing database')
    db_path = get_db_path(global_config_path)
    db_manager = DatabaseManager(log, db_path)
    db_manager.connect(create_tables=True)
    log(f'Database created at {db_manager.db_path}')

    log('Five setup completed')
    return global_config_path


def init_handler(
    project_path: Path,
    global_config_path: Path,
    log: LogFunction,
):
    log(f'Initializing project at {project_path}')

    db_path = get_db_path(global_config_path)
    db_manager = DatabaseManager(log, db_path)
    connect_database(db_manager, log)

    unique_project_name = init_core.prepare_project_name(project_path, db_manager, log)
    git_repo_path = init_core.find_project_git_repo(project_path, log)
    author = init_core.get_git_author(log)

    init_core.create_project_entry(
        db_manager, unique_project_name, project_path, git_repo_path, author, log
    )

    project_config_dir = init_core.initialize_project_directories(
        global_config_path, unique_project_name, project_path, log
    )

    init_core.initialize_checkpoint_repository(project_path, project_config_dir, log)
    init_core.create_gitignore_for_project_git(project_config_dir, log)

    factory = ManagerFactory(project_path, global_config_path, project_config_dir, log)
    git_manager = factory.create_git_manager()

    commit_hash = track.create_user_commit_for_pending_changes(db_manager, git_manager, log)
    if commit_hash:
        log(f'Created initial user commit: {commit_hash[:8]}')

    return unique_project_name


def track_start_handler(
    project_path: Path, global_config_path: Path, project_config_path: Path, log: LogFunction
) -> str | None:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
    git_manager = factory.create_git_manager()
    db_manager = factory.create_db_manager()
    state_manager = factory.create_state_manager()

    track.ensure_not_started(state_manager, log)

    connect_database(db_manager, log)

    commit_hash = track.create_user_commit_for_pending_changes(db_manager, git_manager, log)
    if commit_hash is None:
        log('No changes detected, skipping commit creation')
        track.mark_start(state_manager, log)
        return None

    track.mark_start(state_manager, log)
    return commit_hash


def track_stop_handler(
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    log: LogFunction,
    prompt: str,
    temperature: float | None,
    model_name: str | None,
    reference_ids: list[int],
) -> str:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
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
    track.clear_state(state_manager, log)

    return commit_hash


def track_cancel_handler(
    project_path: Path, global_config_path: Path, project_config_path: Path, log: LogFunction
) -> None:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
    state_manager = factory.create_state_manager()

    track.ensure_started(state_manager, log)
    track.clear_state(state_manager, log)


def handle_get_completed_tasks(
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    log: LogFunction,
    task_id: int | None,
    project_name: str | None,
) -> list[dict] | dict:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
    db_manager = factory.create_db_manager()
    connect_database(db_manager, log)

    project_id = None
    if project_name is not None:
        project = db_manager.get_project_by_name(project_name)
        if not project:
            raise ValueError(f'Project with name "{project_name}" not found')
        project_id = project.id

    if task_id is None:
        tasks = get_core.fetch_completed_tasks_list(db_manager, log, project_id)
        return tasks

    git_manager = factory.create_git_manager()
    task = get_core.fetch_completed_task_with_diff(db_manager, git_manager, task_id, log)
    if task is None:
        raise ValueError(f'Completed task with ID {task_id} not found')
    return task


def handle_get_commits(
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    log: LogFunction,
    commit_id: int | None,
    project_name: str | None,
) -> list[dict] | dict:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
    db_manager = factory.create_db_manager()
    connect_database(db_manager, log)

    project_id = None
    if project_name is not None:
        project = db_manager.get_project_by_name(project_name)
        if not project:
            raise ValueError(f'Project with name "{project_name}" not found')
        project_id = project.id

    if commit_id is None:
        commits = get_core.fetch_commits_by_project_id(db_manager, log, project_id)
        return commits

    git_manager = factory.create_git_manager()
    commit = get_core.fetch_commit_with_diff(db_manager, git_manager, commit_id, log)
    if commit is None:
        raise ValueError(f'Commit with ID {commit_id} not found')
    return commit


def handle_get_projects(
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    log: LogFunction,
    project_id: int | None,
) -> list[dict] | dict:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
    db_manager = factory.create_db_manager()
    connect_database(db_manager, log)

    if project_id is None:
        projects = get_core.fetch_projects_list(db_manager, log)
        return projects

    project = get_core.fetch_project(db_manager, project_id, log)
    if project is None:
        raise ValueError(f'Project with ID {project_id} not found')
    return project


def undo_handler(
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    task_id: int,
    log: LogFunction,
) -> str:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
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

    return revert_hash


def redo_handler(
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    task_id: int,
    log: LogFunction,
) -> str:
    factory = ManagerFactory(project_path, global_config_path, project_config_path, log)
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

    return redo_hash
