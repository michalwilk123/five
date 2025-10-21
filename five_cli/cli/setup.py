from pathlib import Path

import click

from five_cli.cli.utils import build_validation_on_errors, create_click_logger, handle_cli_errors
from five_cli.core.config import get_config_root
from five_cli.handlers import setup_handler
from five_cli.validation import FiveValidator


@click.command()
@click.option(
    '--config',
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        'Path to the global five config directory where database is stored '
        '(defaults to XDG: ~/.config/five)'
    ),
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    default=False,
    help='Enable verbose logging',
)
def setup(config: Path | None, verbose: bool):
    global_config_path = config or get_config_root()
    logger = create_click_logger(verbose)

    FiveValidator(
        raises=click.ClickException, on_errors=build_validation_on_errors('five setup')
    ).setup_does_not_exist(global_config_path).execute()

    with handle_cli_errors('set up five'):
        result_path = setup_handler(global_config_path, logger)
    click.echo(f'Five set up successfully at {result_path}')
