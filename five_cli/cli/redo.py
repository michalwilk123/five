from pathlib import Path

import click

from five_cli.cli.decorators import five_command
from five_cli.cli.utils import handle_cli_errors
from five_cli.handlers import redo_handler


@click.command()
@click.argument('task_id', type=int)
@five_command(project_path=True, global_config_path=True, project_config_path=True, logger=True)
def redo(
    ctx: click.Context,
    task_id: int,
    *,
    project_path: Path,
    global_config_path: Path,
    project_config_path: Path,
    logger,
):
    """Redo a previously undone task by reverting the revert commit."""

    with handle_cli_errors('redo task'):
        redo_hash = redo_handler(
            project_path, global_config_path, project_config_path, task_id, logger
        )
    click.echo(f'Task {task_id} has been redone')
    click.echo(f'Redo commit: {redo_hash[:8]}')
