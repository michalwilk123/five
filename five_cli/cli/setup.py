from pathlib import Path

import click

from five_cli.cli.utils import handle_cli_errors, build_validation_on_errors
from five_cli.core.config import get_config_root
from five_cli.handlers import setup_handler
from five_cli.validation import FiveValidator


@click.command()
@click.option(
    '--config',
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help='Path to the five config directory (defaults to XDG standard path)',
)
@click.option('--verbose', '-v', is_flag=True, default=False, help='Enable verbose logging')
def setup(config: Path | None, verbose: bool):
    def logger(message: str):
        if verbose:
            click.echo(message)

    actual_config_path = config if config is not None else get_config_root()

    # Perform validation without raising; print errors via on_errors
    validator = FiveValidator(
        raises=False, on_errors=build_validation_on_errors('five setup')
    ) \
        .setup_does_not_exist(actual_config_path)
    if not validator.execute():
        raise click.ClickException('Validation failed. See errors above.')

    with handle_cli_errors('set up five'):
        result_path = setup_handler(actual_config_path, logger)
    click.echo(f'Five set up successfully at {result_path}')
