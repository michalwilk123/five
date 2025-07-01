from tqdm import tqdm

from indexer.files import get_files_for_indexing
from indexer.parsers.python import parse as parse_python
from indexer.utils import SymbolDeclaration


def process_project(
    project_path: str, language: str = "python", show_progress: bool = False
) -> list[SymbolDeclaration]:
    files = get_files_for_indexing(project_path)
    all_symbols = []
    language_config = {"python": {"extensions": [".py"], "parser": parse_python}}

    config = language_config.get(language.lower())
    assert config, f"Unsupported language: {language}"

    language_files = [
        f for f in files if any(f.endswith(ext) for ext in config["extensions"])
    ]

    for file_path in tqdm(
        language_files, desc=f"Processing {language} files", disable=not show_progress
    ):
        symbols = config["parser"](project_path, file_path)
        all_symbols.extend(symbols)

    return all_symbols
