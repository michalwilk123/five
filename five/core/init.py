from pathlib import Path

from pony.orm import db_session

from five.core.config import ensure_global_config_path, get_project_config_path
from five.managers import get_git_config_value
from five.managers.db_manager import DatabaseManager
from five.managers.git_manager import init_git_repo_in_dir
from five.utils import LogFunction, find_git_repo_path, generate_unique_project_name


@db_session
def prepare_project_name(project_path: Path, db_manager: DatabaseManager, log: LogFunction) -> str:
    log('Generating unique project name')
    base_project_name = project_path.name
    existing_project_names = db_manager.get_all_project_names()
    unique_project_name = generate_unique_project_name(base_project_name, existing_project_names)
    log(f'Generated project name: {unique_project_name}')
    return unique_project_name


def get_git_author(log: LogFunction) -> str:
    log('Fetching git author')
    author = get_git_config_value('user.name') or 'Unknown'
    log(f'Git author: {author}')
    return author


def find_project_git_repo(project_path: Path, log: LogFunction) -> str | None:
    log('Looking for existing git repository')
    git_repo_path = find_git_repo_path(project_path)
    if git_repo_path:
        log(f'Found git repository at: {git_repo_path}')
    else:
        log('No git repository found')
    return git_repo_path


@db_session
def create_project_entry(
    db_manager: DatabaseManager,
    name: str,
    project_path: Path,
    git_repo_path: str | None,
    author: str,
    log: LogFunction,
):
    log('Creating project entry in database')
    db_manager.create_project(
        name=name,
        path=str(project_path.resolve()),
        git_repo_path=git_repo_path,
        author=author,
    )
    log(f'Project "{name}" created in database')


def initialize_project_directories(
    global_config_path: Path, project_name: str, project_path: Path, log: LogFunction
) -> Path:
    log('Creating project configuration directory')
    project_config_dir = get_project_config_path(global_config_path, project_name)
    ensure_global_config_path(project_config_dir)
    log(f'Created project config directory at {project_config_dir}')

    log('Ensuring project directory exists')
    ensure_global_config_path(project_path)
    log('Project directory verified')

    return project_config_dir


def initialize_checkpoint_repository(
    project_path: Path, project_config_dir: Path, log: LogFunction
):
    log('Initializing checkpoint git repository')
    git_path = project_config_dir / '.git'
    init_git_repo_in_dir(project_path, git_path)
    log(f'Checkpoint repository initialized at {project_config_dir}')
