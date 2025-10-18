import hashlib
import os
from pathlib import Path


def get_config_root() -> Path:
    if custom_dir := os.getenv('FIVE_CONFIG_DIR'):
        return Path(custom_dir)

    xdg_config_home = os.getenv('XDG_CONFIG_HOME')
    if xdg_config_home:
        return Path(xdg_config_home) / 'five'

    return Path.home() / '.config' / 'five'


def get_project_identifier(project_path: Path) -> str:
    absolute_path = project_path.resolve()
    path_hash = hashlib.sha256(str(absolute_path).encode()).hexdigest()[:16]
    return path_hash


# removed: resolve_project_config_dir(project_path: Path) -> Path


def get_db_path(five_dir: Path) -> Path:
    return five_dir / 'data.db'


def ensure_five_dir(five_dir: Path):
    five_dir.mkdir(parents=True, exist_ok=True)
