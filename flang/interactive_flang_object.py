import enum

from flang.core.evaluation import create_event_store
from flang.core.parsers import parse_user_language
from flang.structures import (
    FileRepresentation,
    FlangFileInputReader,
    FlangRoot,
    FlangTextInputReader,
    InputReaderInterface,
    TemplateTree,
    create_input_reader_from_file_representation,
)


class BuiltinEvent(enum.Enum):
    ON_READ = "read"
    ON_DELETE = "delete"
    ON_MODIFY = "modify"


class InteractiveFlangObject:
    def __init__(self, template_tree: TemplateTree, flang_tree: FlangRoot) -> None:
        self.template_tree = template_tree
        self.flang_tree = flang_tree
        self.operation_log = None

        # evaluate here
        self.event_storage = create_event_store(flang_tree, template_tree)
        self.context = {}
        context = self.event_storage.execute_all(BuiltinEvent.ON_READ.value)
        self.context.update(context)

    @staticmethod
    def evaluate_user_language(
        template_tree: TemplateTree, reader: InputReaderInterface
    ) -> FlangRoot:
        flang_tree = parse_user_language(template_tree, reader)
        return flang_tree

    @classmethod
    def from_reader(cls, template_tree: TemplateTree, reader: InputReaderInterface):
        flang_tree = cls.evaluate_user_language(template_tree, reader)
        return cls(template_tree, flang_tree)

    @classmethod
    def from_string(cls, template_tree: TemplateTree, sample: str):
        reader = FlangTextInputReader(sample)
        return cls.from_reader(template_tree, reader)

    @classmethod
    def from_filenames(cls, template_tree: TemplateTree, paths: list[str]) -> None:
        files = [FileRepresentation(path) for path in paths]
        reader = FlangFileInputReader(files)
        return cls.from_reader(template_tree, reader)

    @classmethod
    def from_filename_contents(cls, template_tree: TemplateTree, path: str) -> None:
        fr = FileRepresentation(path)
        reader = create_input_reader_from_file_representation(fr)
        return cls.from_reader(template_tree, reader)

    def run_operation(self): ...

    def get_operation_state(self): ...
