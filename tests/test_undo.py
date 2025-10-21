from five_cli.core.config import get_db_path

from .helpers import (
    get_commits,
    get_task_with_revert,
    verify_git_commit_exists,
)


def test_undo_happy_path(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('User initial setup')

    invoker.run(['track', 'start'])

    test_file = project_dir / 'test_feature.py'
    test_file.write_text('def new_feature():\n    return "feature"\n')

    result_stop = invoker.run(
        [
            'track',
            'stop',
            '--prompt',
            'Add new feature',
            '--model-name',
            'gpt-4',
            '--temperature',
            '0.5',
        ]
    )
    assert 'Created assistant commit:' in result_stop.output

    commits_before_undo = get_commits(db_path)
    assert len(commits_before_undo) == 2
    assert commits_before_undo[0][2] == 'user'
    assert commits_before_undo[1][2] == 'assistant'

    task_before_undo = get_task_with_revert(db_path, 1)
    assert task_before_undo is not None
    assert task_before_undo[0] == 1
    assert task_before_undo[2] == 'Add new feature'
    assert task_before_undo[4] is None
    assert task_before_undo[5] is False

    assert verify_git_commit_exists(project_dir, project_config_path, 'five:1')

    result_undo = invoker.run(['undo', '1'])
    assert 'Task 1 has been reverted' in result_undo.output
    assert 'Revert commit:' in result_undo.output

    commits_after_undo = get_commits(db_path)
    assert len(commits_after_undo) == 3
    assert commits_after_undo[0][2] == 'user'
    assert commits_after_undo[1][2] == 'assistant'
    assert commits_after_undo[2][2] == 'user'

    task_after_undo = get_task_with_revert(db_path, 1)
    assert task_after_undo is not None
    assert task_after_undo[0] == 1
    assert task_after_undo[4] is not None
    assert task_after_undo[4] == 3
    assert task_after_undo[5] is True

    result_undo_again = invoker.run(['undo', '1'], expect_failure=True)
    assert result_undo_again.exit_code != 0
    assert 'has already been reverted' in result_undo_again.output


def test_undo_nonexistent_task(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    result = invoker.run(['undo', '999'], expect_failure=True)
    assert result.exit_code != 0
    assert 'Task with ID 999 not found' in result.output


def test_undo_with_user_changes(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_setup = project_dir / 'user_setup.txt'
    user_setup.write_text('User initial setup')

    invoker.run(['track', 'start'])

    ai_file = project_dir / 'ai_code.py'
    ai_file.write_text('def ai_function():\n    pass\n')

    invoker.run(['track', 'stop', '--prompt', 'Create AI function'])

    commits_after_stop = get_commits(db_path)
    assert len(commits_after_stop) == 2

    user_file = project_dir / 'user_changes.txt'
    user_file.write_text('Some user modifications')

    invoker.run(['undo', '1'])

    commits_after_undo = get_commits(db_path)
    assert len(commits_after_undo) == 4
    assert commits_after_undo[0][2] == 'user'
    assert commits_after_undo[1][2] == 'assistant'
    assert commits_after_undo[2][2] == 'user'
    assert commits_after_undo[3][2] == 'user'

    assert verify_git_commit_exists(project_dir, project_config_path, 'five:1')
    assert verify_git_commit_exists(project_dir, project_config_path, 'five:2')

    task = get_task_with_revert(db_path, 1)
    assert task[4] == 4
    assert task[5] is True


def test_undo_multiple_tasks(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    for i in range(1, 4):
        invoker.run(['track', 'start'])

        task_file = project_dir / f'task_{i}.py'
        task_file.write_text(f'def task_{i}():\n    pass\n')

        invoker.run(['track', 'stop', '--prompt', f'Task {i}'])

    commits_before = get_commits(db_path)
    task_commits = [c for c in commits_before if c[2] == 'assistant']
    assert len(task_commits) == 3

    invoker.run(['undo', '2'])

    task_1 = get_task_with_revert(db_path, 1)
    task_2 = get_task_with_revert(db_path, 2)
    task_3 = get_task_with_revert(db_path, 3)

    assert task_1[5] is False
    assert task_2[5] is True
    assert task_3[5] is False

    invoker.run(['undo', '1'])

    invoker.run(['undo', '3'])

    task_1 = get_task_with_revert(db_path, 1)
    task_2 = get_task_with_revert(db_path, 2)
    task_3 = get_task_with_revert(db_path, 3)

    assert task_1[5] is True
    assert task_2[5] is True
    assert task_3[5] is True
