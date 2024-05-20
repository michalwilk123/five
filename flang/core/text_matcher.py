from utils.abstracts import (
    FlangProcessor,
)
from utils.dataclasses import (
    FlangObject,
    FlangMatchObject,
    Postition,
)
import functools
import utils.constructs as c
from typing import Literal


class FlangTextMatcherBase(FlangProcessor):
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

    @functools.singledispatchmethod
    def _match(self, construct, *args, **kwargs) -> FlangMatchObject | None:
        raise NotImplementedError

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangChoice, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        def func(child: c.BaseFlangConstruct):
            match_object = self.match(child, text, start_position)
            return 0 if match_object is None else match_object.position.end

        return max(construct.children, key=func)

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangComponent, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        """
        Component can only match based on its children
        """
        spec = {}
        end_position = start_position

        for child in construct.children:
            match_object = self.match(child, text, end_position)

            if match_object is not None:
                if child.symbol:
                    spec[child.symbol] = match_object

                end_position = match_object.position.end
            elif construct.component_type == "optional":
                return FlangMatchObject.empty_match(start_position)

        return FlangMatchObject(
            position=Postition(start_position, end_position), spec_or_matched=spec
        )

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangRawText, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        if text.startswith(construct.value, start_position):
            return FlangMatchObject(
                position=Postition(start_position, len(construct.value) + start_position),
                spec_or_matched=construct.value,
            )

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangRawRegex, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        if match := construct.pattern.match(text, start_position):
            return FlangMatchObject(
                position=Postition(start_position, match.end()),
                spec_or_matched=construct.value,
            )

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangPredicate, text: str, start_position: int = 0
    ) -> FlangMatchObject | None:
        if match := construct.pattern.match(text, start_position):
            return FlangMatchObject(
                position=Postition(start_position, match.end()),
                spec_or_matched=match.group(),
            )

    @_match.register
    def __dispatched_match(
        self, construct: c.FlangReference, *args, **kwargs
    ) -> FlangMatchObject | None:
        referenced_object = self.object.find_refrenced_object(
            symbol := construct.attributes["ref"]
        )
        assert referenced_object, f"Cannot find object {symbol}"

        return self._match(referenced_object, *args, **kwargs)
