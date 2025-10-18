from pathlib import Path

import click

from five_cli.cli.utils import handle_cli_errors, runtime_command
from five_cli.handlers import undo_handler
from five_cli.managers import ClickContextManager


@click.command()
@click.argument('task_id', type=int)
@runtime_command
def undo(ctx: click.Context, task_id: int):
    """Undo a completed task by reverting its changes."""
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    with handle_cli_errors('undo task'):
        revert_hash = undo_handler(project_path, config_path, task_id, logger)
    click.echo(f'Task {task_id} has been reverted')
    click.echo(f'Revert commit: {revert_hash[:8]}')
