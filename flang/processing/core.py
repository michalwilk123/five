from flang.structures import (
    BaseFlangInputReader,
    FlangAbstractMatchObject,
    FlangFileInputReader,
    FlangProjectConstruct,
    FlangTextInputReader,
    IntermediateFileObject,
)

from .evaluation import evaluate_match_object
from .generators import generate_flang_construct
from .matchers import match_flang_construct


class FlangProjectProcessor:
    def __init__(self, project_construct: FlangProjectConstruct) -> None:
        self.project_construct: FlangProjectConstruct = project_construct

    def backward(self, spec: FlangAbstractMatchObject) -> BaseFlangInputReader:
        return generate_flang_construct(spec)

    def forward(self, sample: BaseFlangInputReader) -> list[FlangAbstractMatchObject]:
        match_object, _ = match_flang_construct(
            self.project_construct,
            self.project_construct.root_construct,
            sample,
            check=True,
        )
        is_empty_match = match_object == []
        is_a_file_match = isinstance(match_object[0], FlangAbstractMatchObject)

        if is_empty_match or is_a_file_match:
            return match_object

        return [
            FlangAbstractMatchObject(
                identifier="_root", content=match_object, filename=None
            )
        ]

    def forward_string(self, sample: str) -> list[FlangAbstractMatchObject]:
        reader = FlangTextInputReader(sample)
        return self.forward(reader)

    def forward_filename(self, path: str) -> list[FlangAbstractMatchObject]:
        file_object = IntermediateFileObject(path)
        reader = FlangFileInputReader([file_object], filename=file_object)
        return self.forward(reader)
