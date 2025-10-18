from __future__ import annotations

from pathlib import Path

import click

from five_cli.utils import LogFunction


class ClickContextManager:
    """Simple holder for CLI context resources.

    This class intentionally does not perform any validation.
    """

    def __init__(self, project_path: Path, config_path: Path, logger: LogFunction):
        self._project_path = project_path
        self._config_path = config_path
        self._logger = logger

    @classmethod
    def from_context(cls, context: dict) -> 'ClickContextManager':
        project_path: Path = context['project_path']
        config_path: Path = context['config_path']
        logger: LogFunction = context['logger']
        return cls(project_path, config_path, logger)

    @classmethod
    def prepare(
        cls, ctx: click.Context, project_path: Path, config_path: Path, logger: LogFunction
    ) -> click.Context:
        ctx.obj['project_path'] = project_path
        ctx.obj['config_path'] = config_path
        ctx.obj['logger'] = logger
        return ctx

    @classmethod
    def prepare_context(cls, ctx: click.Context) -> 'ClickContextManager':
        return cls.from_context(ctx.obj)

    def get_project_path(self) -> Path:
        return self._project_path

    def get_config_path(self) -> Path:
        return self._config_path

    def get_logger(self) -> LogFunction:
        return self._logger
