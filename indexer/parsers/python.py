import ast

from indexer.utils import SymbolDeclaration, SymbolScope, SymbolType


def create_symbol_declaration(
    name: str,
    filename: str,
    line_number: int,
    symbol_type: SymbolType,
    scope: SymbolScope,
) -> SymbolDeclaration:
    return SymbolDeclaration(
        name=name,
        file_path=filename,
        line_number=line_number,
        symbol_type=symbol_type,
        scope=scope,
    )


def process_function_def(
    node: ast.FunctionDef, filename: str, current_class: str | None = None
) -> SymbolDeclaration:
    if current_class is None:
        return create_symbol_declaration(
            node.name, filename, node.lineno, SymbolType.FUNCTION, SymbolScope.GLOBAL
        )
    else:
        return create_symbol_declaration(
            f"{current_class}.{node.name}",
            filename,
            node.lineno,
            SymbolType.FUNCTION,
            SymbolScope.CLASS,
        )


def process_class_def(node: ast.ClassDef, filename: str) -> list[SymbolDeclaration]:
    symbols = [
        create_symbol_declaration(
            node.name, filename, node.lineno, SymbolType.CLASS, SymbolScope.GLOBAL
        )
    ]

    for item in node.body:
        symbols.extend(process_node(item, filename, node.name))

    return symbols


def process_assign(
    node: ast.Assign, filename: str, current_class: str | None = None
) -> list[SymbolDeclaration]:
    symbols = []

    for target in node.targets:
        if isinstance(target, ast.Name):
            if current_class is None:
                symbols.append(
                    create_symbol_declaration(
                        target.id,
                        filename,
                        node.lineno,
                        SymbolType.CONSTANT,
                        SymbolScope.GLOBAL,
                    )
                )
            else:
                symbols.append(
                    create_symbol_declaration(
                        f"{current_class}.{target.id}",
                        filename,
                        node.lineno,
                        SymbolType.CONSTANT,
                        SymbolScope.CLASS,
                    )
                )

    return symbols


def process_ann_assign(
    node: ast.AnnAssign, filename: str, current_class: str | None = None
) -> list[SymbolDeclaration]:
    symbols = []

    if isinstance(node.target, ast.Name):
        if current_class is None:
            symbols.append(
                create_symbol_declaration(
                    node.target.id,
                    filename,
                    node.lineno,
                    SymbolType.OTHER,
                    SymbolScope.GLOBAL,
                )
            )
        else:
            symbols.append(
                create_symbol_declaration(
                    f"{current_class}.{node.target.id}",
                    filename,
                    node.lineno,
                    SymbolType.OTHER,
                    SymbolScope.CLASS,
                )
            )

    return symbols


def process_node(
    node: ast.AST, filename: str, current_class: str | None = None
) -> list[SymbolDeclaration]:
    if isinstance(node, ast.FunctionDef):
        return [process_function_def(node, filename, current_class)]
    elif isinstance(node, ast.ClassDef):
        return process_class_def(node, filename)
    elif isinstance(node, ast.Assign):
        return process_assign(node, filename, current_class)
    elif isinstance(node, ast.AnnAssign):
        return process_ann_assign(node, filename, current_class)
    else:
        return []


def parse_source(content: str, filename: str) -> list[SymbolDeclaration]:
    symbols = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return symbols

    for node in tree.body:
        symbols.extend(process_node(node, filename))

    return symbols


def parse(project_root: str, filename: str) -> list[SymbolDeclaration]:
    file_path = f"{project_root}/{filename}"

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    return parse_source(content, filename)
