import pytest

from five.core.config import get_db_path
from five.managers.db_manager import DatabaseManager
from five.utils import NOOP_LOG
from five.validation import FiveValidator


@pytest.fixture
def make_validator():
    captured_errors: list[Exception] = []

    def factory(raises: bool = True):
        def on_errors(errors: list[Exception]):
            captured_errors.extend(errors)

        return FiveValidator(raises=raises, on_errors=on_errors), captured_errors

    return factory


def test_validate_project_path_exists_success(tmp_path, make_validator):
    project_dir = tmp_path / 'project'
    project_dir.mkdir()

    validator, captured = make_validator()
    validator.project_path_exists(project_dir).execute()


def test_validate_project_path_exists_fails_when_not_exists(tmp_path, make_validator):
    project_dir = tmp_path / 'nonexistent'

    validator, captured = make_validator()
    validator.project_path_exists(project_dir)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Project path does not exist' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_project_path_exists_fails_when_file(tmp_path, make_validator):
    project_file = tmp_path / 'file.txt'
    project_file.write_text('test')

    validator, captured = make_validator()
    validator.project_path_exists(project_file)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Project path is not a directory' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_config_path_exists_success(tmp_path, make_validator):
    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    validator, _ = make_validator()
    validator.config_path_exists(config_dir).execute()


def test_validate_config_path_exists_fails_when_not_exists(tmp_path, make_validator):
    config_dir = tmp_path / 'nonexistent'

    validator, captured = make_validator()
    validator.config_path_exists(config_dir)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Config path does not exist' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_config_path_exists_fails_when_file(tmp_path, make_validator):
    config_file = tmp_path / 'file.txt'
    config_file.write_text('test')

    validator, captured = make_validator()
    validator.config_path_exists(config_file)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Config path is not a directory' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_setup_exists_success(tmp_path, make_validator):
    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    db_path = get_db_path(config_dir)
    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=True)

    validator, _ = make_validator()
    validator.setup_exists(config_dir).execute()


def test_validate_setup_exists_fails_when_no_db(tmp_path, make_validator):
    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    validator, captured = make_validator()
    validator.setup_exists(config_dir)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Five is not set up' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_setup_does_not_exist_success_when_dir_not_exists(tmp_path, make_validator):
    config_dir = tmp_path / 'config'

    validator, _ = make_validator()
    validator.setup_does_not_exist(config_dir).execute()


def test_validate_setup_does_not_exist_success_when_no_db(tmp_path, make_validator):
    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    validator, _ = make_validator()
    validator.setup_does_not_exist(config_dir).execute()


def test_validate_setup_does_not_exist_fails_when_db_exists(tmp_path, make_validator):
    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    db_path = get_db_path(config_dir)
    db_path.write_text('')

    validator, captured = make_validator()
    validator.setup_does_not_exist(config_dir)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Five is already set up' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_state_file_exists_success(tmp_path, make_validator):
    state_file = tmp_path / 'state'
    state_file.write_text('start')

    validator, _ = make_validator()
    validator.state_file_exists(state_file).execute()


def test_validate_state_file_exists_fails_when_not_exists(tmp_path, make_validator):
    state_file = tmp_path / 'state'

    validator, captured = make_validator()
    validator.state_file_exists(state_file)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'No active tracking session' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_state_file_does_not_exist_success(tmp_path, make_validator):
    state_file = tmp_path / 'state'

    validator, _ = make_validator()
    validator.state_file_does_not_exist(state_file).execute()


def test_validate_state_file_does_not_exist_fails_when_exists(tmp_path, make_validator):
    state_file = tmp_path / 'state'
    state_file.write_text('start')

    validator, captured = make_validator()
    validator.state_file_does_not_exist(state_file)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'Tracking session already active' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validate_project_not_initialized_success(tmp_path, make_validator):
    from five.managers.db_manager import DatabaseManager

    project_dir = tmp_path / 'project'
    project_dir.mkdir()

    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    db_path = get_db_path(config_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text('')

    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=True)

    validator, _ = make_validator()
    validator.project_not_initialized(project_dir, config_dir).execute()


def test_validate_project_not_initialized_fails_when_already_initialized(tmp_path, make_validator):
    from five.managers.db_manager import DatabaseManager

    project_dir = tmp_path / 'project'
    project_dir.mkdir()

    config_dir = tmp_path / 'config'
    config_dir.mkdir()

    db_path = get_db_path(config_dir)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text('')

    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=True)
    db_manager.create_project(
        name='test_project',
        path=str(project_dir.resolve()),
        git_repo_path=None,
        author='Test Author',
    )

    validator, captured = make_validator()
    validator.project_not_initialized(project_dir, config_dir)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 1
    assert 'already initialized in five' in str(exc_info.value.exceptions[0])
    assert len(captured) == 1


def test_validator_pipeline_collects_multiple_errors(tmp_path, make_validator):
    nonexistent_project = tmp_path / 'nonexistent_project'
    nonexistent_config = tmp_path / 'nonexistent_config'

    validator, captured = make_validator()
    validator.project_path_exists(nonexistent_project).config_path_exists(nonexistent_config)

    with pytest.raises(ExceptionGroup) as exc_info:
        validator.execute()

    assert len(exc_info.value.exceptions) == 2
    assert len(captured) == 2
    errors_str = ''.join(str(e) for e in exc_info.value.exceptions)
    assert 'Project path does not exist' in errors_str
    assert 'Config path does not exist' in errors_str


def test_validator_pipeline_with_print_function(tmp_path, make_validator):
    nonexistent_project = tmp_path / 'nonexistent_project'

    validator, captured_errors = make_validator()
    validator.project_path_exists(nonexistent_project)

    with pytest.raises(ExceptionGroup):
        validator.execute()

    assert len(captured_errors) == 1
    assert 'Project path does not exist' in str(captured_errors[0])
