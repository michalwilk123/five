from flang.runtime.subparsers import parse_user_language
from flang.structures import (
    BaseFlangInputReader,
    FlangAST,
    FlangFileInputReader,
    FlangTextInputReader,
    IntermediateFileObject,
    UserASTRootNode,
)


class InteractiveFlangObject:
    def __init__(self, flang_ast: FlangAST, user_ast: UserASTRootNode) -> None:
        self.flang_ast = flang_ast
        self.user_ast = user_ast

    @staticmethod
    def evaluate_user_language(
        flang_ast: FlangAST, reader: BaseFlangInputReader
    ) -> UserASTRootNode:
        match_objects = parse_user_language(flang_ast, reader)

        # evaluate here
        return match_objects

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
