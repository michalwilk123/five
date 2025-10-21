from pathlib import Path

import click

from five.cli.decorators import five_command
from five.cli.utils import handle_cli_errors
from five.core.common import format_json_output
from five.handlers import handle_get_commits, handle_get_completed_tasks, handle_get_projects
from five.utils import LogFunction


@click.group()
def get():
    """Query and retrieve project data, tasks, and commits."""
    pass


@get.command()
@five_command(global_config_path=True, logger=True, project_config_path=True, project_path=True)
@click.argument('task_id', type=int, required=False)
@click.option('--pp', is_flag=True, default=False, help='Pretty print JSON output')
@click.option('--project-name', type=str, required=False, help='Filter by project name')
def completed_tasks(
    ctx: click.Context,
    global_config_path: Path,
    logger: LogFunction,
    task_id: int | None,
    project_name: str | None,
    pp: bool,
    project_path: Path,
    project_config_path: Path,
):
    """Retrieve completed AI assistant tasks. Optionally filter by task ID or project name."""
    with handle_cli_errors('get completed tasks'):
        result = handle_get_completed_tasks(
            project_path, global_config_path, project_config_path, logger, task_id, project_name
        )
        output = format_json_output(result, pp)
    click.echo(output)


@get.command()
@five_command(global_config_path=True, logger=True, project_config_path=True, project_path=True)
@click.argument('commit_id', type=int, required=False)
@click.option('--pp', is_flag=True, default=False, help='Pretty print JSON output')
@click.option('--project-name', type=str, required=False, help='Filter by project name')
def commits(
    ctx: click.Context,
    global_config_path: Path,
    logger: LogFunction,
    commit_id: int | None,
    project_name: str | None,
    pp: bool,
    project_path: Path,
    project_config_path: Path,
):
    """Retrieve tracked git commits. Optionally filter by commit ID or project name."""
    with handle_cli_errors('get commits'):
        result = handle_get_commits(
            project_path,
            global_config_path,
            project_config_path,
            logger,
            commit_id,
            project_name,
        )
        output = format_json_output(result, pp)
    click.echo(output)


@get.command()
@five_command(global_config_path=True, logger=True, project_config_path=True, project_path=True)
@click.argument('project_id', type=int, required=False)
@click.option('--pp', is_flag=True, default=False, help='Pretty print JSON output')
def projects(
    ctx: click.Context,
    global_config_path: Path,
    logger: LogFunction,
    project_id: int | None,
    pp: bool,
    project_path: Path,
    project_config_path: Path,
):
    """Retrieve information about projects."""
    with handle_cli_errors('get projects'):
        result = handle_get_projects(
            project_path, global_config_path, project_config_path, logger, project_id
        )
        output = format_json_output(result, pp)
    click.echo(output)
