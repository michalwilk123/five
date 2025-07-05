import tomllib
from dataclasses import asdict, dataclass
from enum import Enum
import os

import tomli_w


class SymbolType(Enum):
    """
    Enumeration of different types of code declarations.

    CLASS: Represents classes and structures that encapsulate runtime state.
           These are containers designed to hold and manage data during program execution.

    CONSTANT: Represents constants and variables that encapsulate hardcoded values.
              Examples include mathematical constants like PI or configuration values.

    FUNCTION: Represents functions and methods that serve as building blocks of code.
              These are reusable code units designed to perform specific operations.

    OTHER: Represents other types of code declarations that don't fit into the above categories.
           This includes Enums, Types, etc.
    """

    CLASS = "class/structure"
    CONSTANT = "constant/variable"
    FUNCTION = "function/method"
    OTHER = "other"


@dataclass
class SymbolDeclaration:
    name: str
    file_path: str
    line_number: int
    symbol_type: SymbolType


@dataclass
class SearchResult:
    symbol: SymbolDeclaration
    symbol_index: int
    symbol_score: float
    file_score: float
    combined_score: float
    # Może sie przyda :) Zadecyduj na podstawie empirycznych testów
    # symbol_occurrences: int


@dataclass
class IndexConfig:
    symbols: list[SymbolDeclaration]
    file_hashes: dict[str, str]
    merkle_hashes: dict[str, str]
    language: str
    last_updated: str


def index_config_to_toml(config: IndexConfig) -> str:
    data = asdict(config)
    data["symbols"] = [
        {
            "name": symbol["name"],
            "file_path": symbol["file_path"],
            "line_number": symbol["line_number"],
            "symbol_type": symbol["symbol_type"].value,
        }
        for symbol in data["symbols"]
    ]
    return tomli_w.dumps(data)


def toml_to_index_config(toml_content: str) -> IndexConfig:
    data = tomllib.loads(toml_content)
    symbols = [
        SymbolDeclaration(
            name=symbol["name"],
            file_path=symbol["file_path"],
            line_number=symbol["line_number"],
            symbol_type=SymbolType(symbol["symbol_type"]),
        )
        for symbol in data["symbols"]
    ]
    return IndexConfig(
        symbols=symbols,
        file_hashes=data["file_hashes"],
        merkle_hashes=data["merkle_hashes"],
        language=data["language"],
        last_updated=data["last_updated"],
    )


def get_symbol_text(result: SearchResult, symbols: list[SymbolDeclaration], project_path: str) -> str:
    symbol = result.symbol
    symbol_index = result.symbol_index
    file_path = os.path.join(project_path, symbol.file_path)

    with open(file_path, 'r') as f:
        lines = f.readlines()

    start_line = symbol.line_number - 1
    end_line = len(lines)

    for next_symbol in symbols[symbol_index + 1:]:
        if next_symbol.file_path == symbol.file_path:
            end_line = next_symbol.line_number - 1
            break

    return "".join(lines[start_line:end_line])
