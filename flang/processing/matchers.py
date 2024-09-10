import re
from functools import cmp_to_key

from flang.exceptions import (
    MatchNotFoundError,
    SkipConstructException,
    SymbolNotFoundError,
    TextNotParsedError,
    UnknownConstructError,
)
from flang.helpers import BUILTIN_PATTERNS, NAMED_BUILTIN_PATTERNS, emit_function
from flang.structures import (
    FlangConstruct,
    FlangInputReader,
    FlangMatchObject,
    FlangProjectConstruct,
    IntermediateFileObject,
)

__all__ = ["match_flang_construct"]


class TextMatchNotFound(MatchNotFoundError): ...


class ComplexMatchNotFound(MatchNotFoundError): ...


class FileMatchNotFound(MatchNotFoundError): ...


def _match_on_complex_construct(
    project_construct: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: FlangInputReader,
) -> FlangMatchObject:
    match construct.name:
        case "sequence":
            matches = []

            try:
                for child in project_construct.iterate_children(construct.location):
                    match_objects, reader = match_flang_construct(
                        project_construct, child, reader
                    )
                    assert isinstance(match_objects, list), "TODO niepotrzebna asercja!"

                    matches += match_objects
            except MatchNotFoundError as e:
                raise ComplexMatchNotFound(
                    f"Could not match sequence of constructs: {construct.name or construct.location}"
                ) from e

            return FlangMatchObject(
                symbol=construct.location,
                construct=construct.name,
                content=matches,
            )
        case "choice":
            matches = []
            readers = []

            for child in project_construct.iterate_children(construct.location):
                try:
                    match_objects, reader = match_flang_construct(
                        project_construct, child, reader
                    )
                    assert isinstance(match_objects, list), "TODO niepotrzebna asercja!"

                    matches += match_objects
                    readers.append(reader)
                    reader = reader.previous
                except MatchNotFoundError:
                    pass

            if not matches:
                raise ComplexMatchNotFound(
                    f"Could not match any construct from: {construct.name or construct.location}"
                )

            max_reader = max(readers, key=cmp_to_key(FlangInputReader.compare))
            return matches[readers.index(max_reader)]

        case "event":
            # name = construct.get_attrib("name", None) or create_unique_symbol(
            #     "_flang_function"
            # )
            name = construct.get_attrib("name", "dsajndkjasnkjd")
            args = construct.get_attrib("args", "").split(",")
            body = construct.text
            # emit_function(name, args, body)
            raise NotImplementedError
        case "use":
            target_location = construct.get_attrib("ref")
            location = construct.location

            try:
                target_construct = project_construct.find_construct_by_path(
                    target_location, location
                )

                attributes = {**construct.attributes, "visible": True}
                del attributes["ref"]
            except SymbolNotFoundError:
                raise NotImplementedError(
                    "tutaj w starych wersjach five parsowany zostaje od zera "
                    "plik którego brakuje. To ma działać jezeli formatka jest rozrzucona "
                    "na kilka plikow"
                )

            matches, reader = match_flang_construct(
                project_construct, target_construct, reader
            )
            assert isinstance(matches, list), "TODO niepotrzebna asercja!"

            return FlangMatchObject(
                symbol=construct.location,
                construct=construct.name,
                content=matches,
            )
        case _:
            raise UnknownConstructError("Not complex construct")


