from __future__ import annotations

import dataclasses
import itertools
import random
from typing import Any

from flang.structures import (
    BaseUserAST,
    FlangAST,
    UserASTComplexNode,
    UserASTDirectoryNode,
    UserASTFlatFileNode,
    VirtualFileRepresentation,
)
from flang.utils.exceptions import SymbolNotFoundError
from flang.utils.regex import lex_storage


@dataclasses.dataclass
class GeneratorSetup:
    patches: dict[str, str | int] = dataclasses.field(default_factory=dict)
    enforce_full_specification: bool = False

    def _generate_random_content(self, flang_ast):
        if flang_ast.location in self.patches:
            return self.patches[flang_ast.location]

        match flang_ast:
            case "choice":
                return random.randrange(len(flang_ast.children))
            case "text":
                flang_ast_text = flang_ast.get_attrib("value", flang_ast.text)
                return flang_ast_text
            case "text":
                flang_ast_text = flang_ast.get_attrib("value", flang_ast.text)
                return lex_storage.generate_example(flang_ast_text)
            case "file":
                filename = flang_ast.get_attrib("filename")
                return lex_storage.generate_example(filename)

        raise RuntimeError

    def get(self, location, type): ...


EMPTY_SETUP = GeneratorSetup()


def generate_node_quantity(flang_ast) -> int:
    number_choice = [1]

    if flang_ast.get_bool_attrib("hidden"):
        return 0

    if flang_ast.get_bool_attrib("multi"):
        number_choice = number_choice + [2, 3, 4, 5]

    if flang_ast.get_bool_attrib("optional"):
        number_choice = number_choice + [0]

    return random.choice(number_choice)


def generate_single_sample(flang_ast: FlangAST) -> BaseUserAST: ...


def contains_files(flang_ast: FlangAST) -> bool:
    for child in flang_ast.children:
        if child.get_bool_attrib("hidden"):
            continue

        if child.type in ("text", "regex"):
            return False
        elif child.type in ("file"):
            return True
        return contains_files(child)

    raise RuntimeError


def generate_single_node(flang_ast: FlangAST, setup: GeneratorSetup) -> BaseUserAST:
    match flang_ast.type:
        case "sequence":
            return UserASTComplexNode(
                children=list(
                    itertools.chain(generate_node(child) for child in flang_ast.children)
                )
            )
        case "choice":
            idx = setup.get(setup, flang_ast)
            patch_value = setup.patches.get(
                flang_ast.location,
            )
            return UserASTComplexNode
            # return UserASTComplexNode(children=list(itertools.chain(generate_node(child) for child in flang_ast.children)))
        case "use":
            target_location = flang_ast.get_attrib("ref")
            location = flang_ast.location

            target_location = flang_ast.normalize_path(target_location)
            target_flang_ast = flang_ast.resolve_path(target_location, location)

            if target_flang_ast is None:
                raise SymbolNotFoundError(
                    f"Could not find symbol for path: {target_location}, location: {location}"
                )

            attributes = {
                **target_flang_ast.attributes,
                **flang_ast.attributes,
                "hidden": False,
            }
            del attributes["ref"]

            cloned_flang_node = target_flang_ast.replace(attributes=attributes)

            return generate_single_node(cloned_flang_node, setup)
        case "regex":
            ...
        case "text":
            return
        case "file":
            try:
                if contains_files(flang_ast):
                    return UserASTDirectoryNode(
                        children=list(
                            itertools.chain(
                                generate_node(child) for child in flang_ast.children
                            )
                        )
                    )
                else:
                    return UserASTFlatFileNode(
                        children=list(
                            itertools.chain(
                                generate_node(child) for child in flang_ast.children
                            )
                        )
                    )
            except RuntimeError as e:
                raise RuntimeError(
                    "File objects cannot only contain hidden components. "
                    "I need to know if it is file or a directory to generate ast"
                )


def generate_node(flang_ast: FlangAST, setup: GeneratorSetup) -> list[BaseUserAST]:
    qty = generate_node_quantity(flang_ast, setup)
    return [generate_single_node(flang_ast, setup) for _ in range(qty)]


def generate_user_ast(
    flang_ast: FlangAST, setup: GeneratorSetup | None = None
) -> list[BaseUserAST]:
    setup = setup or EMPTY_SETUP
    generated = []

    for child in flang_ast.children:
        generated = generated + generate_node(child, setup)

    return generated
