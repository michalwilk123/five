from __future__ import annotations

from pathlib import Path
import shutil
import tempfile

from click.testing import CliRunner
import pytest

from five_cli.cli.main import cli
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
                '--config',
                str(isolated_config_dir),
                '--no-interactive',
            ],
        )
        assert init_result.exit_code == 0

        invoker = TestInvoker(runner, project_dir, isolated_config_dir)
        yield project_dir, runner, isolated_config_dir, invoker
