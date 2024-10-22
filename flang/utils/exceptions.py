# ast tree errors
class ExactSameNodeInsertionError(Exception):
    pass


class DuplicateNodeInsertionError(Exception):
    pass


# ast manipulation
class TextNotParsedError(Exception): ...


class MatchNotFoundError(Exception): ...


class TextMatchNotFound(MatchNotFoundError): ...


class ComplexMatchNotFound(MatchNotFoundError): ...


class FileMatchNotFound(MatchNotFoundError): ...


class SymbolNotFoundError(Exception): ...


class UnknownFlangNodeError(Exception): ...


class SkipFlangNodeException(Exception): ...


class UnknownParentException(Exception): ...


# xml parser


class UnknownAttributeException(Exception): ...


# events


class EventError(Exception): ...


class UnknownLinkNameError(Exception): ...


class UnknownLinkDeclarationError(Exception): ...


class LinkOutOfScopeError(Exception): ...


# input reader
class NoMoreDataException(Exception): ...
