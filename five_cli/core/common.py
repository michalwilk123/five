import json

from five_cli.managers.db_manager import DatabaseManager
from five_cli.managers.git_manager import GitManager
from five_cli.utils import LogFunction


def connect_database(db_manager: DatabaseManager, log: LogFunction):
    db_manager.connect(create_tables=False)
    log('Connected to database')


def get_diff_for_commit(
    db_manager: DatabaseManager,
    git_manager: GitManager,
    commit_id: int,
    log: LogFunction,
) -> str | None:
    commit = db_manager.get_commit_by_id(commit_id)
    if not commit:
        log(f'Commit {commit_id} not found')
        return None

    commit_hash = commit.get('hash')
    if not commit_hash:
        log(f'No hash found for commit {commit_id}')
        return None

    log(f'Getting diff for commit {commit_hash}')
    return git_manager.get_diff(commit_hash)


def format_json_output(data: dict | list, pretty_print: bool) -> str:
    if pretty_print:
        return json.dumps(data, indent=2, default=str)
    return json.dumps(data, default=str)
