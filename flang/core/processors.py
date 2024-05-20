from utils.abstracts import (
    FlangProcessor,
)
from utils.dataclasses import (
    FlangObject,
    FlangMatchObject,
)
import utils.constructs as c
from utils.helpers import compose
from .text_matcher import FlangTextMatcherBase


def ensure_types(cls: type):
    class processor_class(cls):
        def __init__(self, *args, **kwargs):
            self._ensure_types = kwargs.pop("ensure_types", False)

            super().__init__(*args, **kwargs)

        def forward(self, *args: any, **kwargs: any) -> any:
            if self._ensure_types:
                first_arg = args[0] if args else next(iter(kwargs))

                assert isinstance(
                    first_arg, self.forward_type
                ), f"Processor {cls.__name__} expects type: {self.forward_type} as a forward type and {self.backward_type} as a backward type. Instead it got object: {type(first_arg)}: {first_arg} as a forward type"
                result = super(self).forward(*args, **kwargs)
                assert isinstance(
                    result, self.backward_type
                ), f"Processor {cls.__name__} expects type: {self.forward_type} as a forward type and {self.backward_type} as a backward type. Instead it got object: {type(result)}: {result} as a backward type"

                return result

            return super().forward(*args, **kwargs)

        def backward(self, *args: any, **kwargs: any) -> any:
            if self._ensure_types:
                first_arg = args[0] if args else next(iter(kwargs))

                assert isinstance(
                    first_arg, self.backward_type
                ), f"Reversed processor {cls.__name__} expects type: {self.forward_type} as a forward type and {self.backward_type} as a backward type. Instead it got object: {type(first_arg)}: {first_arg} as a forward type"
                result = super(self).backward(*args, **kwargs)
                assert isinstance(
                    result, self.forward_type
                ), f"Reversed processor {cls.__name__} expects type: {self.forward_type} as a forward type and {self.backward_type} as a backward type. Instead it got object: {type(result)}: {result} as a backward type"

                return result

            return super().backward(*args, **kwargs)

    return processor_class


@ensure_types
class FlangTextProcessor(FlangTextMatcherBase, FlangProcessor):
    """
    How matcher works
    f(x) = matcher(schema).forward
    f'(x) = matcher(schema).backward

    f(a) -> b
    f'(b) -> a'
    a is equivalent to a'

    Forward pass through processor generates source code from provided schema based on the flang object
    Backward pass through processor generates schema with parameters based on source code
    """

    def __init__(self, flang_object: FlangObject, stop_on_error: bool = False) -> any:
        self.root = flang_object.root_component
        self.object = flang_object
        self.stop_on_error = stop_on_error

    def return_without_match(self, reason=""):
        if self.stop_on_error:
            raise RuntimeError(f"Could not match component. Reason: {reason}")

    def match(self, construct: c.BaseFlangConstruct, *args, **kwargs):
        if not self.can_construct_match(construct):
            return None

        result = self._match(construct, *args, **kwargs)
        return self.return_without_match() if result is None else result

    def generate(self, spec: FlangMatchObject) -> str:
        ...

    def backward(self, sample: str) -> FlangMatchObject | None:
        return self.match(self.root, sample)

    def forward(self, *args: any, **kwargs: any) -> any:
        return self.generate(
            self,
        )

    @staticmethod
    def can_construct_match(construct: c.BaseFlangConstruct):
        if isinstance(construct, c.FlangComponent):
            return construct.can_match()
        if isinstance(construct, (c.FlangRawText, c.FlangPredicate)):
            return True
        return False

    @property
    def forward_type(self):
        return FlangMatchObject

    @property
    def backward_type(self):
        return str


class FlangInfererProcessor(FlangProcessor):
    ...


class FlangSerializerProcessor(FlangProcessor):
    ...


@ensure_types
class FlangStandardProcessorToolchain(FlangProcessor):
    def __init__(self, flang_object: FlangObject, ensure_types=True):
        self.flang_object = flang_object

        self.pipeline: list[FlangProcessor] = [
            # FlangSerializerProcessor(flang_object),
            # FlangInfererProcessor(flang_object),
            FlangTextProcessor(flang_object),
        ]

    def forward(self, processor_input: any) -> dict:
        return compose(
            processor_input,
            (processor_class.forward for processor_class in self.pipeline),
        )

    def backward(self, processor_input: any) -> str:
        return compose(
            processor_input,
            (processor_class.backward for processor_class in reversed(self.pipeline)),
        )

    @property
    def forward_type(self) -> type:
        return dict

    @property
    def backward_type(self) -> type:
        return str
