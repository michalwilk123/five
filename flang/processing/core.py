from flang.structures import (
    BaseFlangInputReader,
    FlangAbstractMatchObject,
    FlangFileInputReader,
    FlangFileMatch,
    FlangMatchObject,
    FlangProjectRuntime,
    FlangTextInputReader,
    IntermediateFileObject,
    PossibleRootFlangMatch,
)

from .evaluation import evaluate_match_object
from .generators import generate_flang_construct
from .matchers import match_flang_construct


class FlangProjectProcessor:
    def __init__(self, project_construct: FlangProjectRuntime) -> None:
        self.project_construct: FlangProjectRuntime = project_construct

    def backward(self, spec: FlangMatchObject) -> BaseFlangInputReader:
        return generate_flang_construct(spec)

    def _forward(self, sample: BaseFlangInputReader) -> PossibleRootFlangMatch | None:
        match_objects, _ = match_flang_construct(
            self.project_construct,
            self.project_construct.root_construct,
            sample,
            check=True,
        )

        if self.project_construct.root_construct.name == "file":
            assert (
                len(match_objects) == 1
            ), "When matching a file tree, we should only return one file (root) as the result"
            assert isinstance(match_objects[0], FlangFileMatch)
            return match_objects[0]

        if match_objects == []:
            # I dont really know what should be return value here. Maybe should not be possible at all
            return None

        assert isinstance(match_objects, list), isinstance(match_objects, list)
        match_object = FlangAbstractMatchObject(content=match_objects)

        return match_object

    def forward(self, sample: BaseFlangInputReader) -> PossibleRootFlangMatch | None:
        match_object = self._forward(sample)

        if match_object is None:
            return None

        evaluate_match_object(self.project_construct, match_object)

        return match_object

    def forward_string(self, sample: str) -> PossibleRootFlangMatch | None:
        reader = FlangTextInputReader(sample)
        return self.forward(reader)

    def forward_filename(self, path: str) -> PossibleRootFlangMatch | None:
        file_object = IntermediateFileObject(path)
        reader = FlangFileInputReader([file_object], filename=file_object.filename)
        return self.forward(reader)
