from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Callable

from five.core.config import get_db_path
from five.managers.db_manager import DatabaseManager
from five.utils import NOOP_LOG


class FiveValidationError(Exception):
    """Raised when validation of inputs or environment fails in Five CLI."""


Errors = list[FiveValidationError]


def _get_project_from_db(project_path: Path, global_config_path: Path):
    db_path = get_db_path(global_config_path)
    db_manager = DatabaseManager(NOOP_LOG, db_path)
    db_manager.connect(create_tables=False)

    project_path_str = str(project_path.resolve())
    return db_manager.get_project_by_path(project_path_str)


class FiveValidator:
    def __init__(self, raises: bool | type[Exception], on_errors: Callable[[Errors], None] | None):
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
                    'Tracking session already active. '
                    'Run "five track stop" or "five track cancel" first.'
                )
            )
        return self

    def project_not_initialized(self, project_path: Path, config_path: Path) -> FiveValidator:
        self._project_path = project_path
        self._config_path = config_path

        existing_project = _get_project_from_db(project_path, config_path)
        if existing_project:
            self._errors.append(
                FiveValidationError(f'Project at {project_path} is already initialized in five')
            )
        return self

    def project_initialized(self, project_path: Path, config_path: Path) -> FiveValidator:
        self._project_path = project_path
        self._config_path = config_path

        existing_project = _get_project_from_db(project_path, config_path)
        if not existing_project:
            project_path_str = str(project_path.resolve())
            self._errors.append(
                FiveValidationError(
                    f'Project not found in database for path: {project_path_str}. '
                    f'Run "five init" first.'
                )
            )
        return self

    def project_is_git_repository(self, project_path: Path) -> FiveValidator:
        self._project_path = project_path
        git_dir = project_path / '.git'
        if not git_dir.exists():
            self._errors.append(
                FiveValidationError(
                    f'Project at {project_path} is not a git repository. '
                    f'Initialize git first with "git init".'
                )
            )
            return self

        try:
            subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=str(project_path),
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            self._errors.append(
                FiveValidationError(
                    f'Project at {project_path} has an invalid git repository. '
                    f'Ensure .git directory is properly initialized.'
                )
            )

        return self

    def execute(self) -> bool:
        if not self._errors:
            return True

        if self._on_errors is not None:
            self._on_errors(self._errors)

        if self._raises is False:
            return False
        elif self._raises is True:
            raise ExceptionGroup('Multiple errors occurred', self._errors)
        else:
            exc_group = ExceptionGroup('Multiple errors occurred', self._errors)
            error_messages = '\n'.join(str(e) for e in self._errors)
            raise self._raises(error_messages) from exc_group
