import enum

from flang.core.evaluation import create_event_store
from flang.core.generators import generate_user_language
from flang.core.subparsers import parse_user_language
from flang.structures import (
    FileRepresentation,
    FlangAST,
    FlangFileInputReader,
    FlangTextInputReader,
    InputReaderInterface,
    UserASTRootNode,
    create_input_reader_from_file_representation,
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

    def edit(self):
        raise NotImplementedError

    def generate(self, patch):
        generate_user_language()
        raise NotImplementedError

    @staticmethod
    def evaluate_user_language(
        flang_ast: FlangAST, reader: InputReaderInterface
    ) -> UserASTRootNode:
        user_ast = parse_user_language(flang_ast, reader)
        return user_ast

    @classmethod
    def from_reader(cls, flang_ast: FlangAST, reader: InputReaderInterface):
        user_ast = cls.evaluate_user_language(flang_ast, reader)
        return cls(flang_ast, user_ast)

    @classmethod
    def from_string(cls, flang_ast: FlangAST, sample: str):
        reader = FlangTextInputReader(sample)
        return cls.from_reader(flang_ast, reader)

    @classmethod
    def from_filenames(cls, flang_ast: FlangAST, paths: list[str]) -> None:
        files = [FileRepresentation(path) for path in paths]
        reader = FlangFileInputReader(files)
        return cls.from_reader(flang_ast, reader)

    @classmethod
    def from_filename_contents(cls, flang_ast: FlangAST, path: str) -> None:
        fr = FileRepresentation(path)
        reader = create_input_reader_from_file_representation(fr)
        return cls.from_reader(flang_ast, reader)
