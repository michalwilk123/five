from pathlib import Path

import click

from five.cli.decorators import five_command
from five.cli.utils import build_validation_on_errors, handle_cli_errors
from five.handlers import track_cancel_handler, track_start_handler, track_stop_handler
from five.utils import parse_json_array
from five.validation import FiveValidator


@click.group()
def track():
    """Track AI assistant interactions and code changes."""
    pass


@track.command()
@five_command(project_config_path=True, project_path=True, global_config_path=True, logger=True)
def start(
    ctx: click.Context,
    *,
    project_path: Path,
    project_config_path: Path,
    global_config_path: Path,
    logger,
):
    """Mark the point where the AI assistant prompt begins."""
    FiveValidator(
        raises=click.ClickException, on_errors=build_validation_on_errors('five track start')
    ).state_file_does_not_exist(project_config_path / 'state').execute()

    with handle_cli_errors('start tracking'):
        commit_hash = track_start_handler(
            project_path, global_config_path, project_config_path, logger
        )
    if commit_hash:
        click.echo(f'Created user commit: {commit_hash[:8]}')
    click.echo('Entered Five interface')


@track.command()
@five_command(project_config_path=True, project_path=True, global_config_path=True, logger=True)
@click.option(
    '-p',
    '--prompt',
    required=True,
    help='Prompt content for the completed task',
)
@click.option(
    '--temperature',
    type=float,
    default=None,
    help='Model temperature used for the response',
)
@click.option(
    '--model-name',
    default=None,
    help='Model name used for the response',
)
@click.option(
    '--references',
    default='[]',
    help='List of reference task IDs as JSON array (e.g., [1,2])',
)
@click.option(
    '--note',
    default=None,
    help='Optional note for the commit',
)
def stop(
    ctx: click.Context,
    *,
    project_path: Path,
    project_config_path: Path,
    global_config_path: Path,
    logger,
    prompt: str,
    temperature: float | None,
    model_name: str | None,
    references: str,
    note: str | None,
):
    """Mark the point where the AI assistant completes its task."""
    FiveValidator(
        raises=click.ClickException, on_errors=build_validation_on_errors('five track stop')
    ).state_file_exists(project_config_path / 'state').execute()

    try:
        reference_ids = parse_json_array(references, '--references', int)
    except ValueError as e:
        raise click.ClickException(str(e))

    with handle_cli_errors('stop tracking'):
        commit_hash = track_stop_handler(
            project_path,
            global_config_path,
            project_config_path,
            logger,
            prompt,
            temperature,
            model_name,
            reference_ids,
            note,
        )
    click.echo(f'Created assistant commit: {commit_hash[:8]}')
    click.echo('Exited Five interface')


@track.command()
@five_command(project_config_path=True, project_path=True, global_config_path=True, logger=True)
def cancel(
    ctx: click.Context,
    *,
    project_path: Path,
    project_config_path: Path,
    global_config_path: Path,
    logger,
):
    """Cancel an active tracking session without creating a commit."""
    FiveValidator(
        raises=click.ClickException, on_errors=build_validation_on_errors('five track cancel')
    ).state_file_exists(project_config_path / 'state').execute()

    with handle_cli_errors('cancel tracking'):
        track_cancel_handler(project_path, global_config_path, project_config_path, logger)
    click.echo('Cancelled tracking session')


@track.command()
@five_command(project_config_path=True, project_path=True, global_config_path=True, logger=True)
def status(
    ctx: click.Context,
    *,
    project_path: Path,
    project_config_path: Path,
    global_config_path: Path,
    logger,
):
    """Check if a tracking session is currently active."""
    state_file = project_config_path / 'state'
    if state_file.exists():
        click.echo('Tracking session is active')
    else:
        click.echo('No active tracking session')
