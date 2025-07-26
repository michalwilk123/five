import os
from datetime import datetime, timezone

from tqdm import tqdm

from indexer.files import (
    FileOperation,
    get_file_hashes,
    get_files_for_indexing,
    get_merkle_diff,
    get_merkle_hashes,
)
from indexer.parsers.python import parse as parse_python
from indexer.utils import (
    IndexConfig,
    SymbolDeclaration,
    index_config_to_json,
    json_to_index_config,
)


def _process_files_with_parser(
    project_path: str,
    file_paths: list[str],
    language: str,
    show_progress: bool,
    description: str,
) -> list[SymbolDeclaration]:
    all_symbols = []
    language_config = {"python": {"extensions": [".py"], "parser": parse_python}}

    config = language_config.get(language.lower())
    assert config, f"Unsupported language: {language}"

    language_files = [
        f for f in file_paths if any(f.endswith(ext) for ext in config["extensions"])
    ]

    for file_path in tqdm(language_files, desc=description, disable=not show_progress):
        symbols = config["parser"](project_path, file_path)
        all_symbols.extend(symbols)

    return all_symbols


def process_project(
    project_path: str, language: str = "python", show_progress: bool = False
) -> list[SymbolDeclaration]:
    files = get_files_for_indexing(project_path)
    return _process_files_with_parser(
        project_path, files, language, show_progress, f"Processing {language} files"
    )


def process_specific_files(
    project_path: str,
    file_paths: list[str],
    language: str = "python",
    show_progress: bool = False,
) -> list[SymbolDeclaration]:
    return _process_files_with_parser(
        project_path,
        file_paths,
        language,
        show_progress,
        f"Processing changed {language} files",
    )


def update_index_config(
    old_config: IndexConfig, project_path: str, show_progress: bool = False
) -> tuple[IndexConfig, bool, dict[str, "FileOperation"]]:
    new_file_hashes = get_file_hashes(project_path, show_progress)
    new_merkle_hashes = get_merkle_hashes(new_file_hashes)

    file_changes = get_merkle_diff(
        old_config.merkle_hashes,
        new_merkle_hashes,
        old_config.file_hashes,
        new_file_hashes,
    )

    changed_files = list(file_changes.keys())

    if not changed_files:
        return old_config, False, file_changes

    new_symbols = old_config.symbols.copy()

    for file_path in changed_files:
        operation = file_changes[file_path]

        if operation == FileOperation.DELETED:
            new_symbols = [s for s in new_symbols if s.file_path != file_path]
        elif operation in (FileOperation.ADDED, FileOperation.MODIFIED):
            new_symbols = [s for s in new_symbols if s.file_path != file_path]
            file_symbols = process_specific_files(
                project_path, [file_path], old_config.language, show_progress
            )
            new_symbols.extend(file_symbols)

    last_updated = datetime.now(timezone.utc).isoformat()

    return (
        IndexConfig(
            symbols=new_symbols,
            file_hashes=new_file_hashes,
            merkle_hashes=new_merkle_hashes,
            language=old_config.language,
            last_updated=last_updated,
        ),
        True,
        file_changes,
    )


def build_index_config(
    project_path: str, language: str, show_progress: bool = False
) -> IndexConfig:
    symbols = process_project(project_path, language, show_progress)
    file_hashes = get_file_hashes(project_path, show_progress)
    merkle_hashes = get_merkle_hashes(file_hashes)
    last_updated = datetime.now(timezone.utc).isoformat()

    return IndexConfig(
        symbols=symbols,
        file_hashes=file_hashes,
        merkle_hashes=merkle_hashes,
        language=language,
        last_updated=last_updated,
    )


def save_index_config_to_file(
    config: IndexConfig, config_path: str, language: str, overwrite: bool = True
) -> str:
    sorted_symbols = sorted(config.symbols, key=lambda s: (s.file_path, s.line_number))
    sorted_config = IndexConfig(
        symbols=sorted_symbols,
        file_hashes=config.file_hashes,
        merkle_hashes=config.merkle_hashes,
        language=config.language,
        last_updated=config.last_updated,
    )
    json_content = index_config_to_json(sorted_config)

    filename = f"index_{language.lower()}.json"
    full_path = os.path.join(config_path, filename)

    if not overwrite and os.path.exists(full_path):
        raise FileExistsError(f"File {full_path} already exists and overwrite=False")

    os.makedirs(config_path, exist_ok=True)
    with open(full_path, "w") as f:
        f.write(json_content)

    return full_path


def build_and_save_index_config(
    project_path: str, language: str, config_path: str, show_progress: bool = False
) -> str:
    config = build_index_config(project_path, language, show_progress)
    return save_index_config_to_file(config, config_path, language)


def load_index_config(config_path: str) -> IndexConfig:
    with open(config_path, "r") as f:
        json_content = f.read()
    return json_to_index_config(json_content)


def update_and_save_index_config(
    project_path: str, config_file_path: str, show_progress: bool = False
) -> tuple[str, bool, dict[str, "FileOperation"]]:
    old_config = load_index_config(config_file_path)
    updated_config, has_changes, file_changes = update_index_config(
        old_config, project_path, show_progress
    )

    config_dir = os.path.dirname(config_file_path)
    config_path = save_index_config_to_file(
        updated_config, config_dir, old_config.language
    )
    return config_path, has_changes, file_changes
