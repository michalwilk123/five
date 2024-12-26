import re

from flang.structures import (
    BaseUserAST,
    FlangAST,
    FlangFileInputReader,
    InputReaderInterface,
    UserBranch,
    UserLeaf,
    UserRoot,
)
from flang.utils.exceptions import (
    ComplexMatchNotFound,
    FileMatchNotFound,
    MatchNotFoundError,
    NoMoreDataException,
    TextMatchNotFound,
    TextNotParsedError,
    UnknownFlangNodeError,
)
from flang.utils.regex import lex_storage

from .utils import (
    create_branch_with_children,
    get_resolved_children,
    is_flang_node_hidden,
    resolve_use_node,
)


def _match_text_with_regex(text: str, pattern: str) -> str | None:
    pattern = lex_storage.create_pattern(pattern)
    re_match = re.match(pattern, text)

    if re_match is not None:
        re_match = re_match.group()

    return re_match


def _match_text_with_text(text: str, pattern: str) -> str | None:
    if text.startswith(pattern):
        return pattern
    return None


def _is_file_matched(filename: str, pattern: str, regex: bool) -> bool:
    if not regex:
        return filename == pattern

    pattern = pattern.replace(".", r"\.")
    pattern = pattern.replace(r"\\.", ".")  # fix patterns broken by above code
    pattern = lex_storage.create_pattern(pattern)
    return re.match(pattern, filename) is None


def match_on_sequence(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> UserBranch:
    if not (children := get_resolved_children(flang_ast)):
        raise RuntimeError("Cannot create sequence from empty list of objects")

    matches = []

    try:
        for child in children:
            match_objects, reader = match_flang_ast_node(child, reader)

            matches += match_objects
    except MatchNotFoundError as e:
        raise ComplexMatchNotFound(
            f"Could not match sequence of flang_asts: {flang_ast.type or flang_ast.location}"
        ) from e

    return create_branch_with_children(flang_ast.name, flang_ast.location, matches, None)


def match_on_choice(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> UserBranch:
    if not (children := get_resolved_children(flang_ast)):
        raise RuntimeError("Cannot choose from empty list of objects")

    max_matches, max_reader, max_child = None, None, None

    for child in children:
        try:
            match_objects, new_reader = match_flang_ast_node(child, reader)
            new_match_found = (
                max_matches is None or new_reader.get_key() > max_reader.get_key()
            )

            if new_match_found:
                max_matches, max_reader, max_child = match_objects, new_reader, child

        except MatchNotFoundError:
            pass

    if max_matches is None:
        raise ComplexMatchNotFound(
            f"Could not match any flang_ast from: {[child.location for child in children]} text: {reader.read()[:15]}"
        )

    match_object = create_branch_with_children(
        flang_ast.name, flang_ast.location, max_matches, None
    )

    if max_child.get_bool_attrib("terminal"):
        # NOTE: This should be done in more clever way imo. For example by using sth like Monads??
        match_object.is_terminal = None

    return match_object


def match_on_text(flang_ast: FlangAST, reader: InputReaderInterface) -> UserLeaf:
    if flang_ast.type != "text":
        raise UnknownFlangNodeError("Not text flang_ast")

    content = None
    flang_ast_text = flang_ast.get_attrib("value", flang_ast.text)
    text_to_match = reader.read()

    if is_regex := flang_ast.get_bool_attrib("regex"):
        content = _match_text_with_regex(text_to_match, flang_ast_text)
    else:
        content = _match_text_with_text(text_to_match, flang_ast_text)

    if content is None:
        raise TextMatchNotFound(
            f'Could not match text ({is_regex=}) pattern: "{flang_ast_text}" with text: "{reader.read()[:15]}"'
        )

    return UserLeaf(
        name=flang_ast.name, flang_ast_path=flang_ast.location, content=content
    )


def match_on_file(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> UserBranch:
    assert isinstance(reader, FlangFileInputReader)

    try:
        filename = reader.read()
    except NoMoreDataException as e:
        raise FileMatchNotFound("No files found") from e

    pattern = flang_ast.get_attrib("pattern")
    regex = flang_ast.get_bool_attrib("regex")

    if not _is_file_matched(filename, pattern, regex):
        raise FileMatchNotFound(
            f'Could not match filename pattern: "{pattern}" {regex=} with current '
            f'file : "{filename}"'
        )

    child = flang_ast.first_child
    sub_reader = reader.get_nested_reader(filename)
    content, out_reader = match_flang_ast_node(child, sub_reader)

    if not out_reader.is_empty():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    return create_branch_with_children(
        flang_ast.name, flang_ast.location, content, filename
    )


def match_on_single_node(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> BaseUserAST:
    matchers = {
        "sequence": match_on_sequence,
        "choice": match_on_choice,
        "text": match_on_text,
        "file": match_on_file,
    }
    match_fn = matchers.get(flang_ast.type)

    if match_fn is None:
        raise UnknownFlangNodeError

    match_object = match_fn(flang_ast, reader)

    if match_object.size() == 0:
        raise MatchNotFoundError(
            f"Cannot match a node without content! Match object that matched nothing: {match_object.flang_ast_path}"
        )

    return match_object


def match_flang_ast_node(
    flang_ast: FlangAST,
    reader: InputReaderInterface,
) -> tuple[list[BaseUserAST], InputReaderInterface]:
    if alias_name := flang_ast.get_attrib("alias"):
        flang_ast.create_alias(alias_name)

    if is_flang_node_hidden(flang_ast):
        return [], reader

    if flang_ast.type == "use":
        flang_ast = resolve_use_node(flang_ast)

    reader = reader.copy()
    matches = []
    # possible_tries = flang_ast.get_bool_attrib("optional") then [0] <- moze na cos takiego przepisac

    try:
        match_object = match_on_single_node(flang_ast, reader)
        matches.append(match_object)
        reader.consume_data(match_object)
    except MatchNotFoundError as e:
        if not flang_ast.get_bool_attrib("optional"):
            raise e

        return [], reader.previous

    while flang_ast.get_bool_attrib("multi"):
        reader = reader.copy()
        try:
            match_object = match_on_single_node(flang_ast, reader)
            matches.append(match_object)
            reader.consume_data(match_object)

            if hasattr(match_object, "is_terminal"):
                break
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
        # assert isinstance(match_objects[0], UserASTFileMixin)
        return match_objects[0]

    if match_objects == []:
        raise RuntimeError(
            "I dont really know what should be return value here. Maybe this should not be possible at all"
        )

    assert isinstance(match_objects, list), isinstance(match_objects, list)

    root = UserRoot()

    for match in match_objects:
        root.add_node(match)

    return root
