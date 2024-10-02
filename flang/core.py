from flang.runtime import ProjectParsingRuntime, SpecEvaluationRuntime
from flang.structures import (  # may import InteractiveFlangObject soon
    BaseFlangInputReader,
    FlangAbstractMatchObject,
    FlangFileInputReader,
    FlangFileMatch,
    FlangMatchObject,
    FlangTextInputReader,
    IntermediateFileObject,
    RootFlangMatchObject,
)


class FlangProjectAnalyzer:
    def __init__(self, project_construct: ProjectParsingRuntime) -> None:
        self.project_construct: ProjectParsingRuntime = project_construct

    def backward(self, spec: FlangMatchObject) -> BaseFlangInputReader:
        raise NotImplementedError

    def _forward(self, reader: BaseFlangInputReader) -> RootFlangMatchObject | None:
        match_objects, _ = self.project_construct.match(reader)

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

    def forward(self, reader: BaseFlangInputReader) -> RootFlangMatchObject | None:
        match_object = self._forward(reader)

        if match_object is None:
            return None

        spec_evaluation_runtime = SpecEvaluationRuntime(
            self.project_construct, match_object
        )
        spec_evaluation_runtime.execute_events()

        return match_object

    def forward_string(self, sample: str) -> RootFlangMatchObject | None:
        reader = FlangTextInputReader(sample)
        return self.forward(reader)

    def forward_filename(self, path: str) -> RootFlangMatchObject | None:
        file_object = IntermediateFileObject(path)
        reader = FlangFileInputReader([file_object], filename=file_object.filename)
        return self.forward(reader)