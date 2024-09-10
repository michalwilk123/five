from itertools import chain
from typing import Iterable

from flang.exceptions import (
    MatchNotFoundError,
    TextNotParsedError,
    UnknownConstructError,
)
from flang.helpers import create_unique_symbol, emit_function
from flang.structures import (
    FlangConstruct,
    FlangInputReader,
    FlangMatchObject,
    FlangProjectConstruct,
    IntermediateFileObject,
)


class FlangTextProcessor:
    def __init__(
        self,
        flang_object: FlangProjectConstruct,
        root: FlangConstruct = None,
        allow_partial_match: bool = False,
    ) -> any:
        self.root = root or flang_object.root_construct
        self.object = flang_object
        self.allow_partial_match = allow_partial_match

    def match(
        self,
        construct: FlangConstruct,
        input_stream: FlangInputReader,
        start_position=0,  # może nie powinno przyjmować tekstu?
    ) -> FlangMatchObject:
        visible_in_spec = bool(construct.name)
        match_object = None

        match construct.name:
            case "regex":
                matched_text = construct.pattern.match(input_stream.read())
                if not matched_text:
                    raise MatchNotFoundError

                match_object = FlangMatchObject(
                    symbol=construct.location,
                    content=matched_text.group(),
                    visible_in_spec=visible_in_spec,
                )
                input_stream.consume_data(match_object)
                return match_object
            case "text":
                if not input_stream.read().startswith(construct.text):
                    raise MatchNotFoundError

                match_object = FlangMatchObject(
                    symbol=construct.location,
                    content=construct.text,
                    visible_in_spec=visible_in_spec,
                )
                input_stream.consume_data(match_object)

                return match_object
            case _:
                raise UnknownConstructError(construct.name)


class FlangFileProcessor:
    def __init__(
        self,
        flang_object: FlangProjectConstruct,
        root: FlangConstruct = None,
        allow_partial_match: bool = False,
    ) -> any:
        self.root = root or flang_object.root_construct
        self.object = flang_object
        self.allow_partial_match = allow_partial_match

    def match(
        self, construct: FlangConstruct, input_stream: IntermediateFileObject | str
    ) -> FlangMatchObject:
        visible_in_spec = bool(construct.name)
        match_object = None

        match construct.name:
            case "file":
                if not input_stream.startswith(construct.text, start_position):
                    raise MatchNotFoundError

                return FlangMatchObject(
                    symbol=construct.location,
                    content=construct.text,
                    visible_in_spec=visible_in_spec,
                )
            case _:
                raise UnknownConstructError(construct.name)

    def backward(self, spec: FlangMatchObject) -> IntermediateFileObject:
        """
        Powinno sie tutaj sprawdzic czy plik juz istnieje itd. ew go nadpisac
        """
        return self.generate(spec)

    def forward(self, file: str | IntermediateFileObject) -> FlangMatchObject:
        if isinstance(file, str):
            file = IntermediateFileObject.from_path(file)

        return self.match(self.root, file)


class FlangComponentIterator:
    def __init__(
        self,
        construct: FlangConstruct,
        flang_object: FlangProjectConstruct,
        input_stream: FlangInputReader,
    ) -> None:
        self._construct = construct
        self._iterator: Iterable[str] = flang_object.iterate_children(
            self._construct.location
        )
        self._input_stream = input_stream
        self.current = None

    def __next__(self) -> FlangConstruct:
        if self.current is not None and self.current.get_bool_attrib("multi"):
            pass  # use current construct
        else:
            self.current: FlangConstruct = next(self._iterator)

        construct_optional = self.current.get_bool_attrib("optional")
        construct_multiple = self.current.get_bool_attrib("multi")

        if construct_optional or construct_multiple:
            self._input_stream = self._input_stream.copy()

        return self.current

    def __iter__(self):
        return self

    def get_stream(self):
        return self._input_stream

    def match_not_found(self, exc: MatchNotFoundError, matches: list[FlangMatchObject]):
        assert self.current is not None

        cannot_find_more_matches = (
            self.current.get_bool_attrib("multi")
            and matches
            and matches[-1].symbol == self.current.location
        )
        construct_optional = self.current.get_bool_attrib("optional")

        if not (cannot_find_more_matches or construct_optional):
            raise MatchNotFoundError from exc

        if cannot_find_more_matches:
            self.current: FlangConstruct = None

        self._input_stream = self._input_stream.previous


class FlangCoreProcessor:
    """
    Implements core constructs
    """

    def match(
        self, construct: FlangConstruct, input_stream: FlangInputReader
    ) -> tuple[FlangMatchObject]:
        """
        INPUT STREAM SHOULD BE IMMUTABLE !!!
        It should work like the length like before and only be an extension
        for files
        """
        input_stream = input_stream.copy()
        visible_in_spec = bool(construct.name)
        match_object = None

        match construct.name:
            case "component":
                matches = []

                for child in self.object.iterate_children(construct.location):
                    match_object = self.match(child, input_stream)
                    matches.append(match_object)

                matches = list(chain(matches))

                if (
                    self.object.root == construct.location
                    and not self.allow_partial_match
                    and input_stream.read()
                ):
                    raise TextNotParsedError

                return FlangMatchObject(
                    symbol=construct.location,
                    content=matches,
                    visible_in_spec=visible_in_spec,
                )
            case "choice":
                matches = []
                for child in self.object.iterate_children(construct.location):
                    try:
                        matches.append(self.match(child, input_stream))
                    except MatchNotFoundError:
                        pass

                if not matches:
                    raise MatchNotFoundError

                return [max(matches, key=len)]
            case "event":
                name = construct.get_attrib("name", None) or create_unique_symbol(
                    "_flang_function"
                )
                args = construct.get_attrib("args", "").split(",")
                body = construct.text
                emit_function(name, args, body)
            case _:
                raise UnknownConstructError(construct.name)


class FlangProjectProcessor(FlangCoreProcessor, FlangTextProcessor, FlangFileProcessor):
    def match(self, construct: FlangConstruct, input_stream: str):
        klass = self.__class__

        for base in klass.__bases__:
            try:
                match_object = base.match(self, construct, input_stream)
            except UnknownConstructError:
                continue
            else:
                break

        return match_object

    def generate(self, spec: FlangMatchObject) -> FlangInputReader:
        construct = self.object.find_symbol(spec.symbol)

        match construct.name:
            case "component":
                return "".join(self.generate(child_match) for child_match in spec.content)
            case "choice":
                raise RuntimeError
            case "regex":
                return spec.content
            case "text":
                return spec.content

        raise RuntimeError

    def backward(self, spec: FlangMatchObject) -> FlangInputReader:
        return self.generate(spec)

    def forward(self, sample: FlangInputReader) -> FlangMatchObject:
        return self.match(self.root, sample)
