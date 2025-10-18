from pathlib import Path

import click

from five_cli.handlers import handle_get_commits, handle_get_completed_tasks
from five_cli.cli.utils import runtime_command, handle_cli_errors
from five_cli.managers import ClickContextManager


@click.group()
@runtime_command
def get(ctx: click.Context):
    pass


@get.command()
@click.argument('task_id', type=int, required=False)
@click.option('--pp', is_flag=True, default=False, help='Pretty print JSON output')
@click.pass_context
def completed_tasks(ctx: click.Context, task_id: int | None, pp: bool):
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    with handle_cli_errors('get completed tasks'):
        result = handle_get_completed_tasks(project_path, config_path, logger, task_id, pp)
    click.echo(result)


@get.command()
@click.argument('commit_id', type=int, required=False)
@click.option('--pp', is_flag=True, default=False, help='Pretty print JSON output')
@click.pass_context
def commits(ctx: click.Context, commit_id: int | None, pp: bool):
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    with handle_cli_errors('get commits'):
        result = handle_get_commits(project_path, config_path, logger, commit_id, pp)
    click.echo(result)
