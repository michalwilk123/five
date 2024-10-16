import re

from flang.structures import BaseFlangInputReader, BaseUserAST, FlangAST
from flang.structures.ast import (
    UserASTAbstractNode,
    UserASTComplexNode,
    UserASTDirectoryNode,
    UserASTFileMixin,
    UserASTFlatFileNode,
    UserASTTextNode,
)
from flang.structures.input import FlangFileInputReader, IntermediateFileObject
from flang.utils.common import BUILTIN_PATTERNS
from flang.utils.exceptions import (
    ComplexMatchNotFound,
    FileMatchNotFound,
    MatchNotFoundError,
    SkipFlangNodeException,
    SymbolNotFoundError,
    TextMatchNotFound,
    TextNotParsedError,
    UnknownFlangNodeError,
)


def match_on_complex_flang_ast(
    flang_ast: FlangAST,
    reader: BaseFlangInputReader,
) -> BaseUserAST:
    match flang_ast.type:
        case "sequence":
            matches = []

            assert isinstance(flang_ast.children, list)

            try:
                for child in flang_ast.children:
                    match_objects, reader = match_flang_flang_ast(child, reader)

                    matches += match_objects
            except MatchNotFoundError as e:
                raise ComplexMatchNotFound(
                    f"Could not match sequence of flang_asts: {flang_ast.type or flang_ast.location}"
                ) from e

            return UserASTComplexNode(
                name=flang_ast.name,
                flang_ast_path=flang_ast.location,
                children=matches,
            )
        case "choice":
            matches = []
            readers = []

            for child in flang_ast.children:
                try:
                    match_objects, reader = match_flang_flang_ast(child, reader)

                    matches += match_objects
                    readers.append(reader)
                    reader = reader.previous
                except MatchNotFoundError:
                    pass

            if not matches:
                raise ComplexMatchNotFound(
                    f"Could not match any flang_ast from: {flang_ast.type or flang_ast.location}"
                )

            max_reader = max(readers, key=lambda it: it.get_key())
            return matches[readers.index(max_reader)]

        case "event":
            # TODO: <--- TUTAJ SKONCZYLES
            raise NotImplementedError
        case "module":
            # NOTE: This represents a simple container of all nodes inside this node. This is
            # used mainly for modules and imports. By default it is hidden
            # This is "sequence" that is hidden by default
            raise NotImplementedError
        case "use":
            target_location = flang_ast.get_attrib("ref")
            location = flang_ast.location

            target_flang_ast = flang_ast.resolve_path(target_location, location)

            if target_flang_ast is None:
                raise SymbolNotFoundError(
                    f"Could not find symbol for path: {target_location}, location: {location}"
                )
            # TODO: if target_flang_ast.type is "module" then "hidden" attribute should stay

            attributes = {
                **target_flang_ast.attributes,
                **flang_ast.attributes,
                "hidden": False,
            }
            del attributes["ref"]

            # TODO: can be cached very easily
            cloned_flang_node = target_flang_ast.replace(attributes=attributes)

            return match_against_all_flang_ast_variants(cloned_flang_node, reader)
        case _:
            raise UnknownFlangNodeError("Not complex flang_ast")


def match_on_text(
    flang_ast: FlangAST,
    reader: BaseFlangInputReader,
) -> UserASTTextNode:
    text_to_match = reader.read()
    flang_ast_text = flang_ast.get_attrib("value", flang_ast.text)
    content = None

    match flang_ast.type:
        case "regex":
            assert isinstance(text_to_match, str) and isinstance(flang_ast_text, str)

            flang_ast_pattern = flang_ast_text.format(**BUILTIN_PATTERNS)
            matched_text = re.match(flang_ast_pattern, text_to_match)

            if not matched_text:
                raise TextMatchNotFound(
                    f'Could not match regex pattern: "{flang_ast_pattern}" with text: "{reader.read()[:15]}"'
                )

            if not matched_text.group():
                raise RuntimeError(
                    "We have matched an empty object which does not make any sense. Please fix the template to not match such text. Like what would you expect after matching nothing?"
                )

            content = matched_text.group()
        case "text":
            assert isinstance(text_to_match, str) and isinstance(flang_ast_text, str)

            if not text_to_match.startswith(flang_ast_text):
                raise TextMatchNotFound(
                    f'Could not match text pattern: "{flang_ast_text}" with '
                    f'text: "{reader.read()[:len(flang_ast_text)]}"'
                )

            content = flang_ast_text
        case _:
            raise UnknownFlangNodeError("Not text flang_ast")

    return UserASTTextNode(
        name=flang_ast.name, flang_ast_path=flang_ast.location, content=content
    )


