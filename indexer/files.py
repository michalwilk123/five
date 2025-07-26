import hashlib
import os
import subprocess
from enum import Enum

from tqdm import tqdm


def filter_unignored_files(worktree_path: str, files_list: list[str]):
    """
    This function would not make much sense if'd
    use git list-files, but we somehow need to check single
    files when updating the index
    """
    if not files_list:
        return []

    original_cwd = os.getcwd()
    os.chdir(worktree_path)

    try:
        result = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            input="\n".join(files_list),
            capture_output=True,
            text=True,
            check=False,
        )

        ignored_files = (
            set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()
        )

        non_ignored_files = [f for f in files_list if f not in ignored_files]

        return non_ignored_files

    finally:
        os.chdir(original_cwd)


def get_project_files(project_path: str):
    original_cwd = os.getcwd()
    os.chdir(project_path)

    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )

        files = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return [f for f in files if f]  # Remove empty strings

    except subprocess.CalledProcessError as e:
        # Handle case where project_path is not a git repository
        return []
    finally:
        os.chdir(original_cwd)


def filter_file_language(file_path: str):
    # This could be done with a more sophisticated approach
    return file_path.endswith((".py", ".js", ".ts", ".tsx", ".jsx"))


def get_files_for_indexing(project_path: str) -> list[str]:
    all_files = get_project_files(project_path)
    supported_files = (f for f in all_files if filter_file_language(f))

    non_empty_files = []
    for file_path in supported_files:
        full_path = os.path.join(project_path, file_path)
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            non_empty_files.append(file_path)

    return sorted(non_empty_files)


class FileOperation(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


def get_file_hash(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def get_file_hashes(project_path: str, show_progress: bool = False) -> dict[str, str]:
    files = get_files_for_indexing(project_path)
    iterator = tqdm(files, desc="Calculating file hashes", disable=not show_progress)

    return {
        file_path: get_file_hash(os.path.join(project_path, file_path))
        for file_path in iterator
    }


def get_merkle_hashes(file_hashes: dict[str, str]) -> dict[str, str]:
    merkle_hashes = {}

    for file_path, file_hash in file_hashes.items():
        dir_path = os.path.dirname(file_path) or "."
        if dir_path not in merkle_hashes:
            merkle_hashes[dir_path] = hashlib.md5().hexdigest()
        merkle_hashes[dir_path] = hashlib.md5(
            (merkle_hashes[dir_path] + file_hash).encode()
        ).hexdigest()

    return merkle_hashes


def get_merkle_diff(
    old_merkle: dict[str, str],
    new_merkle: dict[str, str],
    old_files: dict[str, str],
    new_files: dict[str, str],
) -> dict[str, FileOperation]:
    changed_dirs = set()

    for dir_path in set(old_merkle.keys()) | set(new_merkle.keys()):
        if old_merkle.get(dir_path) != new_merkle.get(dir_path):
            changed_dirs.add(dir_path)

    file_changes = {}

    for file_path in set(old_files.keys()) | set(new_files.keys()):
        dir_path = os.path.dirname(file_path) or "."
        if dir_path in changed_dirs:
            if file_path not in old_files:
                file_changes[file_path] = FileOperation.ADDED
            elif file_path not in new_files:
                file_changes[file_path] = FileOperation.DELETED
            elif old_files[file_path] != new_files[file_path]:
                file_changes[file_path] = FileOperation.MODIFIED

    return file_changes
