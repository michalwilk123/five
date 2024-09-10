from functools import partial

from flang.structures import FlangMatchObject, FlangProjectConstruct


def _run_events(project_construct: FlangProjectConstruct, match_object: FlangMatchObject):
    construct = match_object.get_construct(project_construct)


def _create_link_graph(
    project_construct: FlangProjectConstruct, match_object: FlangMatchObject
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
    construct = match_object.get_construct(project_construct)

    if construct.get_attrib("lalalal"):
        ...


def evaluate_match_object(
    project_construct: FlangProjectConstruct, flang_match: FlangMatchObject
):
    FlangMatchObject.evaluate_match_tree(
        flang_match, partial(_create_link_graph, project_construct)
    )
    FlangMatchObject.evaluate_match_tree(
        flang_match, partial(_run_events, project_construct)
    )
