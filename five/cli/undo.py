from pathlib import Path

import click

from five.cli.decorators import five_command
from five.cli.utils import handle_cli_errors
from five.handlers import undo_handler


@click.command()
@click.argument('task_id', type=int)
@five_command(project_path=True, global_config_path=True, project_config_path=True, logger=True)
def undo(
    ctx: click.Context,
    task_id: int,
    *,
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    logger,
):
    """Undo a completed task by reverting its changes."""

    with handle_cli_errors('undo task'):
        revert_hash = undo_handler(
            project_path, global_config_path, project_config_path, task_id, logger
        )
    click.echo(f'Task {task_id} has been reverted')
    click.echo(f'Revert commit: {revert_hash[:8]}')
