"""
Core Code Folding Functionality

Pure folding logic for hierarchical code folding based on symbol declarations.
This module provides the core folding algorithms used by the main CLI.
"""

from indexer.utils import IndexConfig, SymbolDeclaration, SymbolType, SymbolScope

Range = tuple[int, int]
LineContent = tuple[int, str]


def get_code_range(file_path: str, line_range: Range | None) -> Range:
    """Get the code range. If range is None, return 0 to file length."""
    if line_range:
        return line_range

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return (0, len(lines))


def get_file_symbols(config: IndexConfig, file_path: str) -> list[SymbolDeclaration]:
    """Get all symbols for a specific file, sorted by line number."""
    symbols = [s for s in config.symbols if s.file_path == file_path]
    symbols.sort(key=lambda s: s.line_number)
    return symbols


def find_parent_symbols(symbols: list[SymbolDeclaration]) -> set[SymbolDeclaration]:
    """Find parent symbols (symbols that contain other symbols)."""
    parent_symbols = set()
    for i, symbol in enumerate(symbols):
        for j, other in enumerate(symbols):
            if i != j and symbol.line_number < other.line_number:
                # Find if 'other' ends before next symbol after 'symbol'
                next_symbol_after_parent = None
                for k, next_sym in enumerate(symbols):
                    if k > i and next_sym.line_number > symbol.line_number:
                        next_symbol_after_parent = next_sym
                        break

                if (
                    next_symbol_after_parent
                    and other.line_number < next_symbol_after_parent.line_number
                ):
                    parent_symbols.add(symbol)
                    break
    return parent_symbols


def is_in_folded_parent(
    current_line: int,
    parent_symbols: set[SymbolDeclaration],
    symbols: list[SymbolDeclaration],
) -> bool:
    """Check if current line is in a folded parent symbol."""
    for symbol in parent_symbols:
        if symbol.line_number <= current_line:
            # Find next symbol after this parent
            next_symbol = None
            for s in symbols:
                if s.line_number > symbol.line_number:
                    next_symbol = s
                    break

            if next_symbol and current_line < next_symbol.line_number:
                return True
    return False


def process_line(
    current_line: int, symbols: list[SymbolDeclaration], lines: list[str], end_line: int
) -> tuple[int, LineContent | None]:
    """Process a single line and return next line number and content if visible."""
    # Check if current line is a symbol declaration
    current_symbol = None
    for symbol in symbols:
        if symbol.line_number == current_line:
            current_symbol = symbol
            break

    if current_symbol:
        # Show symbol declaration
        content = (current_line, lines[current_line - 1].rstrip())

        # Find next symbol to determine fold range
        next_symbol = None
        for symbol in symbols:
            if symbol.line_number > current_line:
                next_symbol = symbol
                break

        # Hide code between current symbol and next symbol
        if next_symbol:
            return next_symbol.line_number, content
        else:
            # If this is the last symbol, fold to end of file
            return end_line + 1, content
    else:
        # Show regular line
        content = (current_line, lines[current_line - 1].rstrip())
        return current_line + 1, content


def fold_file(
    file_path: str, config: IndexConfig, line_range: Range, level: int
) -> list[LineContent]:
    """Perform fold operation on file and return list of (line_number, text) tuples."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    symbols = get_file_symbols(config, file_path)

    if level >= 3:
        # Level 3+: Show everything (no folding)
        result: list[LineContent] = []
        start_line, end_line = line_range
        for i in range(start_line, end_line + 1):
            if i <= len(lines):
                result.append((i, lines[i - 1].rstrip()))
        return result

    # For levels 0-2, filter symbols based on level
    filtered_symbols = filter_symbols_by_level(symbols, level)
    parent_symbols = find_parent_symbols(filtered_symbols)

    result: list[LineContent] = []
    start_line, end_line = line_range
    current_line = start_line

    while current_line <= end_line:
        # Check if current line is in a folded parent symbol
        if is_in_folded_parent(current_line, parent_symbols, filtered_symbols):
            current_line += 1
            continue

        # Process the line
        next_line, content = process_line(
            current_line, filtered_symbols, lines, end_line
        )
        if content:
            result.append(content)
        current_line = next_line

    return result


def filter_symbols_by_level(
    symbols: list[SymbolDeclaration], level: int
) -> list[SymbolDeclaration]:
    """Filter symbols based on folding level."""
    if level == 0:
        # Level 0: Only show top-level imports and module structure
        return [
            s
            for s in symbols
            if s.scope == SymbolScope.GLOBAL and s.symbol_type == SymbolType.CLASS
        ]
    elif level == 1:
        # Level 1: Show classes and global functions, fold class internals
        return [s for s in symbols if s.scope == SymbolScope.GLOBAL]
    elif level == 2:
        # Level 2: Show classes, global functions, and class methods, fold variables/constants
        return [s for s in symbols if s.symbol_type != SymbolType.CONSTANT]
    else:
        # Level 3+: Show everything
        return symbols
