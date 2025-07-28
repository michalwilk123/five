#!/usr/bin/env python3
import argparse
import os
import sys

from indexer.folding import fold_file, get_code_range
from indexer.lib import (
    Indexer,
    create_index,
    format_file_changes,
    format_search_results,
    get_config_path,
    update_index,
    parse_file_spec,
)
from indexer.utils import load_index_config_from_file


def _handle_changes(
    has_changes: bool,
    file_changes: dict,
    updated_path: str | None = None,
    dry_run: bool = False,
) -> None:
    if has_changes:
        if dry_run:
            print("Changes detected:")
        print(format_file_changes(file_changes))
        if dry_run:
            print("(dry run - no changes made)")
            sys.exit(1)
        else:
            print(f"Index updated: {updated_path}")
    else:
        print("no changes")


def _handle_fold(args, config) -> None:
    """Handle the fold command."""
    file_path, line_range = parse_file_spec(args.file_spec)
    code_range = get_code_range(file_path, line_range)
    folded_lines = fold_file(file_path, config, code_range, args.level)

    for line_num, text in folded_lines:
        if args.numbers:
            print(f"{line_num:4d} {text}")
        else:
            print(text)


def _interactive_search(
    config, project_path: str, max_results: int = 50, show_code: bool = False
):
    indexer = Indexer(project_path, config.language, config)
    background_search = indexer.create_background_search()
    current_results = []

    def on_results_update(results):
        nonlocal current_results
        current_results = results
        print("Symbol Search (type to search, Ctrl+C to exit)")
        print(
            format_search_results(
                results, show_code=show_code, project_path=project_path, config=config
            )
        )
        print("Query: ", end="", flush=True)

    print("Symbol Search (type to search, Ctrl+C to exit)")
    print("Query: ", end="", flush=True)

    try:
        while True:
            query = input().strip()
            if not query:
                background_search.cancel()
                current_results = []
                os.system("clear" if os.name == "posix" else "cls")
                print("Interactive Symbol Search (type to search, Ctrl+C to exit)")
                print("=" * 60)
                print(
                    format_search_results(
                        [],
                        show_code=show_code,
                        project_path=project_path,
                        config=config,
                    )
                )
                print("Query: ", end="", flush=True)
                continue

            background_search.start_search(
                symbol_query=query, max_results=max_results, callback=on_results_update
            )

    except KeyboardInterrupt:
        background_search.cancel()
        print("\nSearch cancelled. Exiting...")


def main():
    parser = argparse.ArgumentParser(description="Code indexer CLI")
    parser.add_argument(
        "command",
        choices=["create", "update", "search", "fold"],
        help="Command to execute",
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
    parser.add_argument(
        "--show-code",
        action="store_true",
        help="Display code content for symbols in search results",
    )
    parser.add_argument(
        "--file-spec",
        help="File path with optional range (e.g., file.py:20-400) (fold command only)",
    )
    parser.add_argument(
        "--numbers",
        "-n",
        action="store_true",
        help="Show line numbers (fold command only)",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        help="Folding level (0-3, default: 1) (fold command only)",
    )

    args = parser.parse_args()

    project_path = os.path.abspath(args.project)

    if not os.path.exists(project_path):
        print(f"Project path does not exist: {project_path}")
        sys.exit(1)

    config = None
    if args.command in ["update", "search", "fold"]:
        try:
            config = load_index_config_from_file(
                get_config_path(project_path, args.language)
            )
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Use 'create' command to build initial index")
            sys.exit(1)

    try:
        if args.command == "create":
            config_path = create_index(
                project_path, args.language, config, args.progress
            )
            print(f"Index created: {config_path}")
        elif args.command == "update":
            has_changes, file_changes, updated_path = update_index(
                project_path, args.language, config, args.progress, args.dry_run
            )
            _handle_changes(has_changes, file_changes, updated_path, args.dry_run)
        elif args.command == "search":
            if args.no_interactive and not args.query:
                print("Error: --query is required when using --no-interactive")
                sys.exit(1)

            if args.no_interactive:
                indexer = Indexer(project_path, args.language, config)
                results = indexer.search_symbols(args.query or "", args.max_results)
                print(
                    format_search_results(
                        results, args.max_results, args.show_code, project_path, config
                    )
                )
            else:
                _interactive_search(
                    config, project_path, args.max_results, args.show_code
                )
        elif args.command == "fold":
            if not args.file_spec:
                print("Error: --file-spec is required for fold command")
                sys.exit(1)
            _handle_fold(args, config)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