def _match_on_text(
    project_construct: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: FlangInputReader,
) -> FlangMatchObject:
    match_object = None
    # TODO: gdzieś tutaj powinno się robić łączenie
    text_to_match = reader.read()
    construct_text = construct.get_attrib("value", construct.text)

    #

    match construct.name:
        case "regex":
            assert isinstance(text_to_match, str) and isinstance(construct_text, str)

            construct_pattern = construct_text.format(**BUILTIN_PATTERNS)
            matched_text = re.match(construct_pattern, text_to_match)
            # matched_text = re.match(construct_pattern, reader.read())

            if not matched_text:
                raise TextMatchNotFound(
                    f'Could not match regex pattern: "{construct_pattern}" with text: "{reader.read()[:15]}"'
                )

            if not matched_text.group():
                raise RuntimeError(
                    "We have matched an empty object which does not make any sense. Please fix the template to not match such text. Like what would you expect after matching nothing?"
                )

            match_object = FlangMatchObject(
                symbol=construct.location,
                construct=construct.name,
                content=matched_text.group(),
            )
            return match_object
        case "text":
            assert isinstance(text_to_match, str) and isinstance(construct_text, str)

            if not text_to_match.startswith(construct_text):
                raise TextMatchNotFound(
                    f'Could not match text pattern: "{construct_text}" with '
                    f'text: "{reader.read()[:len(construct_text)]}"'
                )

            match_object = FlangMatchObject(
                symbol=construct.location,
                construct=construct.name,
                content=construct_text,
            )
            return match_object
        case _:
            raise UnknownConstructError("Not text construct")


def _match_on_file(
    project_construct: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: FlangInputReader,
) -> FlangMatchObject:
    if construct.name != "file":
        raise UnknownConstructError("Not file construct")

    current_files = reader.read()
    assert isinstance(current_files, list), "TODO: Niepotrzebna asercja!"

    pattern = construct.get_attrib("pattern")
    variant = construct.get_attrib("variant", "filename")

    matched_file = IntermediateFileObject.get_first_matched_file(
        current_files, pattern, variant
    )

    if not matched_file:
        raise FileMatchNotFound(
            f'Could not match filename pattern: "{pattern}" variant: {variant} with available '
            f'files in directory: "{[f.path.name for f in current_files]}"'
        )

    assert len(construct.children) == 1, "Files should contain only one construct"
    child = next(project_construct.iterate_children(construct.location))
    new_reader = matched_file.get_input_reader()  # ugly
    content = match_flang_construct(
        project_construct, child, new_reader, always_return_list=False, check=True
    )[0]
    assert new_reader.meta and new_reader.meta["filename"], "TODO: NIEPOTRZEBNA ASERCJA"

    filename = new_reader.meta["filename"]  # ugly
    match_object = FlangMatchObject(
        symbol=construct.location,
        construct=construct.name,
        content=[content] if isinstance(content, FlangMatchObject) else content,  # ugly
        metadata={"filename": filename},
    )

    return match_object


def _match_against_all_construct_variants(
    project_construct: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: FlangInputReader,
) -> FlangMatchObject:
    matchers = (_match_on_complex_construct, _match_on_text, _match_on_file)
    match_object = None

    for matcher in matchers:
        try:
            match_object = matcher(project_construct, construct, reader)
        except UnknownConstructError:
            continue
        else:
            break

    if match_object is None:
        raise UnknownConstructError

    return match_object


def match_flang_construct(
    project_construct: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: FlangInputReader,
    always_return_list: bool = True,
    check: bool = False,
) -> tuple[list[FlangMatchObject] | FlangMatchObject, FlangInputReader]:
    reader = reader.copy()
    matches = []

    try:
        match_object = _match_against_all_construct_variants(
            project_construct, construct, reader
        )
        matches.append(match_object)
        reader.consume_data(match_object)
    except MatchNotFoundError as e:
        # TODO: this looks ugly. A lot of additional steps needed if construct is optional
        if not construct.get_bool_attrib("optional"):
            raise e
        else:
            reader = reader.previous
    except SkipConstructException:
        reader = reader.previous

    while construct.get_bool_attrib("multi"):
        reader = reader.copy()
        try:
            match_object = _match_against_all_construct_variants(
                project_construct, construct, reader
            )
            matches.append(match_object)
            reader.consume_data(match_object)
        except MatchNotFoundError as e:
            reader = reader.previous
            break

    if check and reader.read():
        raise TextNotParsedError(f"Text left: {reader.read()}")

    if always_return_list or construct.get_bool_attrib("multi"):
        return matches, reader

    if check:
        assert len(matches) == 1

    return matches[0], reader
