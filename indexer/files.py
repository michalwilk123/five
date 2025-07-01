import hashlib
import os
import subprocess
import sys
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


# def get_file_chunks(
#     project_path: str, chunk_size: int = 500, overlap: int = 10
# ) -> list[tuple[str, int, str]]:
#     files = get_files_for_indexing(project_path)
#     chunks = []

#     for file_path in files:
#         full_path = os.path.join(project_path, file_path)

#         try:
#             with open(full_path, "r", encoding="utf-8") as f:
#                 lines = f.readlines()

#                 for i in range(0, len(lines), chunk_size - overlap):
#                     chunk_lines = lines[i : i + chunk_size]
#                     chunk_content = "".join(chunk_lines)
#                     start_line = i + 1  # Line numbers are 1-indexed

#                     chunks.append((file_path, start_line, chunk_content))

#         except (IOError, UnicodeDecodeError):
#             # Skip files that can't be read or decoded
#             continue

#     return chunks

# def create_chunk_with_line_numbers(chunk: str, start_line_number: int) -> str:
#     return "\n".join(
#         f"{start_line_number + i} | {line}" for i, line in enumerate(chunk.splitlines())
#     )


# def create_project_directory_structure(project_path: str):
#     """
#     Command that list not empty tracked directories in a git repository
#     tree --fromfile <(git ls-files -z | perl -0 -ne 'chomp; if (-s $_) { $dir = $_; $dir =~ s!^(.*)/[^/]*$!$1!; $dir = "." if $dir eq $_; $d{$dir} = 1 } END { print join("\n", keys %d) }') -d
#     """
#     ...


# def get_non_empty_not_gitignored_dirs():
#     try:
#         repo_root = subprocess.check_output(
#             ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, text=True
#         ).strip()
#     except subprocess.CalledProcessError:
#         return  # Exit silently if not in a Git repo

#     # Fetch Git-tracked files (null-delimited)
#     try:
#         files = subprocess.check_output(
#             ["git", "ls-files", "-z"], cwd=repo_root, stderr=subprocess.DEVNULL
#         ).split(b"\x00")[:-1]
#     except subprocess.CalledProcessError:
#         return

#     # Process files to collect directories
#     fs_encoding = sys.getfilesystemencoding()
#     dirs = set()

#     for f_bytes in files:
#         try:
#             file_path = f_bytes.decode(fs_encoding, errors="surrogateescape")
#             abs_path = os.path.join(repo_root, file_path)

#             # Skip directories/symlinks and check file size
#             if not os.path.isfile(abs_path) or os.path.getsize(abs_path) == 0:
#                 continue

#             # Extract directory and add to set
#             dir_path = os.path.dirname(file_path)
#             dirs.add(dir_path if dir_path else ".")  # Handle root directory

#         except OSError:  # Skip inaccessible files
#             continue

#     return sorted(dirs)


# def tree_from_file_list(file_list: list[str], project_path: str):
#     if not file_list:
#         return ""

#     original_cwd = os.getcwd()

#     try:
#         os.chdir(project_path)

#         file_content = "\n".join(file_list)
#         result = subprocess.run(
#             ["tree", "--fromfile", ".", "-d"],
#             input=file_content,
#             capture_output=True,
#             text=True,
#             check=True,
#         )

#         return result.stdout

#     except subprocess.CalledProcessError as e:
#         # Handle case where tree command fails or is not available
#         return f"Error executing tree command: {e}"
#     except FileNotFoundError:
#         return "Error: tree command not found. Please install tree utility."
#     finally:
#         os.chdir(original_cwd)


# def get_project_structure(project_path: str):
#     return tree_from_file_list(get_project_files(project_path), project_path)


# def get_definition(file_path: str, line: int, column: int):
#     ...

# def get_references(file_path: str, line: int, column: int):
#     ...
