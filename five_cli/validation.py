from __future__ import annotations

from pathlib import Path
from typing import Callable

from five_cli.core.config import get_db_path
from five_cli.managers.db_manager import DatabaseManager


class FiveValidationError(Exception):
    """Raised when validation of inputs or environment fails in Five CLI."""


Errors = list[FiveValidationError]


class FiveValidator:
    def __init__(self, raises: bool, on_errors: Callable[[Errors], None] | None):
        self._errors: Errors = []
        self._project_path: Path | None = None
        self._config_path: Path | None = None
        self._raises = raises
        self._on_errors = on_errors

    def project_path_exists(self, project_path: Path) -> FiveValidator:
        self._project_path = project_path
        if not project_path.exists():
            self._errors.append(FiveValidationError(f'Project path does not exist: {project_path}'))
        elif not project_path.is_dir():
            self._errors.append(
                FiveValidationError(f'Project path is not a directory: {project_path}')
            )
        return self

    def config_path_exists(self, config_path: Path) -> FiveValidator:
        self._config_path = config_path
        if not config_path.exists():
            self._errors.append(FiveValidationError(f'Config path does not exist: {config_path}'))
        elif not config_path.is_dir():
            self._errors.append(
                FiveValidationError(f'Config path is not a directory: {config_path}')
            )
        return self

    def setup_exists(self, config_path: Path) -> FiveValidator:
        self._config_path = config_path
        db_path = get_db_path(config_path)
        if not db_path.exists():
            self._errors.append(
                FiveValidationError(f'Five is not set up at {config_path}. Run "five setup" first.')
            )
        return self

    def setup_does_not_exist(self, config_path: Path) -> FiveValidator:
        self._config_path = config_path
        if config_path.exists():
            db_path = get_db_path(config_path)
            if db_path.exists():
                self._errors.append(
                    FiveValidationError(
                        f'Five is already set up at {config_path}. Remove it first to reinitialize.'
                    )
                )
        return self

    def state_file_exists(self, state_file_path: Path) -> FiveValidator:
        if not state_file_path.exists():
            self._errors.append(
                FiveValidationError('No active tracking session. Run "five track start" first.')
            )
        return self

    def state_file_does_not_exist(self, state_file_path: Path) -> FiveValidator:
        if state_file_path.exists():
            self._errors.append(
                FiveValidationError(
                    'Tracking session already active. Run "five track stop" or "five track cancel" first.'
                )
            )
        return self

    def project_not_initialized(self, project_path: Path, config_path: Path) -> FiveValidator:
        self._project_path = project_path
        self._config_path = config_path

        db_manager = DatabaseManager(config_path, None)
        db_manager.connect(create_tables=False)

        project_path_str = str(project_path.resolve())
        existing_project = db_manager.get_project_by_path(project_path_str)
        if existing_project:
            self._errors.append(
                FiveValidationError(f'Project at {project_path} is already initialized in five')
            )
        return self

    def execute(self) -> bool:
        if not self._errors:
            return True

        if self._on_errors is not None:
            self._on_errors(self._errors)

        if self._raises:
            raise ExceptionGroup('Multiple errors occurred', self._errors)

        return False
