from functools import partial

from flang.structures import (
    FlangMatchObject,
    FlangProjectRuntime,
    PossibleRootFlangMatch,
)


def _run_events(project_construct: FlangProjectRuntime, match_object: FlangMatchObject):
    # construct = match_object.get_construct(project_construct)
    ...


def create_link_graph(project_construct: FlangProjectRuntime, match_object):
    """
    links:

    Import statements:
    object definition -> import -> using module
    link=a -> referring=a link-name=b -> link-from=b

    Function/Variable definition:
    object A definition a -> using object A (a) -> object A definition b -> using object A (b)
    link=a override=True (a) -> reffering=a (a) -> link=a override=True (b) -> reffering=a (b)

    Scopes (variable out of scope in function body)

    features="hoisting"
    Complex reference link != referring (for example import statements)
    """
    # root = match_object.get_construct(project_construct)
    # graph = FlangLinkGraph.from_match_object(project_construct: FlangProjectConstruct, match_object: FlangAbstractMatchObject)


def evaluate_match_object(
    project_construct: FlangProjectRuntime, flang_match: PossibleRootFlangMatch
):
    # perform linking
    # link_graph = create_link_graph(project_construct, flang_match)
    # graph = FlangLinkGraph.from_match_object(project_construct, flang_match)
    # _run_events(project_construct, flang_match)
    project_construct.initialize_link_graph(flang_match)  # TODO: continue this
