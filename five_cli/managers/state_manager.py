from __future__ import annotations

from pathlib import Path

from five_cli.managers.common import BaseManager


class StateManager(BaseManager):
    def __init__(
        self,
        five_dir: Path,
        state_file: Path | None = None,
        logger=None,
    ):
        super().__init__(five_dir, logger)
        self.state_file = state_file or (self.five_dir / 'state')

    @property
    def state_path(self) -> Path:
        return self.state_file

    def load(self) -> str | None:
        if not self.state_path.exists():
            return None
        content = self.state_path.read_text().strip()
        self._log(f'Loaded state: {content}')
        return content

    def save(self, state: str):
        self._log(f'Saving state: {state}')
        self.state_path.write_text(state)

    def clear(self):
        if self.state_path.exists():
            self._log('Clearing state file')
            self.state_path.unlink()

    def is_started(self) -> bool:
        return self.load() == 'start'

    def require_started(self):
        if not self.is_started():
            raise ValueError(
                'Track is not started. State file does not exist or content is not "start". '
                'Use "five track start" first.'
            )

    def require_not_started(self):
        if self.is_started():
            raise ValueError(
                'Track is already started. Use "five track stop" or "five track cancel" first.'
            )
