from flang.utils.exceptions import UnknownConstructError

visible_construct_attributes = ["visible", "execute-[0-9]+"]
naming_attributes = ["name", "alias"]
cardinality_attributes = ["optional", "multi"]
linking_syntax = ["link-definition", "link-from", "scope-start", "scope-end"]


def get_possible_construct_attributes(construct_name: str):

    match construct_name:
        case "sequence" | "choice":
            return (
                naming_attributes + cardinality_attributes + visible_construct_attributes
            )
        case "text" | "regex":
            return (
                naming_attributes
                + cardinality_attributes
                + visible_construct_attributes
                + linking_syntax
                + ["value"]
            )
        case "event":
            return naming_attributes
        case "file":
            return (
                naming_attributes
                + cardinality_attributes
                + visible_construct_attributes
                + ["pattern", "variant"]
            )
        case "use":
            return (
                naming_attributes
                + cardinality_attributes
                + visible_construct_attributes
                + linking_syntax
                + ["value", "ref"]
            )

    raise UnknownConstructError


def validate_construct_attributes(): ...
