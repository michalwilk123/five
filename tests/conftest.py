from pathlib import Path
import shutil
import tempfile

from click.testing import CliRunner
import pytest

from five.cli.main import cli
from five.core.config import get_db_path, get_project_config_path
from five.managers.db_manager import DatabaseManager
from five.utils import NOOP_LOG

from .helpers import TestInvoker


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def isolated_config_dir():
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def initialized_project(runner, isolated_config_dir):
    with runner.isolated_filesystem() as td:
        project_dir = Path(td)

        setup_result = runner.invoke(cli, ['setup', '--config', str(isolated_config_dir)])
        assert setup_result.exit_code == 0

        init_result = runner.invoke(
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
        assert init_result.exit_code == 0

        db_path = get_db_path(isolated_config_dir)
        db_manager = DatabaseManager(NOOP_LOG, db_path)
        db_manager.connect(create_tables=False)

        project_path_str = str(project_dir.resolve())
        project = db_manager.get_project_by_path(project_path_str)
        project_config_path = get_project_config_path(isolated_config_dir, project.name)

        invoker = TestInvoker(runner, project_dir, project_config_path, isolated_config_dir)
        yield project_dir, runner, isolated_config_dir, project_config_path, invoker
