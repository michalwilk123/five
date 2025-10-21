from contextlib import contextmanager
from typing import Callable, Iterator

import click

from five_cli.utils import LogFunction


def _extract_exception_messages(exc: BaseException) -> list[str]:
    """Flatten ExceptionGroup (or single exception) to a list of messages."""
    if isinstance(exc, ExceptionGroup):
        messages: list[str] = []
        for inner in exc.exceptions:
            messages.extend(_extract_exception_messages(inner))
        return messages
    return [str(exc)]


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
