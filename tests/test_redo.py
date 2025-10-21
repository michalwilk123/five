from five_cli.core.config import get_db_path

from .helpers import (
    get_commits,
    get_task_with_revert,
)


def test_redo_happy_path(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('User initial setup')

    invoker.run(['track', 'start'])

    test_file = project_dir / 'test_feature.py'
    test_file.write_text('def new_feature():\n    return "feature"\n')

    invoker.run(
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

    invoker.run(['undo', '1'])

    commits_after_undo = get_commits(db_path)
    assert len(commits_after_undo) == 3

    task_after_undo = get_task_with_revert(db_path, 1)
    assert task_after_undo is not None
    assert task_after_undo[4] is not None
    assert task_after_undo[5] is True

    result_redo = invoker.run(['redo', '1'])
    assert 'Task 1 has been redone' in result_redo.output
    assert 'Redo commit:' in result_redo.output

    commits_after_redo = get_commits(db_path)
    assert len(commits_after_redo) == 4

    task_after_redo = get_task_with_revert(db_path, 1)
    assert task_after_redo is not None
    assert task_after_redo[0] == 1
    assert task_after_redo[4] is None
    assert task_after_redo[5] is False


def test_redo_nonexistent_task(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    result = invoker.run(['redo', '999'], expect_failure=True)
    assert result.exit_code != 0
    assert 'Task with ID 999 not found' in result.output


def test_redo_without_undo_fails(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('User initial setup')

    invoker.run(['track', 'start'])

    test_file = project_dir / 'test_code.py'
    test_file.write_text('def test():\n    pass\n')

    invoker.run(['track', 'stop', '--prompt', 'Create test function'])

    result = invoker.run(['redo', '1'], expect_failure=True)
    assert result.exit_code != 0
    assert 'has not been undone' in result.output


def test_redo_with_user_changes(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('User initial setup')

    invoker.run(['track', 'start'])

    ai_file = project_dir / 'ai_code.py'
    ai_file.write_text('def ai_function():\n    pass\n')

    invoker.run(['track', 'stop', '--prompt', 'Create AI function'])

    invoker.run(['undo', '1'])

    commits_after_undo = get_commits(db_path)
    undo_commit_count = len(commits_after_undo)

    user_file = project_dir / 'user_changes.txt'
    user_file.write_text('Some user modifications after undo')

    invoker.run(['redo', '1'])

    commits_after_redo = get_commits(db_path)
    assert len(commits_after_redo) == undo_commit_count + 2

    task = get_task_with_revert(db_path, 1)
    assert task[4] is None
    assert task[5] is False


def test_redo_multiple_times_fails(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('User initial setup')

    invoker.run(['track', 'start'])

    test_file = project_dir / 'code.py'
    test_file.write_text('def function():\n    pass\n')

    invoker.run(['track', 'stop', '--prompt', 'Add function'])

    invoker.run(['undo', '1'])

    invoker.run(['redo', '1'])

    result = invoker.run(['redo', '1'], expect_failure=True)
    assert result.exit_code != 0
    assert 'has not been undone' in result.output


def test_undo_redo_cycle(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('User initial setup')

    invoker.run(['track', 'start'])

    test_file = project_dir / 'cycle.py'
    test_file.write_text('def cycle_test():\n    return "test"\n')

    invoker.run(['track', 'stop', '--prompt', 'Cycle test'])

    task_initial = get_task_with_revert(db_path, 1)
    assert task_initial[5] is False

    invoker.run(['undo', '1'])

    task_after_undo = get_task_with_revert(db_path, 1)
    assert task_after_undo[5] is True

    invoker.run(['redo', '1'])

    task_after_redo = get_task_with_revert(db_path, 1)
    assert task_after_redo[5] is False

    invoker.run(['undo', '1'])

    task_after_second_undo = get_task_with_revert(db_path, 1)
    assert task_after_second_undo[5] is True

    invoker.run(['redo', '1'])

    task_final = get_task_with_revert(db_path, 1)
    assert task_final[5] is False


def test_redo_specific_task_among_multiple(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    for i in range(1, 4):
        user_file = project_dir / f'user_{i}.txt'
        user_file.write_text(f'User setup {i}')

        invoker.run(['track', 'start'])

        task_file = project_dir / f'task_{i}.py'
        task_file.write_text(f'def task_{i}():\n    pass\n')

        invoker.run(['track', 'stop', '--prompt', f'Task {i}'])

    invoker.run(['undo', '1'])

    invoker.run(['undo', '2'])

    task_1 = get_task_with_revert(db_path, 1)
    task_2 = get_task_with_revert(db_path, 2)
    task_3 = get_task_with_revert(db_path, 3)

    assert task_1[5] is True
    assert task_2[5] is True
    assert task_3[5] is False

    invoker.run(['redo', '2'])

    task_1 = get_task_with_revert(db_path, 1)
    task_2 = get_task_with_revert(db_path, 2)
    task_3 = get_task_with_revert(db_path, 3)

    assert task_1[5] is True
    assert task_2[5] is False
    assert task_3[5] is False

    invoker.run(['redo', '1'])

    task_1 = get_task_with_revert(db_path, 1)
    task_2 = get_task_with_revert(db_path, 2)
    task_3 = get_task_with_revert(db_path, 3)

    assert task_1[5] is False
    assert task_2[5] is False
    assert task_3[5] is False
