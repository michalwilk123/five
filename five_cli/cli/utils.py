from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Callable, Iterator, TypeVar

import click

from five_cli.validation import FiveValidationError, FiveValidator
from five_cli.utils import LogFunction
from five_cli.core.config import get_config_root, get_project_identifier
from five_cli.managers import ClickContextManager


def _extract_exception_messages(exc: BaseException) -> list[str]:
    """Flatten ExceptionGroup (or single exception) to a list of messages."""
    if isinstance(exc, ExceptionGroup):
        messages: list[str] = []
        for inner in exc.exceptions:
            messages.extend(_extract_exception_messages(inner))
        return messages
    return [str(exc)]


T = TypeVar('T')


@contextmanager
def handle_cli_errors(action: str) -> Iterator[None]:
    """Wrap handler invocation to map common errors to Click exceptions."""

    try:
        yield
    except click.ClickException:
        raise
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # pragma: no cover - catch-all guard
        raise click.ClickException(f'Failed to {action}: {exc}') from exc


def build_validation_on_errors(command_hint: str) -> Callable[[list[BaseException]], None]:
    """Create an on_errors callback that logs a summary and bullet list.

    This is intended for CLI validators to report errors via the provided logger
    before the validator raises, ensuring users see a friendly, contextual log.
    """

    def on_errors(errors: list[BaseException]) -> None:
        # Flatten messages and strip whitespace
        messages: list[str] = []
        for err in errors:
            text = str(err).strip()
            if not text:
                continue
            # Split multiline errors into separate bullets
            for line in text.splitlines():
                line = line.strip()
                if line:
                    messages.append(line)

        count = len(messages) if messages else len(errors)
        # Always print validation errors to the CLI output, regardless of verbose flag
        click.echo(f'{count} Validation errors in {command_hint} command:')
        for msg in messages if messages else (str(e) for e in errors):
            click.echo(f'- {msg}')

    return on_errors


def create_click_logger(verbose: bool) -> LogFunction:
    def logger(message: str):
        if verbose:
            click.echo(message)

    return logger


def runtime_command(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator adding common runtime options and context preparation.

    Applies project/config/verbose options, validates environment, and prepares
    Click context with `ClickContextManager` before invoking the wrapped function.
    """

    @click.option('--project', type=click.Path(exists=True, file_okay=False, path_type=Path), default=None, help='Path to the project directory to track (defaults to current directory)')
    @click.option('--config', type=click.Path(file_okay=False, path_type=Path), default=None, help='Path to the five config directory (defaults to XDG standard path)')
    @click.option('--verbose', '-v', is_flag=True, default=False, help='Enable verbose logging')
    @click.pass_context
    @wraps(func)
    def wrapper(ctx: click.Context, verbose: bool, project: Path | None, config: Path | None, *args, **kwargs):
        # Ensure context obj exists
        ctx.ensure_object(dict)

        # If already prepared (e.g., by a parent group), reuse existing context
        if isinstance(ctx.obj, dict) and all(k in ctx.obj for k in ('project_path', 'config_path', 'logger')):
            return func(ctx, *args, **kwargs)

        project_path: Path = project if project is not None else Path.cwd()
        config_root: Path = get_config_root()
        default_project_config = config_root / get_project_identifier(project_path)
        config_path: Path = config if config is not None else default_project_config
        logger = create_click_logger(verbose)

        # Validate base parameters and setup for runtime commands
        validator = FiveValidator(raises=False, on_errors=build_validation_on_errors('five')) \
            .project_path_exists(project_path) \
            .config_path_exists(config_path) \
            .setup_exists(config_path)
        if not validator.execute():
            # When non-raising, explicitly fail with a ClickException carrying summarised message
            raise click.ClickException('Validation failed. See errors above.')

        ClickContextManager.prepare(ctx, project_path, config_path, logger)
        return func(ctx, *args, **kwargs)

    return wrapper  # type: ignore[return-value]
