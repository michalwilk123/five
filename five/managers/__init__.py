"""Manager package exposing concrete manager implementations."""

from .base import BaseManager
from .db_manager import DatabaseManager
from .factory import ManagerFactory
from .git_manager import GitManager, get_git_config_value, init_git_repo_in_dir
from .state_manager import StateManager

__all__ = [
    'BaseManager',
    'DatabaseManager',
    'GitManager',
    'StateManager',
    'ManagerFactory',
    'get_git_config_value',
    'init_git_repo_in_dir',
]
