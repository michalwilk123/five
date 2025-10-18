from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any, Callable, TypeAlias, TypeVar


def noop_log(message: str) -> None:
    pass


NOOP_LOG = noop_log

LogFunction: TypeAlias = Callable[[str], None]

T = TypeVar('T')


def timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_json_array(
    raw_value: str,
    option_name: str,
    item_mapper: Callable[[Any], T] | None = None,
) -> list[T] | list[Any]:
    """Parse a JSON array option, optionally converting each element."""

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON in {option_name}: {exc}') from exc

    if not isinstance(parsed, list):
        raise ValueError(f'{option_name} must be a JSON array')

    if item_mapper is None:
        return parsed

    converted: list[T] = []
    for index, item in enumerate(parsed):
        try:
            converted.append(item_mapper(item))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f'{option_name} contains an invalid value at index {index}: {exc}'
            ) from exc

    return converted


def generate_unique_project_name(base_name: str, existing_names: list[str]) -> str:
    if base_name not in existing_names:
        return base_name

    counter = 2
    while f'{base_name}_{counter}' in existing_names:
        counter += 1

    return f'{base_name}_{counter}'


def find_git_repo_path(project_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ['git', '-C', str(project_path), 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
