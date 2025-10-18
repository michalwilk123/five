from pathlib import Path

import click

from five_cli.cli.utils import handle_cli_errors, build_validation_on_errors
from five_cli.core.config import get_config_root
from five_cli.handlers import init_handler
from five_cli.validation import FiveValidator
from five_cli.managers import ClickContextManager


@click.command()
@click.option('--project', type=click.Path(file_okay=False, path_type=Path), default=None, help='Path to the project directory to track (defaults to current directory)')
@click.option(
    '--config',
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help='Path to the five config directory (defaults to XDG standard path)',
)
@click.option('--verbose', '-v', is_flag=True, default=False, help='Enable verbose logging')
@click.option(
    '--interactive/--no-interactive',
    default=True,
    help='Prompt to run setup if not already done (default: True)',
)
@click.pass_context
def init(ctx: click.Context, project: Path | None, config: Path | None, verbose: bool, interactive: bool):
    from five_cli.cli.utils import create_click_logger

    ctx.ensure_object(dict)
    project_path: Path = project if project is not None else Path.cwd()
    logger = create_click_logger(verbose)

    actual_config_path = config if config is not None else get_config_root()

    # Perform validation without raising; print errors via on_errors
    validator = FiveValidator(
        raises=False, on_errors=build_validation_on_errors('five init')
    ) \
        .project_path_exists(project_path) \
        .project_not_initialized(project_path, actual_config_path)
    if not validator.execute():
        raise click.ClickException('Validation failed. See errors above.')

    with handle_cli_errors('initialize project'):
        project_name = init_handler(
            project_path,
            actual_config_path,
            interactive,
            logger,
        )
    click.echo(f'Project "{project_name}" initialized successfully')
