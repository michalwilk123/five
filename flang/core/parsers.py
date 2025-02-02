import re

from flang.structures import (
    FlangAST,
    FlangBranch,
    FlangFileInputReader,
    FlangLeaf,
    FlangRoot,
    InputReaderInterface,
    TemplateTree,
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

from .utils import create_branch_with_children, get_available_children, resolve_use_node


def _match_text_with_regex(text: str, pattern: str) -> str | None:
    pattern = lex_storage.create_pattern(pattern)
    re_match = re.match(pattern, text)

    if re_match is not None:
        re_match = re_match.group()

    return re_match


def _is_file_matched(filename: str, pattern: str, regex: bool) -> bool:
    if not regex:
        return filename == pattern

    pattern = pattern.replace(".", r"\.")
    pattern = pattern.replace(r"\\.", ".")  # fix patterns broken by above code
    pattern = lex_storage.create_pattern(pattern)
    return re.match(pattern, filename) is None


def match_on_sequence(
    template_tree: TemplateTree,
    reader: InputReaderInterface,
    node_name: str,
) -> FlangBranch:
    if not (children := get_available_children(template_tree)):
        if template_tree.children:
            raise RuntimeError(
                "The <sequence> node contains only hidden objects. At least one object must be visible"
            )

        raise RuntimeError(
            "The <sequence> node has no content and it does not make sense to exist."
        )

    matches = []

    try:
        for child in children:
            match_objects, reader = match_template_tree_node(child, reader)
            matches += match_objects
    except MatchNotFoundError as e:
        raise ComplexMatchNotFound(
            f"Could not match sequence of template_trees: {template_tree.type} {template_tree.location}"
        ) from e

    return create_branch_with_children(node_name, template_tree.location, matches, None)


def match_on_choice(
    template_tree: TemplateTree,
    reader: InputReaderInterface,
    node_name: str,
) -> FlangBranch:
    if not (children := get_available_children(template_tree)):
        raise RuntimeError("Cannot choose from empty list of objects")

    max_matches, max_reader, max_child = None, None, None

    for child in children:
        try:
            match_objects, new_reader = match_template_tree_node(child, reader)
            new_match_found = (
                max_matches is None or new_reader.get_key() > max_reader.get_key()
            )

            if new_match_found:
                max_matches, max_reader, max_child = match_objects, new_reader, child

        except MatchNotFoundError:
            pass

    if max_matches is None:
        raise ComplexMatchNotFound(
            f"Could not match any template_tree from: {[child.location for child in children]} text: {reader.read()[:15]}"
        )

    match_object = create_branch_with_children(
        node_name, template_tree.location, max_matches, None
    )

    if max_child.get_bool_attrib("terminal"):
        # NOTE: This should be done in more clever way imo. For example by using sth like Monads??
        match_object.is_terminal = None

    return match_object


def match_on_text(
    template_tree: TemplateTree, reader: InputReaderInterface, node_name: str
) -> FlangLeaf:
    if template_tree.type != "text":
        raise UnknownFlangNodeError("Not text template_tree")

    content = None
    template_tree_text = template_tree.get_attrib("value", template_tree.text)
    text_to_match = reader.read()

    if is_regex := template_tree.get_bool_attrib("regex"):
        content = _match_text_with_regex(text_to_match, template_tree_text)
    else:
        content = (
            template_tree_text if text_to_match.startswith(template_tree_text) else None
        )

    if content is None:
        raise TextMatchNotFound(
            f'Could not match text ({is_regex=}) pattern: "{template_tree_text}" with text: "{reader.read()[:15]}"'
        )

    return FlangLeaf(name=node_name, template_id=template_tree.location, content=content)


def match_on_file(
    template_tree: TemplateTree,
    reader: InputReaderInterface,
    node_name: str,
) -> FlangBranch:
    assert isinstance(reader, FlangFileInputReader)

    try:
        filename = reader.read()
    except NoMoreDataException as e:
        raise FileMatchNotFound("No files found") from e

    pattern = template_tree.get_attrib("pattern")
    regex = template_tree.get_bool_attrib("regex")

    if not _is_file_matched(filename, pattern, regex):
        raise FileMatchNotFound(
            f'Could not match filename pattern: "{pattern}" {regex=} with current '
            f'file : "{filename}"'
        )

    assert len(template_tree.children), "file node has to have only 1 child"
    child = template_tree.first_child
    sub_reader = reader.get_nested_reader(filename)
    content, out_reader = match_template_tree_node(child, sub_reader)

    if not out_reader.is_empty():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    return create_branch_with_children(
        node_name, template_tree.location, content, filename
    )


def match_on_single_node(
    template_tree: TemplateTree,
    reader: InputReaderInterface,
    node_name: str,
) -> FlangAST:
    matchers = {
        "sequence": match_on_sequence,
        "choice": match_on_choice,
        "text": match_on_text,
        "file": match_on_file,
    }
    match_fn = matchers.get(template_tree.type)

    if match_fn is None:
        raise UnknownFlangNodeError

    match_object = match_fn(template_tree, reader, node_name)

    if match_object.size() == 0:
        raise MatchNotFoundError(
            f"Cannot match a node without content! Match object that matched nothing: {match_object.template_id}"
        )

    return match_object


def match_template_tree_node(
    template_tree: TemplateTree,
    reader: InputReaderInterface,
) -> tuple[list[FlangAST], InputReaderInterface]:
    # If i dont do this
    # i will get duplicates of the same object
    original_template_tree = template_tree

    if template_tree.type == "use":
        template_tree = resolve_use_node(template_tree)

    reader = reader.copy()
    matches = []
    node_name = original_template_tree.get_id()
    # possible_number_of_samples = template_tree.get_bool_attrib("optional") then [0] <- moze na cos takiego przepisac

    try:
        match_object = match_on_single_node(template_tree, reader, node_name)
        matches.append(match_object)
        reader.consume_data(match_object)
    except MatchNotFoundError as e:
        if not template_tree.get_bool_attrib("optional"):
            raise e

        return [], reader.previous

    while template_tree.get_bool_attrib("multi"):
        reader = reader.copy()
        try:
            match_object = match_on_single_node(template_tree, reader, node_name)
            matches.append(match_object)
            reader.consume_data(match_object)

            if hasattr(match_object, "is_terminal"):
                break
        except MatchNotFoundError as e:
            reader = reader.previous
            break

    if original_template_tree != template_tree:
        for match in matches:
            match.template_id = original_template_tree.location

    return matches, reader


def parse_user_language(
    template_tree: TemplateTree, reader: InputReaderInterface
) -> tuple[list[FlangAST], InputReaderInterface]:

    match_objects, out_reader = match_template_tree_node(template_tree.root, reader)

    if not out_reader.is_empty():
        raise TextNotParsedError(f"Text left: {out_reader.read()}")

    if template_tree.root.type == "file":
        # TODO: this does not really make sense here. Should return UserASTContainerNode
        assert (
            len(match_objects) == 1
        ), "When matching a file tree, we should only return one file (root) as the result"
        return match_objects[0]

    if match_objects == []:
        raise RuntimeError(
            "I dont really know what should be return value here. Maybe this should not be possible at all"
        )

    assert isinstance(match_objects, list), isinstance(match_objects, list)

    root = FlangRoot()

    for match in match_objects:
        root.add_node(match)

    return root
