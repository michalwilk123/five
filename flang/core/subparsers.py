import fnmatch
import re

from flang.structures import (
    BaseUserAST,
    FlangAST,
    FlangFileInputReader,
    InputReaderInterface,
    UserASTComplexNode,
    UserASTDirectoryNode,
    UserASTFileMixin,
    UserASTFlatFileNode,
    UserASTRootContainerNode,
    UserASTTextNode,
)
from flang.utils.common import BUILTIN_PATTERNS, NAMED_BUILTIN_PATTERNS
from flang.utils.exceptions import (
    ComplexMatchNotFound,
    FileMatchNotFound,
    MatchNotFoundError,
    NoMoreDataException,
    SkipFlangNodeException,
    SymbolNotFoundError,
    TextMatchNotFound,
    TextNotParsedError,
    UnknownFlangNodeError,
)


def _match_text_with_regex(text: str, pattern: str, negative: bool = False) -> str | None:
    pattern = pattern.format(**NAMED_BUILTIN_PATTERNS)

    if negative:
        re_match = re.search(pattern, text)

        if re_match is None:
            return text

        matched_text = text[: re_match.start()]
        return None if matched_text == "" else matched_text

    re_match = re.match(pattern, text)

    if re_match is not None:
        re_match = re_match.group()

    return re_match


def _match_text_with_text(text: str, pattern: str, negative: bool = False) -> str | None:
    if negative:
        idx = text.find(pattern)

        if idx == -1:
            return text

        return text[:idx]
    else:
        if text.startswith(pattern):
            return pattern

    return None


def _is_file_matched(filename: str, pattern: str, variant: str) -> str | None:
    assert variant in ("filename", "glob", "regex")

    if variant == "glob":
        pattern = fnmatch.translate(pattern)

    if variant == "filename":
        return filename == pattern

    return re.match(pattern, filename)


def match_on_complex_flang_ast(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> BaseUserAST:
    match flang_ast.type:
        case "sequence":
            matches = []

            assert isinstance(flang_ast.children, list)

            try:
                for child in flang_ast.children:
                    match_objects, reader = match_flang_ast_node(child, reader)

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
            matches: list[BaseUserAST] = []
            readers = []

            for child in flang_ast.children:
                try:
                    match_objects, reader = match_flang_ast_node(child, reader)

                    matches += match_objects
                    readers.append(reader)
                    reader = reader.previous
                except MatchNotFoundError:
                    pass

            if not matches:
                raise ComplexMatchNotFound(
                    f"Could not match any flang_ast from: {flang_ast.type or flang_ast.location} text: {reader.read()[:15]}"
                )

            max_reader = max(readers, key=lambda it: it.get_key())
            node = matches[readers.index(max_reader)]

            return node
        case "module":
            # NOTE: This represents a simple container of all nodes inside this node. This is
            # used mainly for modules and imports. By default it is hidden
            # This is "sequence" that is hidden by default. Dont know if this is so necessary...
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


def new_match_on_text(
    flang_ast: FlangAST, reader: InputReaderInterface
) -> UserASTTextNode:
    text_to_match = reader.read()
    content = None
    flang_ast_text = flang_ast.get_attrib("value", flang_ast.text)

    match flang_ast.type:
        case "predicate":
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
        case "const":
            assert isinstance(text_to_match, str) and isinstance(flang_ast_text, str)

            if not text_to_match.startswith(flang_ast_text):
                raise TextMatchNotFound(
                    f'Could not match text pattern: "{flang_ast_text}" with '
                    f'text: "{reader.read()[:len(flang_ast_text)]}"'
                )

            content = flang_ast_text
        case _:
            raise UnknownFlangNodeError("Not text flang_ast")

    if flang_ast.get_bool_attrib("not"):
        raise TextMatchNotFound('Matched with "not" attribute, so')

    return UserASTTextNode(
        name=flang_ast.name, flang_ast_path=flang_ast.location, content=content
    )


def match_on_text(flang_ast: FlangAST, reader: InputReaderInterface) -> UserASTTextNode:
    content = None
    flang_ast_text = flang_ast.get_attrib("value", flang_ast.text)

    match flang_ast.type:
        case "regex":
            text_to_match = reader.read()
            content = _match_text_with_regex(
                text_to_match, flang_ast_text, flang_ast.get_bool_attrib("not")
            )

            if content is None:
                raise TextMatchNotFound(
                    f'Could not match regex pattern: "{flang_ast_text}" with text: "{reader.read()[:15]}"'
                )

            if content == "":
                raise RuntimeError(
                    "We have matched an empty object which does not make any sense. Please fix the template to not match such text. Like what would you expect after matching nothing?"
                )
        case "text":
            text_to_match = reader.read()
            content = _match_text_with_text(
                text_to_match, flang_ast_text, flang_ast.get_bool_attrib("not")
            )

            if content is None:
                raise TextMatchNotFound(
                    f'Could not match text pattern: "{flang_ast_text}" with '
                    f'text: "{reader.read()[:len(flang_ast_text)]}"'
                )
        case _:
            raise UnknownFlangNodeError("Not text flang_ast")

    return UserASTTextNode(
        name=flang_ast.name, flang_ast_path=flang_ast.location, content=content
    )


def match_on_file(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> UserASTFileMixin:
    if flang_ast.type != "file":
        raise UnknownFlangNodeError("Not file flang_ast")

    assert isinstance(reader, FlangFileInputReader)

    try:
        filename = reader.read()
    except NoMoreDataException as e:
        raise FileMatchNotFound("No files found") from e

    pattern = flang_ast.get_attrib("pattern")
    variant = flang_ast.get_attrib("variant", "filename")

    if not _is_file_matched(filename, pattern, variant):
        raise FileMatchNotFound(
            f'Could not match filename pattern: "{pattern}" variant: {variant} with current '
            f'file : "{filename}"'
        )

    child = flang_ast.first_child
    sub_reader = reader.get_nested_reader(filename)
    content, out_reader = match_flang_ast_node(child, sub_reader)

    if not out_reader.is_empty():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    if isinstance(sub_reader, FlangFileInputReader):
        return UserASTDirectoryNode(
            name=flang_ast.name,
            flang_ast_path=flang_ast.location,
            children=content,  # type: ignore TODO: napraw to
            filename=filename,
        )

    return UserASTFlatFileNode(
        name=flang_ast.name,
        flang_ast_path=flang_ast.location,
        children=content,
        filename=filename,
    )


def match_against_all_flang_ast_variants(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> BaseUserAST:
    matchers = (
        match_on_complex_flang_ast,
        match_on_file,
        match_on_text,
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


def match_flang_ast_node(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> tuple[list[BaseUserAST], InputReaderInterface]:
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
    flang_ast: FlangAST, reader: InputReaderInterface
) -> tuple[list[BaseUserAST], InputReaderInterface]:

    match_objects, out_reader = match_flang_ast_node(flang_ast.root, reader)

    if not out_reader.is_empty():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    if flang_ast.root.type == "file":
        assert (
            len(match_objects)
            == 1  # TODO: this does not really make sense here. Should return UserASTContainerNode
        ), "When matching a file tree, we should only return one file (root) as the result"
        assert isinstance(match_objects[0], UserASTFileMixin)
        return match_objects[0]

    if match_objects == []:
        raise RuntimeError(
            "I dont really know what should be return value here. Maybe this should not be possible at all"
        )

    assert isinstance(match_objects, list), isinstance(match_objects, list)

    return UserASTRootContainerNode(children=match_objects)
