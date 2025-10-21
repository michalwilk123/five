import json
from pathlib import Path

from pony.orm import db_session, flush

from five.core.config import get_db_path
from five.db_models import CompletedTask, Project
from five.managers.db_manager import DatabaseManager
from five.managers.git_manager import GitManager, init_git_repo_in_dir
from five.utils import NOOP_LOG


def create_test_git_commits(project_dir: Path, project_config_path: Path):
    """
    Create test git commits in the checkpoint repository.

    Args:
        project_dir: The actual project directory (work_tree)
        project_config_path: The project-specific config directory (contains .git)
    """
    project_config_path.mkdir(parents=True, exist_ok=True)
    git_dir = project_config_path / '.git'
    init_git_repo_in_dir(project_dir, git_dir)

    work_tree = project_dir
    git_manager = GitManager(NOOP_LOG, git_dir, work_tree)

    test_file = project_dir / 'test1.txt'
    test_file.write_text('First test commit')

    result1 = (
        git_manager.chain()
        .stage_all()
        .commit('Test commit 1')
        .capture(['rev-parse', 'HEAD'])
        .get_result()
    )
    hash1 = result1.stdout.strip() if result1 else ''

    test_file2 = project_dir / 'test2.txt'
    test_file2.write_text('Second test commit')

    result2 = (
        git_manager.chain()
        .stage_all()
        .commit('Test commit 2')
        .capture(['rev-parse', 'HEAD'])
        .get_result()
    )
    hash2 = result2.stdout.strip() if result2 else ''

    return hash1, hash2


def populate_test_data(db_path: Path, hash1: str, hash2: str, project_path: Path):
    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=True)

    with db_session:
        # Query for the existing project instead of creating a new one
        project_path_str = str(project_path.resolve())
        project = db_manager.get_project_by_path(project_path_str)

        if not project:
            raise ValueError(f'Project not found at {project_path_str}')

        flush()

        task1 = CompletedTask(
            position=1,
            commit_id=1,
            prompt='Create hello function',
            model_name='gpt-4',
            temperature=0.7,
            project=project,
        )
        flush()

        assistant_commit = db_manager.create_assistant_commit(hash1, task1.id, note=None)
        flush()

        CompletedTask(
            position=2,
            commit_id=assistant_commit.id,
            prompt='Add error handling',
            model_name='claude-3',
            temperature=None,
            project=project,
        )

        db_manager.create_user_commit(hash2, note=None)


def test_get_completed_tasks_list(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    hash1, hash2 = create_test_git_commits(project_dir, project_config_path)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run(['get', 'completed-tasks'])

    tasks = json.loads(result.output)
    assert len(tasks) == 2
    assert tasks[0]['prompt'] == 'Create hello function'
    assert tasks[0]['model_name'] == 'gpt-4'
    assert tasks[1]['prompt'] == 'Add error handling'
    assert tasks[1]['model_name'] == 'claude-3'


def test_get_completed_task_by_id(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    hash1, hash2 = create_test_git_commits(project_dir, project_config_path)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run(['get', 'completed-tasks', '1'])

    task = json.loads(result.output)
    assert task['id'] == 1
    assert task['prompt'] == 'Create hello function'
    assert task['model_name'] == 'gpt-4'
    assert task['temperature'] == 0.7
    assert 'generated_code' in task


def test_get_commits_list(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    hash1, hash2 = create_test_git_commits(project_dir, project_config_path)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run(['get', 'commits'])

    commits = json.loads(result.output)
    assert len(commits) == 2
    assert commits[0]['type'] == 'assistant'
    assert commits[1]['type'] == 'user'


def test_get_commit_by_id(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    hash1, hash2 = create_test_git_commits(project_dir, project_config_path)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run(['get', 'commits', '1'])

    commit = json.loads(result.output)
    assert commit['id'] == 1
    assert commit['type'] == 'assistant'
    assert commit['completed_task_id'] == 1
    assert 'diff' in commit


def test_get_completed_task_nonexistent(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    hash1, hash2 = create_test_git_commits(project_dir, project_config_path)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run(['get', 'completed-tasks', '999'], expect_failure=True)

    assert result.exit_code != 0
    assert 'Completed task with ID 999 not found' in result.output


def test_get_commit_nonexistent(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    hash1, hash2 = create_test_git_commits(project_dir, project_config_path)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run(['get', 'commits', '999'], expect_failure=True)

    assert result.exit_code != 0
    assert 'Commit with ID 999 not found' in result.output


def test_get_project_list(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=True)

    result = invoker.run(['get', 'projects'])

    projects = json.loads(result.output)
    assert len(projects) == 1
    assert projects[0]['name'] == project_dir.name
    assert projects[0]['path'] == str(project_dir.resolve())


def test_get_project_detail(initialized_project):
    project_dir, runner, global_config_dir, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_dir)

    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=True)

    with db_session:
        project = Project.get(path=str(project_dir.resolve()))
        project_id = project.id

    result = invoker.run(['get', 'projects', str(project_id)])

    project_data = json.loads(result.output)
    assert project_data['id'] == project_id
    assert project_data['name'] == project_dir.name
