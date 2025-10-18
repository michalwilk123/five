from __future__ import annotations

from enum import Enum, auto

from pony.orm import db_session

from five_cli.managers.db_manager import DatabaseManager


class SyncOperation(Enum):
    APPLIED = auto()
    REVERTED = auto()


@db_session
def build_commit_state_map(db_manager: DatabaseManager) -> dict[int, bool]:
    all_commits = db_manager.get_all_commits()
    commit_state = {}

    for commit in all_commits:
        commit_id = commit['id']
        commit_state[commit_id] = True

        if commit['type'] == 'assistant' and commit['completed_task_id']:
            task = db_manager.get_completed_task_entity_by_id(commit['completed_task_id'])
            if task and task.revert_commit_id:
                commit_state[commit_id] = False

    return commit_state


def get_commits_up_to(db_manager: DatabaseManager, end_commit_id: int) -> list[dict]:
    all_commits = db_manager.get_all_commits()
    return [c for c in all_commits if c['id'] <= end_commit_id]


def determine_operations(
    commits: list[dict],
    commit_state_map: dict[int, bool],
) -> list[SyncOperation]:
    operations = []
    for commit in commits:
        commit_id = commit['id']
        is_applied = commit_state_map.get(commit_id, True)
        if is_applied:
            operations.append(SyncOperation.APPLIED)
        else:
            operations.append(SyncOperation.REVERTED)
    return operations


def analyze_sync_state(
    db_manager: DatabaseManager,
    end_commit_id: int,
) -> tuple[list[dict], list[SyncOperation]]:
    commits = get_commits_up_to(db_manager, end_commit_id)
    commit_state_map = build_commit_state_map(db_manager)
    operations = determine_operations(commits, commit_state_map)

    return commits, operations


def get_target_commit_hash(commits: list[dict], target_commit_id: int) -> str | None:
    for commit in commits:
        if commit['id'] == target_commit_id:
            return commit['hash']
    return None
