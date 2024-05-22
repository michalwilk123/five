from flang.exceptions import MatchNotFoundError, TextNotParsedError
from flang.helpers import create_unique_symbol, emit_function
from flang.structures import FlangConstruct, FlangObject, FlangStructuredText, IntermediateFileObject

class FlangTextProcessor:
    def __init__(
        self, flang_object: FlangObject, root: FlangConstruct=None, allow_partial_match: bool = False
    ) -> any:
        self.root = root or flang_object.root_construct
        self.object = flang_object
        self.allow_partial_match = allow_partial_match

    def match(
        self, construct: FlangConstruct, text: str, start_position=0 # może nie powinno przyjmować tekstu?
    ) -> FlangStructuredText:
        visible_in_spec = bool(construct.name)
        match_object = None

        match construct.construct_name:
            case "component":
                children = []

                new_position = start_position
                for child in self.object.iterate_children(construct.location):
                    try:
                        while True:
                            match_object = self.match(child, text, new_position)
                            new_position += len(match_object)
                            children.append(match_object)

                            if not child.get_bool_attrib("multi"):
                                break
                    except MatchNotFoundError as e:
                        construct_optional = child.get_bool_attrib("optional")
                        cannot_find_more_matches = (
                            child.get_bool_attrib("multi")
                            and children
                            and children[-1].symbol == child.location
                        )

                        if construct_optional or cannot_find_more_matches:
                            continue

                        raise e

                match_object = FlangStructuredText(
                    symbol=construct.location,
                    content=children,
                    visible_in_spec=visible_in_spec,
                )

                if not self.allow_partial_match and self.object.root == construct.location and len(match_object) != len(text):
                    raise TextNotParsedError
                
                return match_object

            case "choice":
                children = []
                for child in self.object.iterate_children(construct.location):
                    try:
                        children.append(self.match(child, text, start_position))
                    except MatchNotFoundError:
                        continue

                if not children:
                    raise MatchNotFoundError

                return max(children, key=len)
            case "regex":
                matched_text = construct.pattern.match(text, start_position)
                if not matched_text:
                    raise MatchNotFoundError

                return FlangStructuredText(
                    symbol=construct.location,
                    content=matched_text.group(),
                    visible_in_spec=visible_in_spec,
                )
            case "text":
                if not text.startswith(construct.text, start_position):
                    raise MatchNotFoundError

                return FlangStructuredText(
                    symbol=construct.location,
                    content=construct.text,
                    visible_in_spec=visible_in_spec,
                )
            case "event":
                name = construct.get_attrib("name", None) or create_unique_symbol(
                    "_flang_function"
                )
                args = construct.get_attrib("args", "").split(",")
                body = construct.text
                emit_function(name, args, body)
            case _:
                raise RuntimeError(f"No such construct {construct.construct_name}")

    def _args_builder(self, args):
        return []

    def generate(self, spec: FlangStructuredText) -> str:
        construct = self.object.find_symbol(spec.symbol)

        match construct.construct_name:
            case "component":
                return "".join(self.generate(child_match) for child_match in spec.content)
            case "choice":
                raise RuntimeError
            case "regex":
                return spec.content
            case "text":
                return spec.content

        raise RuntimeError

    def backward(self, spec: FlangStructuredText) -> str:
        return self.generate(spec)

    def forward(self, sample: str) -> FlangStructuredText:
        return self.match(self.root, sample)

class FlangFileProcessor:
    def __init__(
        self, flang_object: FlangObject, root: FlangConstruct=None, allow_partial_match: bool = False
    ) -> any:
        self.root = root or flang_object.root_construct
        self.object = flang_object
        self.allow_partial_match = allow_partial_match

    def match(
        self, construct: FlangConstruct, text: str, start_position=0
    ) -> FlangStructuredText:
        ...

    def backward(self, spec: FlangStructuredText) -> IntermediateFileObject:
        """
        Powinno sie tutaj sprawdzic czy plik juz istnieje itd. ew go nadpisac
        """
        return self.generate(spec)

    def forward(self, file: str | IntermediateFileObject) -> FlangStructuredText:
        if isinstance(file, str):
            file = IntermediateFileObject.from_path(file)

        return self.match(self.root, file)

class FlangCoreProcessor:
    """
    Implements core constructs
    """
    ...

class FlangProjectProcessor(FlangCoreProcessor, FlangTextProcessor, FlangFileProcessor):
    def match(self, *args, **kwargs):
        klass = self.__class__

        for base in klass.__bases__:
            try:
                match_object = base.match(self, *args, **kwargs)
            except MatchNotFoundError:
                continue
            else:
                break
        
        return match_object
