import re
from enum import Enum, auto

from flang.structures.input import BaseFlangInputReader, IntermediateFileObject
from flang.structures.spec import (
    FlangComplexMatchObject,
    FlangDirectoryMatchObject,
    FlangFileMatch,
    FlangFlatFileMatchObject,
)
from flang.utils.common import BUILTIN_PATTERNS
from flang.utils.exceptions import (
    ComplexMatchNotFound,
    FileMatchNotFound,
    MatchNotFoundError,
    SkipConstructException,
    SymbolNotFoundError,
    TextMatchNotFound,
    TextNotParsedError,
    UnknownConstructError,
)

from ..structures import (
    FlangConstruct,
    FlangFileInputReader,
    FlangMatchObject,
    FlangTextMatchObject,
)


class LinkVariant(Enum):  # TODO: not needed anymore?
    DEFINITION = auto()
    REFERENCE = auto()


class ProjectParsingRuntime:
    def __init__(self, path: str, extra_checks: bool = False) -> None:
        self.path = path
        self.root = ""
        self.symbol_table: dict[str, FlangConstruct] = {}
        self.symbol_occurence_counter: dict[str, int] = {}
        self.extra_checks = extra_checks

    def find_symbol(self, symbol: str) -> FlangConstruct:
        return self.symbol_table[symbol]

    def add_symbol(self, symbol: str, constr: FlangConstruct, override=False):
        if symbol in self.symbol_table and not override:
            raise RuntimeError(f"Symbol {symbol} already exists!")
        self.symbol_table[symbol] = constr

    def _get_occurence_value(self, key: str) -> int:
        if key not in self.symbol_occurence_counter:
            self.symbol_occurence_counter[key] = 0
            return 0

        self.symbol_occurence_counter[key] += 1
        return self.symbol_occurence_counter[key]

    def _generate_symbol_for_match_object(self, construct_location: str) -> str:
        occurence_counter_symbol = f"MatchObject({construct_location})"
        occurence_no = self._get_occurence_value(occurence_counter_symbol)
        return "{}[{}]".format(construct_location, occurence_no)

    def generate_symbol_for_match_object(self, construct: FlangConstruct) -> str:
        return self._generate_symbol_for_match_object(construct.location)

    def generate_symbol_for_construct(
        self, element_identifier: str, parent_location: str, allow_duplicates: bool
    ) -> str:
        location = (
            f"{parent_location}.{element_identifier}"
            if parent_location
            else f"{self.path}:{element_identifier}"
        )

        if allow_duplicates == False:
            if location in self.symbol_occurence_counter:
                raise RuntimeError(
                    f"There cannot be more than one object named {location} in parent object. Please rename one of objects"
                )

            return location

        occurence_value = self._get_occurence_value(location)

        return "{}@{}".format(location, occurence_value)

    def iterate_children(self, symbol: str):
        constr = self.find_symbol(symbol)

        for child in constr.children:
            child_constr = self.find_symbol(child)

            if not child_constr.get_bool_attrib("visible", True):
                continue

            yield child_constr

    @property
    def root_construct(self) -> FlangConstruct:
        return self.find_symbol(self.root)

    def find_construct_by_path(
        self, reference_path: str, current_path: str = ""
    ) -> FlangConstruct:
        is_symbol_external = ":" in reference_path
        is_symbol_relative = reference_path.startswith(".") and not is_symbol_external

        if is_symbol_relative and not current_path:
            raise RuntimeError

        if is_symbol_external:
            try:
                return self.find_symbol(reference_path)
            except KeyError as e:
                raise SymbolNotFoundError from e
        elif is_symbol_relative:
            path_without_dots = reference_path.lstrip(".")
            backward_steps = len(reference_path) - len(path_without_dots)

            filename, local_path = current_path.split(":")
            target_path = ".".join(
                local_path.split(".")[:-backward_steps] + [path_without_dots]
            )
            full_target_path = "%s:%s" % (filename, target_path)
            return self.find_construct_by_path(full_target_path)

        raise RuntimeError(f"Unknown path to constuct: {reference_path}")

    def _match_on_complex_construct(
        self,
        construct: FlangConstruct,
        reader: BaseFlangInputReader,
    ) -> FlangMatchObject:
        match construct.name:
            case "sequence":
                matches = []

                try:
                    for child in self.iterate_children(construct.location):
                        match_objects, reader = self._match_flang_construct(
                            child, reader, check_if_all_text_parsed=False
                        )

                        matches += match_objects
                except MatchNotFoundError as e:
                    raise ComplexMatchNotFound(
                        f"Could not match sequence of constructs: {construct.name or construct.location}"
                    ) from e

                return FlangComplexMatchObject(
                    identifier=self.generate_symbol_for_match_object(construct),
                    content=matches,
                )
            case "choice":
                matches = []
                readers = []

                for child in self.iterate_children(construct.location):
                    try:
                        match_objects, reader = self._match_flang_construct(
                            child, reader, check_if_all_text_parsed=False
                        )

                        matches += match_objects
                        readers.append(reader)
                        reader = reader.previous
                    except MatchNotFoundError:
                        pass

                if not matches:
                    raise ComplexMatchNotFound(
                        f"Could not match any construct from: {construct.name or construct.location}"
                    )

                max_reader = max(readers, key=lambda it: it.get_key())
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
                    target_construct = self.find_construct_by_path(
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

                return self._match_against_all_construct_variants(
                    target_construct, reader
                )
            case _:
                raise UnknownConstructError("Not complex construct")

    def _match_on_text(
        self,
        construct: FlangConstruct,
        reader: BaseFlangInputReader,
    ) -> FlangTextMatchObject:
        text_to_match = reader.read()
        construct_text = construct.get_attrib("value", construct.text)

        match construct.name:
            case "regex":
                assert isinstance(text_to_match, str) and isinstance(construct_text, str)

                construct_pattern = construct_text.format(**BUILTIN_PATTERNS)
                matched_text = re.match(construct_pattern, text_to_match)

                if not matched_text:
                    raise TextMatchNotFound(
                        f'Could not match regex pattern: "{construct_pattern}" with text: "{reader.read()[:15]}"'
                    )

                if not matched_text.group():
                    raise RuntimeError(
                        "We have matched an empty object which does not make any sense. Please fix the template to not match such text. Like what would you expect after matching nothing?"
                    )

                return FlangTextMatchObject(
                    identifier=self.generate_symbol_for_match_object(construct),
                    content=matched_text.group(),
                )
            case "text":
                assert isinstance(text_to_match, str) and isinstance(construct_text, str)

                if not text_to_match.startswith(construct_text):
                    raise TextMatchNotFound(
                        f'Could not match text pattern: "{construct_text}" with '
                        f'text: "{reader.read()[:len(construct_text)]}"'
                    )

                return FlangTextMatchObject(
                    identifier=self.generate_symbol_for_match_object(construct),
                    content=construct_text,
                )
            case _:
                raise UnknownConstructError("Not text construct")

    def _match_on_file(
        self,
        construct: FlangConstruct,
        reader: BaseFlangInputReader,
    ) -> FlangFileMatch:
        if construct.name != "file":
            raise UnknownConstructError("Not file construct")

        assert isinstance(reader, FlangFileInputReader)

        current_files = reader.read()

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

        child = next(self.iterate_children(construct.location))
        sub_reader = matched_file.get_input_reader()

        content, _ = self._match_flang_construct(
            child, sub_reader, check_if_all_text_parsed=True
        )

        if isinstance(sub_reader, FlangFileInputReader):
            return FlangDirectoryMatchObject(
                identifier=self.generate_symbol_for_match_object(construct),
                content=content,  # type: ignore TODO: napraw to
                filename=matched_file.filename,
            )

        return FlangFlatFileMatchObject(
            identifier=self.generate_symbol_for_match_object(construct),
            content=content,  # type: ignore TODO: napraw to
            filename=matched_file.filename,
        )

    def _match_against_all_construct_variants(
        self,
        construct: FlangConstruct,
        reader: BaseFlangInputReader,
    ) -> FlangMatchObject:
        matchers = (
            self._match_on_complex_construct,
            self._match_on_text,
            self._match_on_file,
        )
        match_object = None

        for matcher in matchers:
            try:
                match_object = matcher(construct, reader)
            except UnknownConstructError:
                continue
            else:
                break

        if match_object is None:
            raise UnknownConstructError

        return match_object

    def _match_flang_construct(
        self,
        construct: FlangConstruct,
        reader: BaseFlangInputReader,
        check_if_all_text_parsed: bool,
    ) -> tuple[list[FlangMatchObject], BaseFlangInputReader]:
        reader = reader.copy()
        matches = []

        try:
            match_object = self._match_against_all_construct_variants(construct, reader)
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
                match_object = self._match_against_all_construct_variants(
                    construct, reader
                )
                matches.append(match_object)
                reader.consume_data(match_object)
            except MatchNotFoundError as e:
                reader = reader.previous
                break

        if check_if_all_text_parsed and reader.read():
            raise TextNotParsedError(f"Text left: {reader.read()}")

        return matches, reader

    def match(
        self, reader: BaseFlangInputReader
    ) -> tuple[list[FlangMatchObject], BaseFlangInputReader]:
        return self._match_flang_construct(
            self.root_construct, reader, check_if_all_text_parsed=True
        )

    def get_construct_from_spec(self, match_object: FlangMatchObject) -> FlangConstruct:
        return self.find_symbol(match_object.construct_name)
