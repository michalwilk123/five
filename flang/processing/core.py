from flang.structures import FlangInputReader, FlangMatchObject, FlangProjectConstruct

from .generators import generate_flang_construct
from .matchers import match_flang_construct


class FlangProjectProcessor:
    def __init__(self, project_construct: FlangProjectConstruct) -> None:
        self.project_construct = project_construct

    def backward(self, spec: FlangMatchObject) -> FlangInputReader:
        return generate_flang_construct(spec)

    def forward(
        self, sample: FlangInputReader
    ) -> FlangMatchObject | list[FlangMatchObject]:
        match_object = match_flang_construct(
            self.project_construct,
            self.project_construct.root_construct,
            sample,
            always_return_list=False,
            check=True,
        )[0]

        return match_object
