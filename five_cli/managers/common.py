from __future__ import annotations

from pathlib import Path
from typing import Protocol

from five_cli.utils import NOOP_LOG, LogFunction


class SupportsClose(Protocol):
    def close(self) -> None: ...


class BaseManager:
    def __init__(self, five_dir: Path, logger: LogFunction | None = None):
        self.five_dir = five_dir
        self.logger = logger
        self._log = self.logger or NOOP_LOG

    def cleanup(self):
        """Optional hook for managers needing cleanup."""


class LazyResourceManager(BaseManager):
    _resource: SupportsClose | None = None

    def get_resource(self) -> SupportsClose:
        raise NotImplementedError

    def cleanup(self):
        if self._resource is not None:
            try:
                self._resource.close()
            finally:
                self._resource = None


class ManagerFactory:
    """Factory responsible for constructing Five service managers."""

    def __init__(self, project_path: Path, config_path: Path, logger: LogFunction | None = None):
        self.project_path = project_path
        self.config_path = config_path
        self.logger = logger
        self._five_dir: Path | None = None

    def _resolve_five_dir(self) -> Path:
        if self._five_dir is None:
            five_dir = self.config_path

            if not five_dir.exists():
                raise ValueError(
                    f'Five is not initialized. Run "five init" first. Looking for: {five_dir}'
                )

            git_dir = five_dir / '.git'
            if not git_dir.exists():
                raise ValueError(f'Git directory not found: {git_dir}')

            self._five_dir = five_dir

        return self._five_dir

    def create_git_manager(self) -> BaseManager:
        from five_cli.managers.git_manager import GitManager

        five_dir = self._resolve_five_dir()
        return GitManager(five_dir, logger=self.logger)

    def create_db_manager(self) -> BaseManager:
        from five_cli.managers.db_manager import DatabaseManager

        five_dir = self._resolve_five_dir()
        return DatabaseManager(five_dir, logger=self.logger)

    def create_state_manager(self) -> BaseManager:
        from five_cli.managers.state_manager import StateManager

        five_dir = self._resolve_five_dir()
        return StateManager(five_dir, logger=self.logger)
