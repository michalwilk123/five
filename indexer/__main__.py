#!/usr/bin/env python3
import os
import sys

import click

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
from indexer.docs import CREATE_HELP, UPDATE_HELP, SEARCH_HELP, FOLD_HELP, EDIT_HELP
from indexer.differ import DiffParser, FileEditor


def common_options(f):
    """Decorator for common CLI options used across multiple commands."""
    f = click.option(
        "--project", "-p", default=".", help="Project path (default: current directory)"
    )(f)
    f = click.option(
        "--language",
        "-l",
        default="python",
        help="Programming language (default: python)",
    )(f)
    return f


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


def _handle_fold(file_spec: str, config, level: int, numbers: bool) -> None:
    """Handle the fold command."""
    file_path, line_range = parse_file_spec(file_spec)
    code_range = get_code_range(file_path, line_range)
    folded_lines = fold_file(file_path, config, code_range, level)

    for line_num, text in folded_lines:
        if numbers:
            print(f"{line_num:4d} {text}")
        else:
            print(text)


def _handle_edit(project_path: str) -> None:
    """Handle the edit command."""
    try:
        parser = DiffParser(project_path)
        operations = parser.parse_stdin()

        if not operations:
            click.echo("No diff operations found in input", err=True)
            sys.exit(1)

        seen_files = set()
        for op in operations:
            if op.filepath in seen_files:
                raise ValueError(f"Duplicate file entry: {op.filepath}")
            seen_files.add(op.filepath)

        editor = FileEditor()
        editor.add_operations(operations)
        editor.validate_operations()

        modified_files = editor.apply_operations()

        for filepath in modified_files:
            click.echo(filepath)

    except (ValueError, IOError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


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


@click.group()
@click.version_option()
def cli():
    """Code indexer CLI"""
    pass


@cli.command(help=CREATE_HELP)
@common_options
@click.option("--progress", is_flag=True, help="Show progress bars")
def create(project: str, language: str, progress: bool):
    project_path = os.path.abspath(project)

    if not os.path.exists(project_path):
        click.echo(f"Project path does not exist: {project_path}")
        sys.exit(1)

    try:
        config_path = create_index(project_path, language, None, progress)
        click.echo(f"Index created: {config_path}")
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command(help=UPDATE_HELP)
@common_options
@click.option("--progress", is_flag=True, help="Show progress bars")
@click.option("--dry-run", is_flag=True, help="Show what would change without updating")
def update(project: str, language: str, progress: bool, dry_run: bool):
    project_path = os.path.abspath(project)

    if not os.path.exists(project_path):
        click.echo(f"Project path does not exist: {project_path}")
        sys.exit(1)

    try:
        config = load_index_config_from_file(get_config_path(project_path, language))
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
        click.echo("Use 'create' command to build initial index")
        sys.exit(1)

    try:
        has_changes, file_changes, updated_path = update_index(
            project_path, language, config, progress, dry_run
        )
        _handle_changes(has_changes, file_changes, updated_path, dry_run)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command(help=SEARCH_HELP)
@common_options
@click.option(
    "--max-results", type=int, default=50, help="Maximum number of search results"
)
@click.option("--no-interactive", is_flag=True, help="Disable interactive mode")
@click.option("--query", help="Search query (for non-interactive mode)")
@click.option("--show-code", is_flag=True, help="Display code content for symbols")
def search(
    project: str,
    language: str,
    max_results: int,
    no_interactive: bool,
    query: str | None,
    show_code: bool,
):
    project_path = os.path.abspath(project)

    if not os.path.exists(project_path):
        click.echo(f"Project path does not exist: {project_path}")
        sys.exit(1)

    try:
        config = load_index_config_from_file(get_config_path(project_path, language))
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
        click.echo("Use 'create' command to build initial index")
        sys.exit(1)

    try:
        if no_interactive and not query:
            click.echo("Error: --query is required when using --no-interactive")
            sys.exit(1)

        if no_interactive:
            indexer = Indexer(project_path, language, config)
            results = indexer.search_symbols(query or "", max_results)
            click.echo(
                format_search_results(
                    results, max_results, show_code, project_path, config
                )
            )
        else:
            _interactive_search(config, project_path, max_results, show_code)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command(help=FOLD_HELP)
@common_options
@click.option("--numbers", "-n", is_flag=True, help="Show line numbers")
@click.argument("file_spec", required=True)
@click.argument("level", type=int, default=1, required=False)
def fold(project: str, language: str, numbers: bool, file_spec: str, level: int = 1):
    project_path = os.path.abspath(project)

    if not os.path.exists(project_path):
        click.echo(f"Project path does not exist: {project_path}")
        sys.exit(1)

    try:
        config = load_index_config_from_file(get_config_path(project_path, language))
    except FileNotFoundError as e:
        click.echo(f"Error: {e}")
        click.echo("Use 'create' command to build initial index")
        sys.exit(1)

    try:
        _handle_fold(file_spec, config, level, numbers)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@cli.command(help=EDIT_HELP)
@common_options
def edit(project: str, language: str):
    project_path = os.path.abspath(project)

    if not os.path.exists(project_path):
        click.echo(f"Project path does not exist: {project_path}")
        sys.exit(1)

    try:
        _handle_edit(project_path)
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
