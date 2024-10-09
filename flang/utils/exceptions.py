# project parsing
class TextNotParsedError(Exception): ...


class MatchNotFoundError(Exception): ...


class TextMatchNotFound(MatchNotFoundError): ...


class ComplexMatchNotFound(MatchNotFoundError): ...


class FileMatchNotFound(MatchNotFoundError): ...


class SymbolNotFoundError(Exception): ...


class UnknownConstructError(Exception): ...


class SkipConstructException(Exception): ...


class UnknownParentException(Exception): ...


# xml parser


class UnknownAttributeException(Exception): ...


# events


class EventError(Exception): ...


class UnknownLinkNameError(Exception): ...


class UnknownLinkDeclarationError(Exception): ...


class LinkOutOfScopeError(Exception): ...
