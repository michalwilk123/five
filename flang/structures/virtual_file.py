from __future__ import annotations

import abc
import dataclasses
import enum
import itertools
import os


class AbstractFileInterface(abc.ABC):
    @abc.abstractmethod
    def get_content(self) -> VirtualFileContentType:
        raise NotImplementedError

    @abc.abstractmethod
    def get_is_directory(self) -> bool:
        raise NotImplementedError


VirtualFileContentType = str | list[AbstractFileInterface]


class FileOperation(enum.Enum):
    CREATE = enum.auto()
    DELETE = enum.auto()
    MODIFY = enum.auto()


@dataclasses.dataclass
class FileRepresentation(AbstractFileInterface):
    path: str

    def get_content(self):
        assert os.path.exists(self.path)

        if self.get_is_directory():
            return [
                FileRepresentation(os.path.join(self.path, file))
                for file in sorted(os.listdir(self.path))
            ]
        else:
            with open(self.path) as f:
                return f.read()

    def get_is_directory(self):
        return os.path.isdir(self.path)

    def get_name(self):
        assert (name := os.path.basename(self.path))

        return name


@dataclasses.dataclass
class DiffResult:
    filepath: str
    operation: FileOperation
    text_content: str | None = None

    def apply(self) -> None:
        match self.operation:
            case FileOperation.CREATE:
                if self.text_content is None:
                    os.makedirs(self.filepath)
                else:
                    with open(self.filepath, "x") as f:
                        f.write(self.text_content)
            case FileOperation.DELETE:
                if os.path.isdir(self.filepath):
                    os.rmdir(self.filepath)
                else:
                    os.unlink(self.filepath)
            case FileOperation.MODIFY:
                assert self.text_content is not None

                with open(self.filepath, "r+") as f:
                    f.write(self.text_content)
            case _:
                raise RuntimeError


@dataclasses.dataclass
class VirtualFileRepresentation(AbstractFileInterface):
    name: str
    content: VirtualFileContentType

    class DiffResultContainer(list[DiffResult]):
        Order = (FileOperation.DELETE, FileOperation.CREATE, FileOperation.MODIFY)

        def apply_all(self):
            """
            We should first delete items, starting from most nested.
            Then we add items starting from least nested
            """

            def __key_function(item: DiffResult):
                number_of_separators = item.filepath.count(os.sep)
                return (
                    self.Order.index(item.operation),
                    (
                        -number_of_separators
                        if item.operation == FileOperation.DELETE
                        else number_of_separators
                    ),
                )

            for item in sorted(self, key=__key_function):
                item.apply()

    def get_content(self):
        return self.content

    def get_is_directory(self):
        return isinstance(self.content, list)

    def _diff_directory(self, path: str) -> DiffResultContainer:
        if os.path.exists(path):
            files_in_virtual_directory = set([it.name for it in self.get_content()])
            files_in_real_directory = set(os.listdir(path))
            assert "" not in files_in_virtual_directory

            files_to_delete = files_in_real_directory - files_in_virtual_directory
            ops = [
                DiffResult(
                    filepath=os.path.join(path, name),
                    operation=FileOperation.DELETE,
                )
                for name in files_to_delete
            ]
        else:
            ops = [DiffResult(filepath=path, operation=FileOperation.CREATE)]

        return self.DiffResultContainer(
            list(
                itertools.chain(
                    ops, *(file.diff(root=path) for file in self.get_content())
                )
            )
        )

    def _diff_file(self, path: str) -> DiffResultContainer:
        if not os.path.exists(path):
            return [
                DiffResult(
                    filepath=path,
                    text_content=self.content,
                    operation=FileOperation.CREATE,
                )
            ]

        with open(path, "r+") as f:
            if f.read() != self.get_content():
                return [
                    DiffResult(
                        filepath=path,
                        text_content=self.content,
                        operation=FileOperation.MODIFY,
                    )
                ]

        return []

    def diff(self, root: str = "") -> DiffResultContainer:
        # Compare virtual file representation with actual filesystem.
        path = os.path.join(root, self.name)

        if self.get_is_directory():
            return self._diff_directory(path)

        return self._diff_file(path)

    @classmethod
    def from_real(cls, file: FileRepresentation):
        if file.get_is_directory():
            return cls(
                name=os.path.basename(file.path),
                content=[cls.from_real(item) for item in file.get_content()],
            )

        return cls(name=os.path.basename(file.path), content=file.get_content())
