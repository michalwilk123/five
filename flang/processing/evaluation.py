from functools import partial

from flang.structures import FlangLinkGraph, FlangProjectConstruct, FlangTextMatchObject
from flang.utils import linking_syntax


def _run_events(
    project_construct: FlangProjectConstruct, match_object: FlangTextMatchObject
):
    construct = match_object.get_construct(project_construct)


def _perform_linking_on_single_match(
    project_construct: FlangProjectConstruct,
    graph: FlangLinkGraph,
    match_object: FlangTextMatchObject,
) -> None:
    # TODO can be easily cached
    construct = project_construct.find_symbol(match_object.identifier)

    if "link-definition" in construct.attributes:
        graph.add_parent()

    if "link-from" in construct.attributes:
        graph.add_relation()


def create_link_graph(
    project_construct: FlangProjectConstruct, match_object: FlangTextMatchObject
):
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
    graph = FlangLinkGraph()
    match_object.evaluate_match_tree(
        partial(_perform_linking_on_single_match, project_construct, graph)
    )


def evaluate_match_object(
    project_construct: FlangProjectConstruct, flang_match: FlangTextMatchObject
):
    # perform linking
    link_graph = create_link_graph(project_construct, flang_match)

    _run_events(project_construct, flang_match)
