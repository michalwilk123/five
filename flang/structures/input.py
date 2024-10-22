from __future__ import annotations

import abc
import io

from flang.utils.exceptions import NoMoreDataException

from .ast import UserASTFileMixin, UserASTTextNode
from .virtual_file import FileRepresentation

SANITY_CHECK = True


class InputReaderInterface(abc.ABC):
    @abc.abstractmethod
    def read(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_key(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def consume_data(self, data) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def copy(self) -> InputReaderInterface:
        raise NotImplementedError

    @abc.abstractmethod
    def is_empty(self) -> bool:
        raise NotImplementedError

    @property
    def previous(self) -> FlangTextInputReader:
        assert self._previous is not None
        return self._previous


class FlangTextInputReader(InputReaderInterface):
    def __init__(
        self,
        data: str | io.StringIO,
        cursor: int | None = None,
        previous: FlangTextInputReader | None = None,
    ) -> None:
        self._data = io.StringIO(data) if isinstance(data, str) else data
        self._cursor = cursor or 0
        self._previous = previous

    def is_empty(self) -> bool:
        return self.read() == ""

    def read(self, size=None) -> str:
        self._data.seek(self._cursor)  # look-up correct scope of input stream
        data = self._data.read() if size is None else self._data.read(size)
        self._data.seek(self._cursor)  # return to the initial state
        return data

    def get_key(self):
        return self._cursor

    def consume_data(self, data: UserASTTextNode) -> None:
        if SANITY_CHECK:
            consumed_data = self.read(data.size())
            assert consumed_data == data.get_raw_content(), "{} {}".format(
                consumed_data, data.get_raw_content()
            )
        self._cursor += data.size()

    def copy(self) -> FlangTextInputReader:
        return FlangTextInputReader(self._data, cursor=self._cursor, previous=self)


class FlangFileInputReader(InputReaderInterface):
    def __init__(
        self,
        data: list[FileRepresentation],
        cursor: list | None = None,
        previous: FlangFileInputReader | None = None,
    ) -> None:
        self._data = data
        self._cursor = list(range(len(data))) if cursor is None else cursor.copy()
        self._previous = previous

    def is_empty(self) -> bool:
        return self._cursor == []

    def read(self) -> str:
        if self.is_empty():
            raise NoMoreDataException

        return next(iter(self._data[i].get_name() for i in self._cursor))

    def get_key(self):
        return len(self._data) - len(self._cursor)

    # can be changed in future to include file metadata, so cannot really take string as data
    def consume_data(self, data: UserASTFileMixin) -> None:
        filename = data.filename
        filenames = [f.get_name() for f in self._data]

        self._cursor.remove(filenames.index(filename))

        if SANITY_CHECK:
            assert len(self._cursor) == len(set(self._cursor)), "Should be no duplicates"

    def get_nested_reader(self, filename: str):
        assert self._data != []

        file_representation = next(
            iter(item for item in self._data if item.get_name() == filename)
        )
        return create_input_reader_from_file_representation(file_representation)

    def copy(self) -> FlangFileInputReader:
        return FlangFileInputReader(self._data, cursor=self._cursor.copy(), previous=self)


def create_input_reader_from_file_representation(
    fr: FileRepresentation,
) -> InputReaderInterface:
    if fr.get_is_directory():
        return FlangFileInputReader(data=fr.get_content())

    return FlangTextInputReader(data=fr.get_content())
