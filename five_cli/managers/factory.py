from pathlib import Path

from five_cli.core.config import get_db_path
from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager
from five_cli.managers.state_manager import StateManager
from five_cli.utils import LogFunction


class ManagerFactory:
    def __init__(
        self,
        project_path: Path,
        global_config_path: Path,
        project_config_path: Path,
        logger: LogFunction,
    ):
        self.project_path = project_path
        self.global_config_path = global_config_path
        self.project_config_path = project_config_path
        self.logger = logger

    def create_git_manager(self) -> GitManager:
        git_path = self.project_config_path / '.git'
        work_tree = self.project_path
        return GitManager(self.logger, git_path, work_tree)

    def create_db_manager(self) -> DatabaseManager:
        db_path = get_db_path(self.global_config_path)
        return DatabaseManager(self.logger, db_path)

    def create_state_manager(self) -> StateManager:
        state_file = self.project_config_path / 'state'
        return StateManager(self.logger, state_file)
