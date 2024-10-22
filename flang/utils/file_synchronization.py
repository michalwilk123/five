import dataclasses
import filecmp
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Set, Tuple


@dataclasses.dataclass
class SyncResult:
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    backup_zip_path: str | None = None


class DirectorySynchronizer:
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)

    def _get_relative_paths(self, directory: Path) -> Set[str]:
        """Get all relative file paths in a directory."""
        return {
            os.path.relpath(os.path.join(root, file), directory)
            for root, _, files in os.walk(directory)
            for file in files
        }

    def _compare_files(self, rel_path: str) -> bool:
        """Compare two files and return True if they are the same."""
        source_file = self.source_dir / rel_path
        target_file = self.target_dir / rel_path

        if not source_file.exists() or not target_file.exists():
            return False

        return filecmp.cmp(source_file, target_file, shallow=False)

    def _create_backup_zip(self, files_to_backup: List[str]) -> str:
        """Create a zip file containing the specified files."""
        # Create a temporary directory for the zip file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(temp_dir, f"backup_{timestamp}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_backup:
                full_path = self.target_dir / file_path
                if full_path.exists():
                    zipf.write(full_path, file_path)

        return zip_path

    def synchronize(self) -> SyncResult:
        """
        Synchronize target directory with source directory and backup changes.
        """
        # Get all files in both directories
        source_files = self._get_relative_paths(self.source_dir)
        target_files = self._get_relative_paths(self.target_dir)

        # Find differences
        added_files = list(source_files - target_files)
        deleted_files = list(target_files - source_files)
        common_files = source_files & target_files

        # Check for modified files
        modified_files = [f for f in common_files if not self._compare_files(f)]

        # If there are files to be deleted or modified, create backup
        files_to_backup = deleted_files + modified_files
        backup_zip_path = None
        if files_to_backup:
            backup_zip_path = self._create_backup_zip(files_to_backup)

        # Perform synchronization
        for file_path in added_files + modified_files:
            source_file = self.source_dir / file_path
            target_file = self.target_dir / file_path

            # Create directory if it doesn't exist
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source_file, target_file)

        # Remove deleted files
        for file_path in deleted_files:
            target_file = self.target_dir / file_path
            target_file.unlink(missing_ok=True)

            # Remove empty directories
            for parent in target_file.parents:
                if parent == self.target_dir:
                    break
                try:
                    parent.rmdir()  # Will only remove if directory is empty
                except OSError:
                    break

        return SyncResult(
            added_files=added_files,
            modified_files=modified_files,
            deleted_files=deleted_files,
            backup_zip_path=backup_zip_path,
        )
