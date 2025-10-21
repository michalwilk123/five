from pathlib import Path
import traceback

from click.testing import CliRunner

from five.cli.main import cli
from five.core.config import get_db_path, get_project_config_path
from five.managers.db_manager import DatabaseManager
from five.utils import NOOP_LOG

from .helpers import ensure_tables_exist, get_commits, verify_git_commit_exists


def run_setup(runner: CliRunner, config_path: Path):
    result = runner.invoke(cli, ['setup', '--config', str(config_path)])
    if result.exit_code != 0:
        print('\n=== SETUP FAILED ===')
        print(f'Exit code: {result.exit_code}')
        print(f'Output: {result.output}')
        if result.exception:
            print(f'Exception: {result.exception}')
            traceback.print_exception(
                type(result.exception), result.exception, result.exception.__traceback__
            )
    assert result.exit_code == 0
    return result


def run_init(runner: CliRunner, project_path: Path | str, config_path: Path):
    result = runner.invoke(
        cli,
        [
            'init',
            '--project',
            str(project_path),
            '--global-config',
            str(config_path),
            '--no-interactive',
        ],
    )
    if result.exit_code != 0:
        print('\n=== INIT FAILED ===')
        print(f'Exit code: {result.exit_code}')
        print(f'Output: {result.output}')
        if result.exception:
            print(f'Exception: {result.exception}')
            traceback.print_exception(
                type(result.exception), result.exception, result.exception.__traceback__
            )
    assert result.exit_code == 0
    return result


def test_init_basic(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        result = run_init(runner, project_dir, isolated_config_dir)

        assert 'initialized successfully' in result.output

        assert isolated_config_dir.exists()
        assert isolated_config_dir.is_dir()

        db_path = get_db_path(isolated_config_dir)
        assert db_path.exists()


def test_init_creates_sqlite_tables(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        run_init(runner, project_dir, isolated_config_dir)

        db_path = get_db_path(isolated_config_dir)

        ensure_tables_exist(db_path, ['CompletedTask', 'Commit', 'Project'])


def test_init_creates_checkpoint_repo(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        run_init(runner, project_dir, isolated_config_dir)

        db_path = get_db_path(isolated_config_dir)
        db_manager = DatabaseManager(NOOP_LOG, db_path)
        db_manager.connect(create_tables=False)

        project_path_str = str(project_dir.resolve())
        project = db_manager.get_project_by_path(project_path_str)
        project_config_dir = get_project_config_path(isolated_config_dir, project.name)

        checkpoint_git_dir = project_config_dir / '.git'
        assert checkpoint_git_dir.exists()
        assert checkpoint_git_dir.is_dir()


def test_init_already_initialized_error(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        run_init(runner, project_dir, isolated_config_dir)

        result_second = runner.invoke(
            cli,
            [
                'init',
                '--project',
                str(project_dir),
                '--global-config',
                str(isolated_config_dir),
                '--no-interactive',
            ],
        )

        assert result_second.exit_code != 0
        assert 'already initialized' in result_second.output


def test_init_with_verbose_option(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)

        result = runner.invoke(
            cli,
            [
                'init',
                '--verbose',
                '--project',
                str(project_dir),
                '--global-config',
                str(isolated_config_dir),
                '--no-interactive',
            ],
        )

        assert result.exit_code == 0
        assert 'Initializing project at' in result.output
        assert 'Creating project entry in database' in result.output


def test_init_with_existing_files_creates_initial_user_commit(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        file1 = project_dir / 'readme.txt'
        file1.write_text('Initial project setup')

        file2 = project_dir / 'src' / 'main.py'
        file2.parent.mkdir(parents=True)
        file2.write_text('def main():\n    pass\n')

        file3 = project_dir / 'config.json'
        file3.write_text('{"version": "1.0"}')

        run_setup(runner, isolated_config_dir)
        result = run_init(runner, project_dir, isolated_config_dir)

        assert result.exit_code == 0
        assert 'initialized successfully' in result.output

        db_path = get_db_path(isolated_config_dir)
        db_manager = DatabaseManager(NOOP_LOG, db_path)
        db_manager.connect(create_tables=False)

        project_path_str = str(project_dir.resolve())
        project = db_manager.get_project_by_path(project_path_str)
        project_config_dir = get_project_config_path(isolated_config_dir, project.name)

        commits = get_commits(db_path)
        assert len(commits) == 1
        assert commits[0][2] == 'user'

        assert verify_git_commit_exists(project_dir, project_config_dir, 'five:1')


def test_init_with_existing_git_repo_does_not_track_project_git(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        project_git_dir = project_dir / '.git'
        project_git_dir.mkdir()
        (project_git_dir / 'config').write_text('[core]\n\trepositoryformatversion = 0\n')
        (project_git_dir / 'HEAD').write_text('ref: refs/heads/main\n')

        file1 = project_dir / 'app.py'
        file1.write_text('print("hello")\n')

        file2 = project_dir / 'data.txt'
        file2.write_text('some data')

        run_setup(runner, isolated_config_dir)
        result = run_init(runner, project_dir, isolated_config_dir)

        assert result.exit_code == 0
        assert 'initialized successfully' in result.output

        db_path = get_db_path(isolated_config_dir)
        db_manager = DatabaseManager(NOOP_LOG, db_path)
        db_manager.connect(create_tables=False)

        project_path_str = str(project_dir.resolve())
        project = db_manager.get_project_by_path(project_path_str)
        project_config_dir = get_project_config_path(isolated_config_dir, project.name)

        from five.managers.git_manager import GitManager

        git_manager = GitManager(NOOP_LOG, project_config_dir / '.git', project_dir)
        result = git_manager.run(['ls-files'])
        tracked_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

        assert '.git' not in tracked_files
        assert '.git/config' not in tracked_files
        assert '.git/HEAD' not in tracked_files

        assert 'app.py' in tracked_files
        assert 'data.txt' in tracked_files
