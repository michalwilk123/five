from pathlib import Path

import click

from five_cli.cli.utils import handle_cli_errors, runtime_command
from five_cli.handlers import redo_handler
from five_cli.managers import ClickContextManager


@click.command()
@click.argument('task_id', type=int)
@runtime_command
def redo(ctx: click.Context, task_id: int):
    """Redo a previously undone task by reverting the revert commit."""
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    with handle_cli_errors('redo task'):
        redo_hash = redo_handler(project_path, config_path, task_id, logger)
    click.echo(f'Task {task_id} has been redone')
    click.echo(f'Redo commit: {redo_hash[:8]}')
