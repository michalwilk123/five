from pathlib import Path

import click

from five.cli.decorators import five_command
from five.cli.utils import build_validation_on_errors, handle_cli_errors
from five.handlers import init_handler, setup_handler
from five.utils import LogFunction
from five.validation import FiveValidator


@click.command()
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Prompt to run setup if not already done (default: True)',
)
@five_command(project_path=True, logger=True, global_config_path=True)
def init(
    ctx: click.Context,
    interactive: bool,
    *,
    project_path: Path,
    global_config_path: Path,
    logger: LogFunction,
):
    """
    Initialize a project for Five tracking.
    Creates project-specific config and git repository.
    """
    # Validate basic inputs (do not enforce setup existence here)
    FiveValidator(
        raises=click.ClickException, on_errors=build_validation_on_errors('five init')
    ).project_path_exists(project_path).config_path_exists(global_config_path).execute()

    # Ensure setup exists or perform setup if interactive
    setup_check = FiveValidator(raises=False, on_errors=None).setup_exists(global_config_path)
    if not setup_check.execute():
        if interactive:
            # Ask for confirmation and run setup
            if click.confirm('Five is not set up. Would you like to set it up now?', default=True):
                with handle_cli_errors('set up five'):
                    setup_handler(global_config_path, logger)
            else:
                raise click.ClickException(
                    f'Five is not set up at {global_config_path}. '
                    f'Run "five setup" first or use --interactive.'
                )
        else:
            raise click.ClickException(
                f'Five is not set up at {global_config_path}. '
                f'Run "five setup" first or use --interactive.'
            )

    # Ensure project is not already initialized
    FiveValidator(
        raises=click.ClickException, on_errors=build_validation_on_errors('five init')
    ).project_not_initialized(project_path, global_config_path).execute()

    with handle_cli_errors('initialize project'):
        project_name = init_handler(
            project_path,
            global_config_path,
            logger,
        )
    click.echo(f'Project "{project_name}" initialized successfully')
