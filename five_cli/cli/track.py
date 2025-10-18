from pathlib import Path

import click

from five_cli.cli.utils import handle_cli_errors, build_validation_on_errors, runtime_command
from five_cli.handlers import track_cancel_handler, track_start_handler, track_stop_handler
from five_cli.utils import parse_json_array
from five_cli.validation import FiveValidator
from five_cli.managers import ClickContextManager


@click.group()
@runtime_command
def track(ctx: click.Context):
    """Track AI assistant interactions and code changes."""
    pass


@track.command()
@click.pass_context
def start(ctx: click.Context):
    """Mark the point where the AI assistant prompt begins."""
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    # Validate without raising; print via on_errors
    validator = FiveValidator(
        raises=False, on_errors=build_validation_on_errors('five track start')
    ) \
        .state_file_does_not_exist(config_path / 'state')
    if not validator.execute():
        raise click.ClickException('Validation failed. See errors above.')

    with handle_cli_errors('start tracking'):
        commit_hash = track_start_handler(project_path, config_path, logger)
    if commit_hash:
        click.echo(f'Created user commit: {commit_hash[:8]}')
    click.echo('Entered Five interface')


@track.command()
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
@click.pass_context
def stop(
    ctx: click.Context,
    prompt: str,
    temperature: float | None,
    model_name: str | None,
    references: str,
):
    """Mark the point where the AI assistant completes its task."""
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    # Validate without raising; print via on_errors
    validator = FiveValidator(
        raises=False, on_errors=build_validation_on_errors('five track stop')
    ) \
        .state_file_exists(config_path / 'state')
    if not validator.execute():
        raise click.ClickException('Validation failed. See errors above.')

    try:
        reference_ids = parse_json_array(references, '--references', int)
    except ValueError as e:
        raise click.ClickException(str(e))

    with handle_cli_errors('stop tracking'):
        commit_hash = track_stop_handler(
            project_path,
            config_path,
            logger,
            prompt,
            temperature,
            model_name,
            reference_ids,
        )
    click.echo(f'Created assistant commit: {commit_hash[:8]}')
    click.echo('Exited Five interface')


@track.command()
@click.pass_context
def cancel(ctx: click.Context):
    """Cancel the current tracking session without saving."""
    context_manager = ClickContextManager.prepare_context(ctx)
    project_path: Path = context_manager.get_project_path()
    config_path: Path = context_manager.get_config_path()
    logger = context_manager.get_logger()

    # Validate without raising; print via on_errors
    validator = FiveValidator(
        raises=False, on_errors=build_validation_on_errors('five track cancel')
    ) \
        .state_file_exists(config_path / 'state')
    if not validator.execute():
        raise click.ClickException('Validation failed. See errors above.')

    with handle_cli_errors('cancel tracking'):
        track_cancel_handler(project_path, config_path, logger)
    click.echo('Cancelled tracking session')