def match_on_file(
    flang_ast: FlangAST,
    reader: BaseFlangInputReader,
) -> UserASTFileMixin:
    if flang_ast.type != "file":
        raise UnknownFlangNodeError("Not file flang_ast")

    assert isinstance(reader, FlangFileInputReader)

    current_files = reader.read()

    pattern = flang_ast.get_attrib("pattern")
    variant = flang_ast.get_attrib("variant", "filename")

    matched_file = IntermediateFileObject.get_first_matched_file(
        current_files, pattern, variant
    )

    if not matched_file:
        raise FileMatchNotFound(
            f'Could not match filename pattern: "{pattern}" variant: {variant} with available '
            f'files in directory: "{[f.path.name for f in current_files]}"'
        )

    child = flang_ast.first_child
    sub_reader = matched_file.get_input_reader()

    content, out_reader = match_flang_flang_ast(child, sub_reader)

    if out_reader.read():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    if isinstance(sub_reader, FlangFileInputReader):
        return UserASTDirectoryNode(
            name=flang_ast.name,
            flang_ast_path=flang_ast.location,
            children=content,  # type: ignore TODO: napraw to
            filename=matched_file.filename,
        )

    return UserASTFlatFileNode(
        name=flang_ast.name,
        flang_ast_path=flang_ast.location,
        children=content,
        filename=matched_file.filename,
    )


def match_against_all_flang_ast_variants(
    flang_ast: FlangAST,
    reader: BaseFlangInputReader,
) -> BaseUserAST:
    matchers = (
        match_on_complex_flang_ast,
        match_on_text,
        match_on_file,
    )
    match_object = None

    for matcher in matchers:
        try:
            match_object = matcher(flang_ast, reader)
        except UnknownFlangNodeError:
            continue
        else:
            break

    if match_object is None:
        raise UnknownFlangNodeError

    return match_object


def match_flang_flang_ast(
    flang_ast: FlangAST,
    reader: BaseFlangInputReader,
) -> tuple[list[BaseUserAST], BaseFlangInputReader]:
    if alias_name := flang_ast.get_attrib("alias"):
        flang_ast.create_alias(alias_name)

    if flang_ast.get_bool_attrib("hidden") or flang_ast.type in ["event"]:
        return [], reader

    reader = reader.copy()
    matches = []

    try:
        match_object = match_against_all_flang_ast_variants(flang_ast, reader)
        matches.append(match_object)
        if isinstance(match_object, UserASTComplexNode):
            pass
        reader.consume_data(match_object)
    except (MatchNotFoundError, SkipFlangNodeException) as e:
        if isinstance(e, MatchNotFoundError) and not flang_ast.get_bool_attrib(
            "optional"
        ):
            raise e

        return [], reader.previous

    while flang_ast.get_bool_attrib("multi"):
        reader = reader.copy()
        try:
            match_object = match_against_all_flang_ast_variants(flang_ast, reader)
            matches.append(match_object)
            reader.consume_data(match_object)
        except MatchNotFoundError as e:
            reader = reader.previous
            break

    return matches, reader


def parse_user_language(
    flang_ast: FlangAST, reader: BaseFlangInputReader
) -> tuple[list[BaseUserAST], BaseFlangInputReader]:

    match_objects, out_reader = match_flang_flang_ast(flang_ast.root, reader)

    if out_reader.read():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    if flang_ast.root.type == "file":
        assert (
            len(match_objects) == 1
        ), "When matching a file tree, we should only return one file (root) as the result"
        assert isinstance(match_objects[0], UserASTFileMixin)
        return match_objects[0]

    if match_objects == []:
        raise RuntimeError(
            "I dont really know what should be return value here. Maybe this should not be possible at all"
        )

    assert isinstance(match_objects, list), isinstance(match_objects, list)

    return UserASTAbstractNode(children=match_objects)
