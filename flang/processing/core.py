from flang.structures import (
    BaseFlangInputReader,
    FlangAbstractMatchObject,
    FlangFileInputReader,
    FlangProjectRuntime,
    FlangTextInputReader,
    IntermediateFileObject,
)

from .evaluation import evaluate_match_object
from .generators import generate_flang_construct
from .matchers import match_flang_construct


class FlangProjectProcessor:
    def __init__(self, project_construct: FlangProjectRuntime) -> None:
        self.project_construct: FlangProjectRuntime = project_construct

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

        if self.project_construct.root_construct.name == "file":
            assert (
                len(match_object) == 1
            ), "When matching a file tree, we should only return one file (root) as the result"
            match_object = match_object[0]

        is_a_file_match = isinstance(match_object, FlangAbstractMatchObject)

        if is_empty_match or is_a_file_match:
            return match_object

        match_object = FlangAbstractMatchObject(
            identifier="_root", content=match_object, filename=None
        )
        evaluate_match_object(self.project_construct, match_object)

        return match_object

    def forward_string(self, sample: str) -> list[FlangAbstractMatchObject]:
        reader = FlangTextInputReader(sample)
        return self.forward(reader)

    def forward_filename(self, path: str) -> list[FlangAbstractMatchObject]:
        file_object = IntermediateFileObject(path)
        reader = FlangFileInputReader([file_object], filename=file_object)
        return self.forward(reader)
