import hashlib
import os
from pathlib import Path


def get_config_root() -> Path:
    xdg_config_home = os.getenv('XDG_CONFIG_HOME')
    if xdg_config_home:
        return Path(xdg_config_home) / 'five'

    return Path.home() / '.config' / 'five'


def get_project_identifier(project_path: Path) -> str:
    absolute_path = project_path.resolve()
    path_hash = hashlib.sha256(str(absolute_path).encode()).hexdigest()[:16]
    return path_hash


def get_db_path(global_config_path: Path) -> Path:
    return global_config_path / 'data.db'


def ensure_global_config_path(global_config_path: Path):
    global_config_path.mkdir(parents=True, exist_ok=True)


def get_project_config_path(config_root: Path, project_name: str) -> Path:
    return config_root / project_name
