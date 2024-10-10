from flang.utils.exceptions import UnknownFlangNodeError

visible_construct_attributes = ["hidden", "execute-[0-9]+"]
naming_attributes = ["name", "alias"]
cardinality_attributes = ["optional", "multi"]
linking_syntax = ["link-name", "refers-to-link", "scope-start", "scope-end", "hoisting"]


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

    raise UnknownFlangNodeError
