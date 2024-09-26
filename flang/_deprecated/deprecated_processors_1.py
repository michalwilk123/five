from functools import cmp_to_key

from flang._deprecated.structures_depr import (
    DEPRECATED_FlangInputReader,
    FlangConstruct,
    FlangProjectConstruct,
    FlangTextMatchObject,
    IntermediateFileObject,
)
from flang.utils.common import create_unique_symbol, emit_function
from flang.utils.exceptions import (
    MatchNotFoundError,
    SymbolNotFoundError,
    TextNotParsedError,
    UnknownConstructError,
)


def match_single_core(
    flang_object: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: DEPRECATED_FlangInputReader,
):
    visible_in_spec = bool(construct.name)

    match construct.name:
        case "sequence":
            matches = []

            for child in flang_object.iterate_children(construct.location):
                match_objects, reader = match_flang_construct(flang_object, child, reader)
                matches += match_objects

            return FlangTextMatchObject(
                identifier=construct.location,
                construct=construct.name,
                content=matches,
                visible_in_spec=visible_in_spec,
            )
        case "choice":
            matches = []
            readers = []

            for child in flang_object.iterate_children(construct.location):
                try:
                    match_objects, reader = match_flang_construct(
                        flang_object, child, reader
                    )
                    matches += match_objects
                    readers.append(reader)
                    reader = reader.previous
                except MatchNotFoundError:
                    pass

            if not matches:
                raise MatchNotFoundError

            max_reader = max(readers, key=cmp_to_key(DEPRECATED_FlangInputReader.compare))
            return matches[readers.index(max_reader)]

        case "event":
            name = construct.get_attrib("name", None) or create_unique_symbol(
                "_flang_function"
            )
            args = construct.get_attrib("args", "").split(",")
            body = construct.text
            emit_function(name, args, body)
        case "use":
            target_location = construct.get_attrib("ref")
            location = construct.location

            try:
                target_construct = flang_object.find_construct_by_path(
                    target_location, location
                )

                if not target_construct.visible:  # ugly
                    target_construct.visible = True
            except SymbolNotFoundError:
                raise NotImplementedError(
                    "tutaj w starych wersjach five parsowany zostaje od zera "
                    "plik którego brakuje. To ma działać jezeli formatka jest rozrzucona "
                    "na kilka plikow"
                )

            matches, reader = match_flang_construct(
                flang_object, target_construct, reader
            )

            return FlangTextMatchObject(
                identifier=construct.location,
                construct=construct.name,
                content=matches,
                visible_in_spec=visible_in_spec,
            )
        case _:
            raise UnknownConstructError(construct.name)


def match_single_text(
    flang_object: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: DEPRECATED_FlangInputReader,  # TODO: wyrzuc flang object
):
    visible_in_spec = bool(construct.name)
    match_object = None
    # TODO: gdzieś tutaj powinno się robić łączenie

    match construct.name:
        case "regex":
            matched_text = construct.pattern.match(reader.read())

            if not matched_text:
                raise MatchNotFoundError

            if not matched_text.group():
                raise RuntimeError(
                    "We have matched an empty object which does not make any sense. Please fix the template to not match such text. Like what would you expect after matching nothing?"
                )

            match_object = FlangTextMatchObject(
                identifier=construct.location,
                construct=construct.name,
                content=matched_text.group(),
                visible_in_spec=visible_in_spec,
            )
            return match_object
        case "text":
            if not reader.read().startswith(construct.text):
                raise MatchNotFoundError

            match_object = FlangTextMatchObject(
                identifier=construct.location,
                construct=construct.name,
                content=construct.text,
                visible_in_spec=visible_in_spec,
            )
            return match_object
        case "connection":
            assert 0, "not implemented yet..."
        case _:
            raise UnknownConstructError(construct.name)


def match_single_file(
    flang_object: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: DEPRECATED_FlangInputReader,
):
    if construct.name != "file":
        raise UnknownConstructError(construct.name)

    visible_in_spec = bool(construct.name)
    current_files: list[IntermediateFileObject] = reader.read()

    pattern = construct.get_attrib("pattern")
    variant = construct.get_attrib("variant", "filename")

    matched_file = IntermediateFileObject.get_first_matched_file(
        current_files, pattern, variant
    )

    if not matched_file:
        raise MatchNotFoundError

    assert len(construct.children) == 1, "Files should contain only one construct"
    child = next(flang_object.iterate_children(construct.location))
    new_reader = matched_file.get_input_reader()  # ugly

    match_object = FlangTextMatchObject(
        identifier=construct.location,
        construct=construct.name,
        content=match_flang_construct(
            flang_object, child, new_reader, always_return_list=False, check=True
        )[0],
        visible_in_spec=visible_in_spec,
        metadata={"filename": new_reader.meta["filename"]},
    )

    return match_object


def match_single(
    flang_object: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: DEPRECATED_FlangInputReader,
):
    matchers = (match_single_core, match_single_text, match_single_file)

    for matcher in matchers:
        try:
            match_object = matcher(flang_object, construct, reader)
        except UnknownConstructError:
            continue
        else:
            break

    return match_object


def match_flang_construct(
    flang_object: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: DEPRECATED_FlangInputReader,
    always_return_list: bool = True,
    check: bool = False,
):
    reader = reader.copy()
    matches = []
    try:
        match_object = match_single(flang_object, construct, reader)
        matches.append(match_object)
        reader.consume_data(match_object)
    except MatchNotFoundError as e:
        if not construct.get_bool_attrib("optional"):
            raise MatchNotFoundError from e
        else:
            reader = reader.previous

    while construct.get_bool_attrib("multi"):
        reader = reader.copy()
        try:
            match_object = match_single(flang_object, construct, reader)
            matches.append(match_object)
            reader.consume_data(match_object)
        except MatchNotFoundError as e:
            reader = reader.previous
            break

    if check and reader.read():
        print(f"Text left: {reader.read()}")
        raise TextNotParsedError

    if always_return_list or construct.get_bool_attrib("multi"):
        return matches, reader

    if check:
        assert len(matches) == 1

    return matches[0], reader


def match_flang_raw(  # bad name
    flang_object: FlangProjectConstruct,
    construct: FlangConstruct,
    reader: DEPRECATED_FlangInputReader,
    return_list: bool = False,
):
    matched, reader = match_flang_construct(flang_object, construct, reader)
    if reader.read():
        print(f"Text left: {reader.read()}")
        raise TextNotParsedError

    if construct.get_bool_attrib("multi") or return_list:
        return matched

    assert len(matched) == 1
    return matched[0]


class FlangProjectProcessor:
    def __init__(self, flang_object: FlangProjectConstruct) -> None:
        self.flang_object = flang_object

    def backward(self, spec: FlangTextMatchObject) -> DEPRECATED_FlangInputReader:
        return self.generate(spec)

    def forward(self, sample: DEPRECATED_FlangInputReader) -> FlangTextMatchObject:
        return match_flang_construct(
            self.flang_object,
            self.flang_object.root_construct,
            sample,
            always_return_list=False,
            check=True,
        )[0]
