from functools import cmp_to_key

from flang.exceptions import MatchNotFoundError, TextNotParsedError, UnknownConstructError
from flang.helpers import create_unique_symbol, emit_function
from flang.structures import (
    FlangConstruct,
    FlangInputReader,
    FlangObject,
    FlangTextMatchObject,
)


def match_single_core(
    flang_object: FlangObject, construct: FlangConstruct, reader: FlangInputReader
):
    # input_stream = input_stream.save_checkpoint()
    visible_in_spec = bool(construct.name)

    match construct.construct_name:
        case "component":
            matches = []

            for child in flang_object.iterate_children(construct.location):
                match_objects, reader = match_flang_construct(flang_object, child, reader)
                matches += match_objects

            if flang_object.root == construct.location and reader.read():
                print(f"Text left: {reader.read()}")
                raise TextNotParsedError

            return FlangTextMatchObject(
                symbol=construct.location,
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

            max_reader = max(readers, key=cmp_to_key(FlangInputReader.compare))
            return matches[readers.index(max_reader)]

        case "event":
            name = construct.get_attrib("name", None) or create_unique_symbol(
                "_flang_function"
            )
            args = construct.get_attrib("args", "").split(",")
            body = construct.text
            emit_function(name, args, body)
        case _:
            raise UnknownConstructError(construct.construct_name)


def match_single_text(
    flang_object: FlangObject, construct: FlangConstruct, reader: FlangInputReader
):
    visible_in_spec = bool(construct.name)
    match_object = None

    match construct.construct_name:
        case "regex":
            matched_text = construct.pattern.match(reader.read())
            if not matched_text:
                raise MatchNotFoundError

            match_object = FlangTextMatchObject(
                symbol=construct.location,
                content=matched_text.group(),
                visible_in_spec=visible_in_spec,
            )
            return match_object
        case "text":
            if not reader.read().startswith(construct.text):
                raise MatchNotFoundError

            match_object = FlangTextMatchObject(
                symbol=construct.location,
                content=construct.text,
                visible_in_spec=visible_in_spec,
            )

            return match_object
        case _:
            raise UnknownConstructError(construct.construct_name)


def match_single_file(
    flang_object: FlangObject, construct: FlangConstruct, reader: FlangInputReader
):
    visible_in_spec = bool(construct.name)

    match construct.construct_name:
        case "file":
            if not reader.read().startswith(construct.text):
                raise MatchNotFoundError

            return FlangTextMatchObject(
                symbol=construct.location,
                content=construct.text,
                visible_in_spec=visible_in_spec,
            )
        case _:
            raise UnknownConstructError(construct.construct_name)


def match_single(
    flang_object: FlangObject, construct: FlangConstruct, reader: FlangInputReader
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
    flang_object: FlangObject, construct: FlangConstruct, reader: FlangInputReader
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

    return matches, reader


class FlangProjectProcessor:
    def __init__(self, flang_object: FlangObject) -> None:
        self.flang_object = flang_object

    def backward(self, spec: FlangTextMatchObject) -> FlangInputReader:
        return self.generate(spec)

    def forward(self, sample: FlangInputReader) -> FlangTextMatchObject:
        matched, _reader = match_flang_construct(
            self.flang_object, self.flang_object.root_construct, sample
        )
        assert len(matched) == 1
        return matched[0]
