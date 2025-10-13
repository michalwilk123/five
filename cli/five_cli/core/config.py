import os


def get_five_paths(five_config_path: str):
    five_path = os.path.dirname(five_config_path)
    git_dir = os.path.join(five_path, '.git')
    return five_path, git_dir


def detect_if_five_initialized(five_config_path: str, project_path: str):
    _, git_dir = get_five_paths(five_config_path)
    return os.path.exists(git_dir)
