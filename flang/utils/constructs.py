# from .dataclasses import BaseFlangConstruct
from __future__ import annotations
import re
from .helpers import BUILTIN_PATTERNS, create_unique_symbol
import dataclasses
import abc


@dataclasses.dataclass(slots=True)
class BaseFlangConstruct(abc.ABC):
    children_or_value: list[BaseFlangConstruct] | str
    attributes: dict[str, str] | None
    location: str
    external_dependencies: list[str] = dataclasses.field(default_factory=list)
    path: None | str = dataclasses.field(init=False, default=None)

    # def get_full_location(self) -> str:
    #     symbol = self.symbol or create_unique_symbol(type(self).__name__)

    #     if not self.parent:
    #         return symbol

    #     return f"{self.parent}.{symbol}"

    @property
    def symbol(self) -> str:
        if "." in self.location:
            return self.location.split(".")[-1]
        else:
            return self.location

    @property
    def children(self) -> list[BaseFlangConstruct]:
        assert isinstance(self.children_or_value, list)
        return self.children_or_value

    @property
    def value(self) -> str:
        assert isinstance(self.children_or_value, str)
        return self.children_or_value


class FlangBaseRawConstruct(BaseFlangConstruct):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if isinstance(self.children_or_value, list):
            assert len(self.children_or_value) == 1
            assert isinstance(self.children_or_value[0], FlangRawText)
            self.children_or_value = self.children_or_value[0].value


class FlangComponent(BaseFlangConstruct):
    """
    type = regular, choice, optional
    """

    name = "component"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.component_type = self.attributes.get("type", "regular")
        self.visibile = self.attributes.get("visibility", True)
        self.optional = self.attributes.get("optional", False)

    def can_match(self) -> bool:
        return self.visibile != "definition"

    def match(self, text):
        sample = {}
        start = 0

        for matcher in self.matchers:
            match = matcher.match(text, start)

            if not match:
                assert False, "Could not match the text!"

            sample_chunk, pos = match

            assert all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in sample_chunk.items()
            )

            if not self.is_root:
                sample_chunk = {
                    f"{self.name}.{key}": value for key, value in sample_chunk.items()
                }

            sample.update(sample_chunk)

            start = pos

        return sample, start

    def generate(self, config: dict[str, str]) -> str:
        generated_component = ""

        new_config = {**config}

        for key, value in config.items():
            if key.startswith(self.name):  # todo: should be a better way to do this...
                del new_config[key]
                new_config[key.removeprefix(self.name)] = value

        config = new_config  # cannot iterate through changing dictionary..

        for matcher in self.matchers:
            chunk, config = matcher.generate(config)
            generated_component += chunk

        return generated_component, config


class FlangPredicate(BaseFlangConstruct):
    name = "predicate"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._raw_pattern = self.attributes["pattern"]
        self.pattern = re.compile(self._raw_pattern.format(**BUILTIN_PATTERNS))

    def generate(self, config):
        value = config.pop(self.name)
        return value, config


class FlangRawRegex(FlangBaseRawConstruct):
    name = "regex"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.pattern = re.compile(self.value.format(**BUILTIN_PATTERNS))


class FlangRawText(FlangBaseRawConstruct):
    name = "text"

    def generate(self, config):  # deprecated
        return self.value, config


class FlangRule(BaseFlangConstruct):
    name = "rule"


class FlangChoice(BaseFlangConstruct):
    name = "choice"


class FlangReference(BaseFlangConstruct):
    name = "ref"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        refrenced_construct = self.attributes["ref"]

        if ":" in refrenced_construct:
            self.external_dependencies.append(refrenced_construct)
