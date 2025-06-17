import glob
import os
import subprocess


class FilePassageGenerator:
    def __init__(
        self,
        root_dir: str,
        globs: list[str],
        passage_length: int = 500,
        overlap: int = 100,
        numbered: bool = False,
    ):
        self.root_dir = root_dir
        self.globs = globs
        self.passage_length = passage_length
        self.overlap = overlap
        self.numbered = numbered

    def get_files(self) -> list[str]:
        files = []
        for pattern in self.globs:
            full_pattern = os.path.join(self.root_dir, pattern)
            files.extend(glob.glob(full_pattern, recursive=True))
        return files

    def generate_passages(self) -> list[tuple[str, str]]:
        passages = []
        for file_path in self.get_files():
            with open(file_path, "r", encoding="utf-8") as f:
                content = ""

                for line_number, line in enumerate(f.readlines(), 1):
                    if self.numbered:
                        content += f"{line_number}|{line}"
                    else:
                        content += line

            start = 0
            while start < len(content):
                end = min(start + self.passage_length, len(content))
                passage = content[start:end]
                passages.append((file_path, passage))
                start = end - self.overlap

        return passages


def get_last_commit_hash(repo_path: str, filename: str) -> str | None:
    original_dir = os.getcwd()
    try:
        os.chdir(repo_path)

        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--follow", "--", filename],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = result.stdout.strip()
        return commit_hash if commit_hash else None
    finally:
        os.chdir(original_dir)
