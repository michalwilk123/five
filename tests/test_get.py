from __future__ import annotations

import json
from pathlib import Path

from pony.orm import db_session, flush

from five_cli.cli.main import cli
from five_cli.core.config import get_db_path
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager

from five_cli.db_models import CompletedTask


def create_test_git_commits(five_dir: Path):
    git_manager = GitManager(five_dir)

    test_file = five_dir / 'test1.txt'
    test_file.write_text('First test commit')

    result1 = (
        git_manager.chain()
        .stage_all()
        .commit('Test commit 1')
        .capture(['rev-parse', 'HEAD'])
        .get_result()
    )
    hash1 = result1.stdout.strip() if result1 else ''

    test_file2 = five_dir / 'test2.txt'
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
    five_dir = db_path.parent
    db_manager = DatabaseManager(five_dir)
    db_manager.connect(create_tables=True)

    with db_session:
        project = db_manager.create_project(
            name='test_project',
            path=str(project_path),
            git_repo_path=None,
            author='Test Author',
        )
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
    project_dir, runner, config_dir, invoker = initialized_project
    db_path = get_db_path(config_dir)

    hash1, hash2 = create_test_git_commits(config_dir)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run_without_project(['get', 'completed-tasks'])

    tasks = json.loads(result.output)
    assert len(tasks) == 2
    assert tasks[0]['prompt'] == 'Create hello function'
    assert tasks[0]['model_name'] == 'gpt-4'
    assert tasks[1]['prompt'] == 'Add error handling'
    assert tasks[1]['model_name'] == 'claude-3'


def test_get_completed_task_by_id(initialized_project):
    project_dir, runner, config_dir, invoker = initialized_project
    db_path = get_db_path(config_dir)

    hash1, hash2 = create_test_git_commits(config_dir)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run_without_project(['get', 'completed-tasks', '1'])

    task = json.loads(result.output)
    assert task['id'] == 1
    assert task['prompt'] == 'Create hello function'
    assert task['model_name'] == 'gpt-4'
    assert task['temperature'] == 0.7
    assert 'diff' in task


def test_get_commits_list(initialized_project):
    project_dir, runner, config_dir, invoker = initialized_project
    db_path = get_db_path(config_dir)

    hash1, hash2 = create_test_git_commits(config_dir)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run_without_project(['get', 'commits'])

    commits = json.loads(result.output)
    assert len(commits) == 2
    assert commits[0]['type'] == 'assistant'
    assert commits[1]['type'] == 'user'


def test_get_commit_by_id(initialized_project):
    project_dir, runner, config_dir, invoker = initialized_project
    db_path = get_db_path(config_dir)

    hash1, hash2 = create_test_git_commits(config_dir)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run_without_project(['get', 'commits', '1'])

    commit = json.loads(result.output)
    assert commit['id'] == 1
    assert commit['type'] == 'assistant'
    assert commit['completed_task_id'] == 1
    assert 'diff' in commit


def test_get_completed_task_nonexistent(initialized_project):
    project_dir, runner, config_dir, invoker = initialized_project
    db_path = get_db_path(config_dir)

    hash1, hash2 = create_test_git_commits(config_dir)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run_without_project(['get', 'completed-tasks', '999'], expect_failure=True)

    assert result.exit_code != 0
    assert 'Completed task with ID 999 not found' in result.output


def test_get_commit_nonexistent(initialized_project):
    project_dir, runner, config_dir, invoker = initialized_project
    db_path = get_db_path(config_dir)

    hash1, hash2 = create_test_git_commits(config_dir)
    populate_test_data(db_path, hash1, hash2, project_dir)

    result = invoker.run_without_project(['get', 'commits', '999'], expect_failure=True)

    assert result.exit_code != 0
    assert 'Commit with ID 999 not found' in result.output
