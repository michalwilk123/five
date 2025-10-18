from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from five_cli.cli.main import cli
from five_cli.core.config import get_db_path
from five_cli.managers.git_manager import GitManager

from .helpers import ensure_tables_exist


def run_setup(runner: CliRunner, config_path: Path):
    result = runner.invoke(cli, ['setup', '--config', str(config_path)])
    if result.exit_code != 0:
        print(f"\n=== SETUP FAILED ===")
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    assert result.exit_code == 0
    return result


def run_init(runner: CliRunner, project_path: Path | str, config_path: Path):
    result = runner.invoke(
        cli,
        [
            'init',
            '--project',
            str(project_path),
            '--config',
            str(config_path),
            '--no-interactive',
        ],
    )
    if result.exit_code != 0:
        print(f"\n=== INIT FAILED ===")
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    assert result.exit_code == 0
    return result


def verify_git_initial_commit(five_dir: Path):
    git_dir = five_dir / '.git'
    git_manager = GitManager(five_dir, git_dir)
    result = git_manager.run(['log', '--oneline'])
    log_output = result.stdout.strip()
    assert log_output, 'No commits found in git history'
    assert 'Initial commit by' in log_output


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

        git_dir = isolated_config_dir / '.git'
        assert git_dir.exists()


def test_init_creates_sqlite_tables(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        run_init(runner, project_dir, isolated_config_dir)

        db_path = get_db_path(isolated_config_dir)

        ensure_tables_exist(db_path, ['CompletedTask', 'Commit', 'Project'])


def test_init_creates_initial_commit(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        run_init(runner, project_dir, isolated_config_dir)

        verify_git_initial_commit(isolated_config_dir)


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
                '--config',
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
                '--config',
                str(isolated_config_dir),
                '--no-interactive',
            ],
        )

        assert result.exit_code == 0
        assert 'Initializing project at' in result.output
        assert 'Creating project entry in database' in result.output


def test_init_git_config_set_correctly(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        run_setup(runner, isolated_config_dir)
        run_init(runner, project_dir, isolated_config_dir)

        git_dir = isolated_config_dir / '.git'
        git_manager = GitManager(isolated_config_dir, git_dir)

        import subprocess

        try:
            git_manager.run(['config', 'core.excludesFile'])
            assert False, 'core.excludesFile should not be set'
        except subprocess.CalledProcessError:
            pass
