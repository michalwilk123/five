import enum

from flang.core.evaluation import create_event_store
from flang.core.subparsers import parse_user_language
from flang.structures import (
    BaseFlangInputReader,
    FlangAST,
    FlangFileInputReader,
    FlangTextInputReader,
    IntermediateFileObject,
    UserASTRootNode,
)


class BuiltinEvent(enum.Enum):
    ON_READ = "read"
    ON_DELETE = "delete"
    ON_MODIFY = "modify"


class InteractiveFlangObject:
    def __init__(self, flang_ast: FlangAST, user_ast: UserASTRootNode) -> None:
        self.flang_ast = flang_ast
        self.user_ast = user_ast

        # evaluate here
        self.event_storage = create_event_store(user_ast, flang_ast)
        self.context = {}
        context = self.event_storage.execute_all(BuiltinEvent.ON_READ.value)
        self.context.update(context)

    @staticmethod
    def evaluate_user_language(
        flang_ast: FlangAST, reader: BaseFlangInputReader
    ) -> UserASTRootNode:
        user_ast = parse_user_language(flang_ast, reader)

        return user_ast

    @classmethod
    def from_string(cls, flang_ast: FlangAST, sample: str):
        reader = FlangTextInputReader(sample)
        user_ast = cls.evaluate_user_language(flang_ast, reader)
        return cls(flang_ast, user_ast)

    @classmethod
    def from_filename(cls, flang_ast: FlangAST, path: str) -> None:
        file_object = IntermediateFileObject(path)
        reader = FlangFileInputReader([file_object], filename=file_object.filename)
        user_ast = cls.evaluate_user_language(flang_ast, reader)

        return cls(flang_ast, user_ast)
