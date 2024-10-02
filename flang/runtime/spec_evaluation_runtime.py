from collections.abc import Callable

from flang.structures import (
    FlangAbstractMatchObject,
    FlangConstruct,
    FlangMatchObject,
    FlangTextMatchObject,
    RootFlangMatchObject,
    ScopeTree,
)
from flang.utils.exceptions import (
    LinkOutOfScopeError,
    UnknownLinkDeclarationError,
    UnknownLinkNameError,
    EventError,
)

from .project_parsing_runtime import ProjectParsingRuntime

Subroutine = Callable[[], None]


class EventQueue:
    def __init__(self):
        self.bank = {}

    def add_event(self, anchor: str, event: Subroutine, priority: int = 1):
        if priority not in self.bank:
            self.bank[priority] = []

        self.bank[priority].append((anchor, event))


    def execute_all(self):
        for priority in sorted(self.bank, reverse=True):
            for anchor, event in self.bank[priority]:
                try:
                    event()
                except Exception as e:
                    raise EventError(f"Event from {anchor} named {event} caused an exception") from e

    def _forward(self): ...

    def clean_up(self): ...

    def __len__(self):
        return 0


class LinkStorage:
    def __init__(self, scope_tree: ScopeTree) -> None:
        self.scope_tree = scope_tree
        self.symbol_stack_dictionary: dict = {}
        self.connected_symbols: dict[str, str] = {}

    def declare(self, location, link_name, declared_symbol, scope_start, scope_end=None):
        if declared_symbol not in self.symbol_stack_dictionary:
            self.symbol_stack_dictionary[declared_symbol] = []

        self.symbol_stack_dictionary[declared_symbol].append(
            (location, link_name, scope_start, scope_end)
        )

    def reference_fits_target(self, location, link_name):
        return location == link_name

    def reference_fits_scope(self, location, scope_start, scope_end):
        parent = self.scope_tree.get_(scope_start)
        assert parent is not None, f"Unknown scope start: {scope_start}"

        return parent.contains(location, scope_end)

    def connect(self, location, link_name, declared_symbol):
        possible_link_targets = self.symbol_stack_dictionary.get(declared_symbol, [])[
            ::-1
        ]
        if not possible_link_targets:
            raise UnknownLinkNameError

        possible_link_targets = [
            (_tl, _ln)
            for _tl, _ln, scope_start, scope_end in possible_link_targets
            if self.reference_fits_scope(location, scope_start, scope_end)
        ]
        if not possible_link_targets:
            raise LinkOutOfScopeError

        possible_link_targets = [
            target_location
            for target_location, target_link_name in possible_link_targets
            if self.reference_fits_target(link_name, target_link_name)
        ]
        if not possible_link_targets:
            raise UnknownLinkDeclarationError

        connected_link_location = possible_link_targets[0]
        self.connected_symbols[location] = connected_link_location
        return connected_link_location


class SpecEvaluationRuntime:
    def __init__(
        self, project_runtime: ProjectParsingRuntime, spec: RootFlangMatchObject
    ):
        self.project_runtime = project_runtime
        self.event_queue = EventQueue()
        self.scope_tree = ScopeTree(spec.identifier, parent=None)
        self.link_storage = LinkStorage(self.scope_tree)
        self.spec = spec

        self._collect_events()

    def _find_scope(self, scope_from): 
        ###### TODO: <----- TUTAJ SKONCZYLES
        pass

    def _add_link_declaration(
        self, location, link_name, declaration, scope_start, scope_end=None
    ) -> bool:
        def _link_declaration_fn():
            self.link_storage.declare(location, link_name, declaration, scope_start, scope_end)

        self.event_queue.add_event(location, event=_link_declaration_fn, priority=5)

    def _add_link_reference(
        self, location, link_name, declaration, hoisting
    ) -> bool:

        def _link_reference_fn():
            import warnings
            warnings.warn("Implement scope-finding!")
            # self.link_storage.connect(location, link_name, declaration)
            pass # TODO: for this to work, we need self._find_scope to be finished

        self.event_queue.add_event(location, event=_link_reference_fn, priority=6 if hoisting else 5)

    def _add_link_event(self, spec: FlangMatchObject, link_storage) -> bool:
        construct = self.project_runtime.get_construct_from_spec(spec)

        if construct.get_attrib("link-name"):  # change to property
            assert isinstance(spec, FlangTextMatchObject)

            link_name = construct.attributes["link-name"]

            if scope_start := construct.get_bool_attrib("scope-start"):
                scope_start = self._find_scope(scope_start)

            if scope_end := construct.get_attrib("scope-end"):
                scope_end = self._find_scope(scope_end)

            self._add_link_declaration(
                spec.identifier,
                link_name,
                spec.content,
                scope_start,
                scope_end=scope_end,
            )

        if construct.get_attrib("refers-to-link"):
            link_name = construct.get_attrib("refers-to-link")
            hoisting = construct.get_attrib("hoisting")

            self._add_link_reference(spec.identifier, link_name, spec.content, hoisting)

    def _add_user_event(self, spec: FlangMatchObject) -> bool:
        return False

    def _add_match_to_scope_tree(self, spec: FlangMatchObject, scope_tree: ScopeTree):
        if isinstance(spec.content, list):
            for item in spec.content:
                assert isinstance(item, FlangMatchObject)
                scope_tree.add_node(spec.identifier, item.identifier)

    def populate_queue(self, spec: FlangMatchObject, link_storage: LinkStorage) -> bool:
        link_event = self._add_link_event(spec, link_storage)
        user_event = self._add_user_event(spec)

        return link_event or user_event

    def _collect_events_recursively(
        self, spec: FlangMatchObject, link_storage: LinkStorage
    ):
        self._add_match_to_scope_tree(spec, link_storage.scope_tree)

        if not isinstance(spec, FlangAbstractMatchObject):
            self.populate_queue(spec, link_storage)

        if isinstance(spec.content, list):
            for item in spec.content:
                assert isinstance(item, FlangMatchObject)

                self._collect_events_recursively(item, link_storage)

    def _collect_events(self) -> None:
        assert (
            len(self.event_queue) == 0
        ), "Should initialize collection of events on empty event queue"

        self._collect_events_recursively(self.spec, self.link_storage)

    def _execute_events_recursively(self): ...

    def execute_events(self) -> None:
        self.event_queue.execute_all()
