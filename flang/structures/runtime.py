import re

from flang.exceptions import SymbolNotFoundError
import collections
from .events import FlangLink
from .spec import FlangConstruct, FlangMatchObject, PossibleRootFlangMatch, FlangTextMatchObject
from enum import Enum,auto


class LinkVariant(Enum):
    DEFINITION = auto()
    REFERENCE = auto()


class FlangProjectRuntime:
    # TODO: maybe should be in separate file?
    # path: str
    # root: str = ""
    # # linking_graph: FlangLinkGraph = dataclasses.field(default_factory=FlangLinkGraph) # TODO: not needed?
    # # event_queue: FlangEventQueue = dataclasses.field(default_factory=FlangEventQueue)
    # symbol_table: dict[str, FlangConstruct] = dataclasses.field(default_factory=dict)
    # symbol_occurence_counter: dict[str, int] = dataclasses.field(default_factory=dict)
    def __init__(self, path: str) -> None:
        self.path = path
        self.root = ""
        self.symbol_table: dict[str, FlangConstruct] = {}
        self.symbol_occurence_counter: dict[str, int] = {}
        self.links: list[FlangLink] = []

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

    def get_construct_from_spec(self, match_object: FlangMatchObject) -> FlangConstruct:
        return self.find_symbol(match_object.construct_name)

    def _match_source_links_with_targets(self, match_object:PossibleRootFlangMatch, symbols):

        for variant, symbol in symbols:
            ...

        # FlangMatchObject.get_construct_name_from_spec_name(source_symbol)

    def initialize_linking(self, root: PossibleRootFlangMatch) -> None:
        # TODO can be easily cached
        symbols = []
        das = collections.defaultdict(list)

        def _create_symbols(match_object: FlangMatchObject):
            construct = self.get_construct_from_spec(match_object)

            # if declaration := construct.get_attrib("link-definition"):
            #     assert isinstance(match_object, FlangTextMatchObject)

            #     key = f"{match_object.content}:{declaration}"
            #     das[key].append()

            #     symbols.append(
            #         (LinkVariant.DEFINITION, match_object.identifier)
            #     )
            
            # if construct.get_attrib("link-from"):
            #     symbols.append(
            #         (LinkVariant.REFERENCE, match_object.identifier)
            #     )

        def _cleanup_symbols(match_object: FlangMatchObject):
            construct = self.get_construct_from_spec(match_object)

            # if declaration := construct.get_attrib("link-definition"):
            #     assert isinstance(match_object, FlangTextMatchObject)

            #     key = f"{match_object.content}:{declaration}"
            #     das[key].append()

            #     symbols.append(
            #         (LinkVariant.DEFINITION, match_object.identifier)
            #     )

        # if we'd want hoisting we should implement breadth first search. For now we use only DFS
        root.apply_function(enter_function=_create_symbols, exit_function=_cleanup_symbols)

        # for symbol in symbols:
        self._match_source_links_with_targets(root, symbols)
    

def inilinkin(project_runtime: FlangProjectRuntime, root: PossibleRootFlangMatch):
    ...
