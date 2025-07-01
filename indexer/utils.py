from dataclasses import dataclass
from enum import Enum


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
class IndexConfig:
    symbols: list[SymbolDeclaration]
    file_hashes: dict[str, str]
    merkle_hashes: dict[str, str]
    language: str
    last_updated: int
