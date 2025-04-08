import dataclasses
import random
import re
import string

"""
NOTE: maybe someday we will ditch the regex patterns? It is kinda problematic for my use case

1. It is to some excent not readable to at first glance its hard to tell what it does
2. It is not easy to distinguish what is a part of syntax and what is a raw text to match
"""


class UnknownLexPatternError(Exception):
    pass


@dataclasses.dataclass
class LexicalAnalysisPattern:
    name: str
    pattern: str
    examples: list[str] = dataclasses.field(default_factory=list)
    flags: list[re.RegexFlag] = dataclasses.field(default_factory=list)

    def get_example(self):
        return random.choice(self.examples)

    def get_pattern(self):
        return self.pattern


class LexicalAnalysisPatternStorage:
    def __init__(self, patterns: list[LexicalAnalysisPattern]) -> None:
        self.pattern_dict = {pattern.name.lower(): pattern for pattern in patterns}
        self.validate()

    def validate(self):
        for pattern_obj in self.pattern_dict.values():
            for example in pattern_obj.examples:
                assert re.fullmatch(
                    pattern_obj.pattern, example
                ), f"Example: {example} does not match on pattern: {pattern_obj}"

    def _transform_alias_to_single_pattern(self, pattern: str) -> str:
        try:
            return "|".join(
                self.pattern_dict[elem].get_pattern()
                for elem in pattern.lower().split("|")
            )
        except KeyError:
            raise UnknownLexPatternError(
                f"At least one of the patterns is unknown: {pattern=}"
            )

    @property
    def global_pattern(self):
        possible_pattern_names = "|".join(
            item.name for item in self.pattern_dict.values()
        )
        return re.compile(rf"{possible_pattern_names}(\|{possible_pattern_names})*", re.I)

    def _generate_from_single_pattern(self, pattern: str) -> str:
        try:
            single_pattern = random.choice(pattern.lower().split("|"))
            return self.pattern_dict[single_pattern].get_example()
        except KeyError:
            raise UnknownLexPatternError(
                f"At least one of the patterns is unknown: {pattern=}"
            )

    def _process_pattern(self, pattern: str, transform_func) -> str:
        format_string_args = {
            fname: transform_func(fname)
            for _, fname, _, _ in string.Formatter().parse(pattern)
            if fname
            and (
                transform_func == self._generate_from_single_pattern
                or re.match(self.global_pattern, fname)
            )
        }

        for format_key, value in format_string_args.items():
            pattern = pattern.replace(f"{{{format_key}}}", value)

        return pattern

    def create_pattern(self, pattern: str) -> str:
        return self._process_pattern(pattern, self._transform_alias_to_single_pattern)

    def generate_example(self, pattern: str) -> str:
        return self._process_pattern(pattern, self._generate_from_single_pattern)
