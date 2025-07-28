import os
import sys

from indexer.core import (
    build_and_save_index_config,
    update_and_save_index_config,
    update_index_config,
)
from indexer.search import BackgroundSearch, regex_search_symbols
from indexer.utils import get_symbol_text, load_index_config_from_file, IndexConfig
from indexer.folding import fold_file, get_code_range

Range = tuple[int, int]
LineContent = tuple[int, str]


def parse_file_spec(file_spec: str) -> tuple[str, Range | None]:
    """Parse file specification with optional line range."""
    if ":" not in file_spec:
        return file_spec, None

    file_path, range_spec = file_spec.rsplit(":", 1)
    start, end = range_spec.split("-", 1)
    return file_path, (int(start), int(end))


class Indexer:
    def __init__(self, project_path: str, language: str, config: IndexConfig):
        self.project_path = os.path.abspath(project_path)
        self.language = language.lower()
        self.config_path = self._get_config_path()
        self.config = config

    def _get_config_path(self) -> str:
        config_dir = os.path.join(self.project_path, ".five")
        return os.path.join(config_dir, f"index_{self.language}.json")

    def create_index(self, show_progress: bool = False) -> str:
        """Create a new index for the project."""
        config_dir = os.path.join(self.project_path, ".five")
        config_path = build_and_save_index_config(
            self.project_path, self.language, config_dir, show_progress
        )
        return config_path

    def update_index(
        self, show_progress: bool = False, dry_run: bool = False
    ) -> tuple[bool, dict, str | None]:
        """Update the existing index. Returns (has_changes, file_changes, updated_path)."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Index file not found: {self.config_path}")

        if dry_run:
            old_config = self.config
            _, has_changes, file_changes = update_index_config(
                old_config, self.project_path, show_progress
            )
            return has_changes, file_changes, None
        else:
            updated_path, has_changes, file_changes = update_and_save_index_config(
                self.project_path, self.config_path, show_progress
            )
            return has_changes, file_changes, updated_path

    def search_symbols(self, query: str = "", max_results: int = 50) -> list:
        """Search for symbols in the index."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Index file not found: {self.config_path}")

        config = self.config or load_index_config_from_file(self.config_path)
        return regex_search_symbols(config, symbol_query=query, max_results=max_results)

    def get_symbol_text(self, result) -> str:
        """Get the text content of a symbol."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Index file not found: {self.config_path}")

        config = self.config or load_index_config_from_file(self.config_path)
        return get_symbol_text(result, config.symbols, self.project_path)

    def create_background_search(self) -> BackgroundSearch:
        """Create a background search instance for interactive use."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Index file not found: {self.config_path}")

        config = self.config or load_index_config_from_file(self.config_path)
        return BackgroundSearch(config)


def create_index(
    project_path: str, language: str, config: IndexConfig, show_progress: bool = False
) -> str:
    """Create a new index for the project."""
    indexer = Indexer(project_path, language, config)
    return indexer.create_index(show_progress)


def update_index(
    project_path: str,
    language: str,
    config: IndexConfig,
    show_progress: bool = False,
    dry_run: bool = False,
) -> tuple[bool, dict, str | None]:
    """Update the existing index."""
    indexer = Indexer(project_path, language, config)
    return indexer.update_index(show_progress, dry_run)


def search_symbols(
    project_path: str, language: str, query: str = "", max_results: int = 50
) -> list:
    """Search for symbols in the index."""
    indexer = Indexer(project_path, language)
    return indexer.search_symbols(query, max_results)


def get_config_path(project_path: str, language: str) -> str:
    """Get the path to the index configuration file."""
    config_dir = os.path.join(project_path, ".five")
    return os.path.join(config_dir, f"index_{language.lower()}.json")


def format_file_changes(file_changes: dict) -> str:
    """Format file changes for display."""
    op_map = {
        "added": "A",
        "deleted": "D",
        "modified": "M",
    }
    lines = []
    for file_path, op in file_changes.items():
        op_symbol = op_map.get(op.value, op.value)
        lines.append(f"{op_symbol} {file_path}")
    return "\n".join(lines)


def format_search_results(
    results,
    max_display: int = 10,
    show_code: bool = False,
    project_path: str = "",
    config=None,
) -> str:
    """Format search results for display."""
    if not results:
        return "No results found"

    lines = [f"Found {len(results)} results:"]

    for i, result in enumerate(results[:max_display]):
        symbol = result.symbol
        score = result.combined_score
        symbol_type = f" [{symbol.symbol_type.value}]" if symbol.symbol_type else ""
        lines.append(
            f"{i + 1:2d}. {symbol.name} ({score:.2f}) - {symbol.file_path}:{symbol.line_number}{symbol_type}"
        )

        if show_code and config:
            try:
                code_content = get_symbol_text(result, config.symbols, project_path)
                if code_content.strip():
                    lines.append("   " + "─" * 60)
                    for line in code_content.rstrip().split("\n"):
                        lines.append(f"   {line}")
                    lines.append("   " + "─" * 60)
            except Exception as e:
                lines.append(f"   Error reading code: {e}")

    return "\n".join(lines)
