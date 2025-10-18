"""Manager package exposing concrete manager implementations."""

from .common import BaseManager
from .db_manager import DatabaseManager
from .git_manager import GitManager, get_git_config_value, init_git_repo
from .state_manager import StateManager
from .context_manager import ClickContextManager

__all__ = [
    'BaseManager',
    'DatabaseManager',
    'GitManager',
    'StateManager',
    'ClickContextManager',
    'get_git_config_value',
    'init_git_repo',
]
