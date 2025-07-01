"""
Python file parser using AST to extract symbols.
"""

import ast

from indexer.utils import SymbolDeclaration, SymbolType


def parse_source(content: str, filename: str) -> list[SymbolDeclaration]:
    """
    Parse Python source code and extract symbol declarations.

    Args:
        content: Python source code as string
        filename: Path to the Python file (for reference in SymbolDeclaration)

    Returns:
        List of SymbolDeclaration objects
    """
    symbols = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return symbols

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            symbols.append(
                SymbolDeclaration(
                    name=node.name,
                    file_path=filename,
                    line_number=node.lineno,
                    symbol_type=SymbolType.FUNCTION,
                )
            )
        elif isinstance(node, ast.ClassDef):
            symbols.append(
                SymbolDeclaration(
                    name=node.name,
                    file_path=filename,
                    line_number=node.lineno,
                    symbol_type=SymbolType.CLASS,
                )
            )
        elif isinstance(node, ast.Assign):
            if _is_global_scope(node, tree):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.append(
                            SymbolDeclaration(
                                name=target.id,
                                file_path=filename,
                                line_number=node.lineno,
                                symbol_type=SymbolType.CONSTANT,
                            )
                        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    symbols.append(
                        SymbolDeclaration(
                            name=f"{node.name}.{item.name}",
                            file_path=filename,
                            line_number=item.lineno,
                            symbol_type=SymbolType.FUNCTION,
                        )
                    )

    return symbols


def parse(project_root: str, filename: str) -> list[SymbolDeclaration]:
    """
    Parse a Python file and extract symbol declarations.

    Args:
        project_root: Root directory of the project
        filename: Path to the Python file relative to project root

    Returns:
        List of SymbolDeclaration objects
    """
    file_path = f"{project_root}/{filename}"

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    return parse_source(content, filename)


def _is_global_scope(node: ast.AST, tree: ast.AST) -> bool:
    """
    Check if a node is in global scope (not inside a function or class).
    """
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.FunctionDef, ast.ClassDef)):
            if _node_in_parent(node, parent):
                return False
    return True


def _node_in_parent(node: ast.AST, parent: ast.AST) -> bool:
    """
    Check if a node is contained within a parent node.
    """
    for child in ast.walk(parent):
        if child is node:
            return True
    return False
