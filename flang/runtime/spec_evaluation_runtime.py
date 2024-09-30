from collections.abc import Callable

from flang.structures import (
    FlangConstruct,
    FlangMatchObject,
    FlangTextMatchObject,
    PossibleRootFlangMatch,
    ScopeTree,
)

from .project_parsing_runtime import ProjectParsingRuntime
from flang.utils. exceptions import ReferenceKeyError

Subroutine = Callable[[], None]


class EventQueue:
    def __init__(self):
        self.bank = {}

    def add_event(self, anchor: str, event: Subroutine, priority: int = 1): ...

    def execute_all(self): ...

    def _forward(self): ...

    def clean_up(self): ...

    def __len__(self):
        return 0


# ScopeGraph = dict[str, dict[str, "ScopeGraph"]]
# this is soo much underoptimized
# class ScopeGraph(dict):
#     def find_parent_dict(self, parent:str) -> "ScopeGraph":
#         for key, value in self.values():
#             if key == parent:
#                 return value
#     def add_node(self, current:str, parent:str | None=None):
#         parent_dict = self if parent is None else self.find_parent_dict(parent)
#         parent_dict[current] = None


class LinkStorage:
    def __init__(self) -> None:
        self.symbol_stack_dictionary:dict[str, list[tuple[str, str, str]]] = {}

    def declare(self, link_name, declared_symbol, scope_start, scope_end):
        if declared_symbol not in self.symbol_stack_dictionary:
            self.symbol_stack_dictionary = []
        
        self.symbol_stack_dictionary.append( (link_name, scope_start, scope_end) )

    def reference_fits_target(self):
        ...

    def refer(self, link_name, declared_symbol):
        if not (targets := self.symbol_stack_dictionary.get(declared_symbol))[::-1]:
            raise ReferenceKeyError
        
        target = next(filter(lambda args: self.reference_fits_target(*args), targets))
        




class SpecEvaluationRuntime:
    def __init__(self, project_runtime: ProjectParsingRuntime):
        self.project_runtime = project_runtime
        self.event_queue = EventQueue()
        self.link_storage = LinkStorage()

    def _build_link_declaration_event(
        self, link_name: str, declared_symbol: str, scope_start: str, scope_end: str
    ) -> Subroutine:
        def _link_declaration_fn():
            self.link_storage.declare(link_name, declared_symbol)

        return _link_declaration_fn

    def _build_link_reference_event(
        self, link_name: str, declared_symbol: str
    ) -> Subroutine:
        def _link_reference_fn():
            self.link_storage.refer(link_name, declared_symbol)

        return _link_reference_fn

    def _find_scope(self, scope_from, scope_to): ...

    def _add_link_declaration(
        self, spec: FlangMatchObject, construct: FlangConstruct
    ) -> bool:
        assert isinstance(spec, FlangTextMatchObject)

        declaration = construct.attributes["link-definition"]

        if scope_start := construct.get_bool_attrib("scope-start"):
            scope_start = self._find_scope(scope_start)

        if scope_end := construct.get_attrib("scope-end"):
            scope = self._find_scope(scope_end)

        value = spec.content

        subroutine = self._build_link_declaration_event(declaration, value)
        self.event_queue.add_event(scope, priority=1)

    def _add_link_reference(
        self, spec: FlangMatchObject, construct: FlangConstruct
    ) -> bool:
        assert isinstance(spec, FlangTextMatchObject)

        referred = construct.get_attrib("link-from")
        value = spec.content
        hoisting = construct.get_bool_attrib("hoisting")

        subroutine = self._build_link_reference_event(
            referred, value, scope_start, scope_end
        )
        self.event_queue.add_event(referred, priority=2 if hoisting else 1)

    def _add_link_event(self, spec: FlangMatchObject) -> bool:
        construct = self.project_runtime.get_construct_from_spec(spec)

        if construct.get_attrib("link-definition"):
            # TODO: <-- unpack variables from construct here
            self._add_link_declaration(spec, construct)

        if construct.get_attrib("link-from"):
            # TODO: <-- unpack variables from construct here
            self._add_link_reference(spec, construct)

    def _add_user_event(self, spec: FlangMatchObject) -> bool: ...

    def _add_match_to_scope_tree(self, spec: FlangMatchObject, scope_tree: ScopeTree):
        if isinstance(spec.content, list):
            for item in spec.content:
                assert isinstance(item, FlangMatchObject)
                scope_tree.add_node(spec.identifier, item.identifier)

    def populate_queue(self, spec: FlangMatchObject) -> bool:
        link_event = self._add_link_event(spec)
        user_event = self._add_user_event(spec)

        return link_event or user_event

    def _collect_events_recursively(self, spec: FlangMatchObject, scope_tree: ScopeTree):
        self._add_match_to_scope_tree(spec, scope_tree)
        self.populate_queue(spec)

        if isinstance(spec.content, list):
            for item in spec.content:
                assert isinstance(item, FlangMatchObject)

                self._collect_events_recursively(item, scope_tree)

    def collect_events(self, spec: PossibleRootFlangMatch) -> None:
        assert (
            len(self.event_queue) == 0
        ), "Should initialize collection of events on empty event queue"
        scope_tree = ScopeTree(spec.identifier, parent=None)

        self._collect_events_recursively(spec, self.event_queue, scope_tree)

    def _execute_events_recursively(self): ...

    def execute_events(self) -> None:
        pass
