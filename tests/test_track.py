from five.core.config import get_db_path

from .helpers import (
    get_commit_by_hash,
    get_commits,
    get_task_by_id,
    read_state,
    verify_git_commit_exists,
)


def test_track_start_no_changes(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    result = invoker.run(['track', 'start'])

    assert 'Entered Five interface' in result.output

    assert read_state(project_config_path) == 'start'


def test_track_start_with_changes_creates_user_commit(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    test_file = project_dir / 'test_data.txt'
    test_file.write_text('Some test data')

    result = invoker.run(['track', 'start'])

    assert 'Created user commit:' in result.output
    assert 'Entered Five interface' in result.output

    assert read_state(project_config_path) == 'start'

    commits = get_commits(db_path)
    assert len(commits) == 1

    _, commit_hash, commit_type = commits[0]
    assert commit_type == 'user'
    assert verify_git_commit_exists(project_dir, project_config_path, 'five:1')

    commit_data = get_commit_by_hash(db_path, commit_hash)
    assert commit_data is not None
    assert commit_data[2] == 'user'


def test_track_full_cycle_start_stop(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_file = project_dir / 'user_changes.txt'
    user_file.write_text('User changes before AI')

    invoker.run(['track', 'start'])

    assert read_state(project_config_path) == 'start'

    new_file = project_dir / 'generated_code.py'
    new_file.write_text('def hello():\n    print("Hello from AI")\n')

    result_stop = invoker.run(
        [
            'track',
            'stop',
            '--prompt',
            'Generate hello function',
            '--model-name',
            'gpt-4',
            '--temperature',
            '0.7',
        ]
    )

    assert 'Created assistant commit:' in result_stop.output
    assert 'Exited Five interface' in result_stop.output

    assert read_state(project_config_path) is None

    commits = get_commits(db_path)
    assert len(commits) == 2

    _, user_commit_hash, user_commit_type = commits[0]
    assert user_commit_type == 'user'
    _, assistant_commit_hash, assistant_commit_type = commits[1]
    assert assistant_commit_type == 'assistant'
    assert verify_git_commit_exists(project_dir, project_config_path, 'five:1')
    assert verify_git_commit_exists(project_dir, project_config_path, 'five:2')

    commit_hash = assistant_commit_hash

    commit_data = get_commit_by_hash(db_path, commit_hash)
    assert commit_data is not None
    assert commit_data[2] == 'assistant'
    assert commit_data[3] is not None

    task_id = commit_data[3]
    task_data = get_task_by_id(db_path, task_id)
    assert task_data is not None
    assert task_data[1] == 2
    assert task_data[2] == 'Generate hello function'
    assert task_data[3] == 'gpt-4'


def test_track_start_stop_with_user_commit(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    initial_file = project_dir / 'user_changes.txt'
    initial_file.write_text('User made some changes')

    result_start = invoker.run(['track', 'start'])
    assert 'Created user commit:' in result_start.output

    commits_after_start = get_commits(db_path)
    assert len(commits_after_start) == 1
    assert commits_after_start[0][2] == 'user'

    ai_file = project_dir / 'ai_changes.txt'
    ai_file.write_text('AI made some changes')

    result_stop = invoker.run(['track', 'stop', '--prompt', 'Make AI changes'])

    assert 'Created assistant commit:' in result_stop.output

    commits_after_stop = get_commits(db_path)
    assert len(commits_after_stop) == 2
    assert commits_after_stop[0][2] == 'user'
    assert commits_after_stop[1][2] == 'assistant'

    assert verify_git_commit_exists(project_dir, project_config_path, 'five:1')
    assert verify_git_commit_exists(project_dir, project_config_path, 'five:2')


def test_track_cancel(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    invoker.run(['track', 'start'])

    assert read_state(project_config_path) == 'start'

    result_cancel = invoker.run(['track', 'cancel'])

    assert 'Cancelled tracking session' in result_cancel.output

    assert read_state(project_config_path) is None


def test_track_stop_without_start_fails(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    result = invoker.run(['track', 'stop', '--prompt', 'This should fail'], expect_failure=True)

    assert result.exit_code != 0
    assert 'No active tracking session' in result.output


def test_track_start_twice_fails(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    invoker.run(['track', 'start'])

    result = invoker.run(['track', 'start'], expect_failure=True)

    assert result.exit_code != 0
    assert 'Tracking session already active' in result.output


def test_track_cancel_without_start_fails(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    result = invoker.run(['track', 'cancel'], expect_failure=True)

    assert result.exit_code != 0
    assert 'No active tracking session' in result.output


def test_track_stop_with_references(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project
    db_path = get_db_path(global_config_path)

    user_file = project_dir / 'user_setup.txt'
    user_file.write_text('Initial user setup')

    invoker.run(['track', 'start'])

    file_1 = project_dir / 'task1.txt'
    file_1.write_text('Task 1')

    invoker.run(['track', 'stop', '--prompt', 'Task 1'])

    invoker.run(['track', 'start'])

    file_2 = project_dir / 'task2.txt'
    file_2.write_text('Task 2 referencing task 1')

    invoker.run(
        [
            'track',
            'stop',
            '--prompt',
            'Task 2 based on task 1',
            '--references',
            '[1]',
            '--note',
            'This is a test note for the commit',
        ]
    )

    commits = get_commits(db_path)
    assert len(commits) == 3

    assert commits[0][2] == 'user'
    assert commits[1][2] == 'assistant'
    assert commits[2][2] == 'assistant'

    task_2_commit = commits[2]
    task_2_commit_data = get_commit_by_hash(db_path, task_2_commit[1])
    task_2_id = task_2_commit_data[3]
    task_2 = get_task_by_id(db_path, task_2_id)
    assert task_2 is not None
    assert task_2[2] == 'Task 2 based on task 1'


def test_track_status_no_session(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    result = invoker.run(['track', 'status'])

    assert 'No active tracking session' in result.output


def test_track_status_active_session(initialized_project):
    project_dir, runner, global_config_path, project_config_path, invoker = initialized_project

    invoker.run(['track', 'start'])

    result = invoker.run(['track', 'status'])

    assert 'Tracking session is active' in result.output
