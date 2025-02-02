from contextlib import contextmanager
from typing import Self

from flang.core.evaluation import create_event_store
from flang.core.parsers import parse_user_language
from flang.generators.ast_to_specification import create_specification
from flang.operations.core import OperationState
from flang.parsers.xml import parse_text
from flang.structures import (
    BuiltinEvent,
    FileRepresentation,
    FlangFileInputReader,
    FlangRoot,
    FlangTextInputReader,
    OperationLog,
    TemplateTree,
    create_input_reader_from_file_representation,
)


class FlangObject:
    def __init__(self, template_tree: TemplateTree, flang_tree: FlangRoot) -> None:
        self.template_tree = template_tree
        self.flang_tree = flang_tree
        self.specification = create_specification(template_tree, flang_tree)

        # evaluate here
        self.event_storage = create_event_store(flang_tree, template_tree)
        self.context = {}
        self.operation_log = OperationLog()
        context = self.event_storage.execute_all(BuiltinEvent.ON_READ.value)
        self.context.update(context)

    @contextmanager
    def run_operation(self):
        state = OperationState(
            log=self.operation_log,
            template_tree=self.template_tree,
            specification=self.specification,
        )

        yield state

        # TODO: Test out how events work with operations
        # context = self.event_storage.execute_all(BuiltinEvent.ON_READ.value)
        # self.context.update(context)


class FlangObjectBuilder:
    def xml_template(self, xml_string: str, validate_attributes: bool) -> Self:
        self.template_tree = parse_text(
            xml_string, validate_attributes=validate_attributes
        )
        return self

    def text_sample(self, sample: str) -> Self:
        self.reader = FlangTextInputReader(sample)
        return self

    def filename_sample(self, path: str) -> Self:
        fr = FileRepresentation(path)
        self.reader = create_input_reader_from_file_representation(fr)
        return self

    def filenames_sample(self, paths: list[str]) -> Self:
        files = [FileRepresentation(path) for path in paths]
        self.reader = FlangFileInputReader(files)
        return self

    def build(self) -> FlangObject:
        flang_tree = parse_user_language(self.template_tree, self.reader)
        return FlangObject(self.template_tree, flang_tree)
