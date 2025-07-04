#!/usr/bin/env python3
import argparse
import os
import sys
import threading
import time

from indexer.core import (
    build_and_save_index_config,
    load_index_config,
    update_and_save_index_config,
    update_index_config,
)
from indexer.search import BackgroundSearch


def get_config_path(project_path: str, language: str) -> str:
    config_dir = os.path.join(project_path, ".five")
    return os.path.join(config_dir, f"index_{language.lower()}.toml")


def create_index(project_path: str, language: str, show_progress: bool) -> None:
    config_dir = os.path.join(project_path, ".five")
    config_path = build_and_save_index_config(
        project_path, language, config_dir, show_progress
    )
    print(f"Index created: {config_path}")


def _print_file_changes(file_changes: dict) -> None:
    op_map = {
        "added": "A",
        "deleted": "D",
        "modified": "M",
    }
    for file_path, op in file_changes.items():
        print(f"{op_map.get(op.value, op.value)} {file_path}")


def _handle_changes(
    has_changes: bool, file_changes: dict, updated_path: str = None, dry_run: bool = False
) -> None:
    if has_changes:
        if dry_run:
            print("Changes detected:")
        _print_file_changes(file_changes)
        if dry_run:
            print("(dry run - no changes made)")
            sys.exit(1)
        else:
            print(f"Index updated: {updated_path}")
    else:
        print("no changes")


def update_index(
    project_path: str, language: str, show_progress: bool, dry_run: bool = False
) -> None:
    config_path = get_config_path(project_path, language)

    if not os.path.exists(config_path):
        print(f"Index file not found: {config_path}")
        print("Use 'create' command to build initial index")
        sys.exit(1)

    if dry_run:
        old_config = load_index_config(config_path)
        _, has_changes, file_changes = update_index_config(
            old_config, project_path, show_progress
        )
        _handle_changes(has_changes, file_changes, dry_run=True)
    else:
        updated_path, has_changes, file_changes = update_and_save_index_config(
            project_path, config_path, show_progress
        )
        _handle_changes(has_changes, file_changes, updated_path, dry_run=False)


def _display_results(results, max_display: int = 10):
    if not results:
        print("No results found")
        return
    
    print(f"Found {len(results)} results:")
    
    for i, result in enumerate(results[:max_display]):
        symbol = result.symbol
        score = result.combined_score
        symbol_type = f" [{symbol.symbol_type.value}]" if symbol.symbol_type else ""
        print(f"{i+1:2d}. {symbol.name} ({score:.2f}) - {symbol.file_path}:{symbol.line_number}{symbol_type}")


def _interactive_search(config, max_results: int = 50):
    background_search = BackgroundSearch(config)
    current_results = []
    
    def on_results_update(results):
        nonlocal current_results
        current_results = results
        os.system('clear' if os.name == 'posix' else 'cls')
        print("Symbol Search (type to search, Ctrl+C to exit)")
        _display_results(results)
        print("Query: ", end='', flush=True)
    
    print("Symbol Search (type to search, Ctrl+C to exit)")
    print("Query: ", end='', flush=True)
    
    try:
        while True:
            query = input().strip()
            if not query:
                background_search.cancel()
                current_results = []
                os.system('clear' if os.name == 'posix' else 'cls')
                print("Interactive Symbol Search (type to search, Ctrl+C to exit)")
                print("=" * 60)
                _display_results([])
                print("Query: ", end='', flush=True)
                continue
            
            background_search.start_search(
                symbol_query=query,
                max_results=max_results,
                callback=on_results_update
            )
            
    except KeyboardInterrupt:
        background_search.cancel()
        print("\nSearch cancelled. Exiting...")


def search_symbols(
    project_path: str, 
    language: str, 
    max_results: int = 50,
    interactive: bool = True,
    query: str = ""
) -> None:
    config_path = get_config_path(project_path, language)

    if not os.path.exists(config_path):
        print(f"Index file not found: {config_path}")
        print("Use 'create' command to build initial index")
        sys.exit(1)

    config = load_index_config(config_path)
    
    if interactive:
        _interactive_search(config, max_results)
    else:
        from indexer.search import fuzzy_search_symbols
        results = fuzzy_search_symbols(config, symbol_query=query, max_results=max_results)
        _display_results(results, max_results)


def main():
    parser = argparse.ArgumentParser(description="Code indexer CLI")
    parser.add_argument(
        "command", choices=["create", "update", "search"], help="Command to execute"
    )
    parser.add_argument(
        "--project", "-p", default=".", help="Project path (default: current directory)"
    )
    parser.add_argument(
        "--language",
        "-l",
        default="python",
        help="Programming language (default: python)",
    )
    parser.add_argument("--progress", action="store_true", help="Show progress bars")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without updating (update command only)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of search results (search command only)",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive mode (search command only)",
    )
    parser.add_argument(
        "--query",
        help="Search query (for non-interactive mode)",
    )

    args = parser.parse_args()

    project_path = os.path.abspath(args.project)

    if not os.path.exists(project_path):
        print(f"Project path does not exist: {project_path}")
        sys.exit(1)

    if args.command == "create":
        create_index(project_path, args.language, args.progress)
    elif args.command == "update":
        update_index(project_path, args.language, args.progress, args.dry_run)
    elif args.command == "search":
        if args.no_interactive and not args.query:
            print("Error: --query is required when using --no-interactive")
            sys.exit(1)
        search_symbols(
            project_path, 
            args.language, 
            args.max_results,
            not args.no_interactive,
            args.query or ""
        )


if __name__ == "__main__":
    main()
