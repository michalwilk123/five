from __future__ import annotations

import abc
import fnmatch
import io
import pathlib
import re

from .ast import UserASTTextNode


class IntermediateFileObject:
    def __init__(self, path: str, content: list | None = None) -> None:
        self.path = pathlib.Path(path)
        self._content = content

        assert self.path.exists()

    @property
    def content(self) -> str | list[IntermediateFileObject]:
        if self._content is not None:
            return self._content

        if self.path.is_dir():
            return [IntermediateFileObject(str(file)) for file in self.path.iterdir()]
        else:
            with open(self.path) as f:
                return f.read()

    @property
    def filename(self) -> str:
        return self.path.name

    def get_input_reader(self) -> FlangFileInputReader | FlangTextInputReader:
        if self.path.is_dir():
            assert isinstance(self.content, list)
            return FlangFileInputReader(self.content, filename=self.path.name)

        assert isinstance(self.content, str)
        return FlangTextInputReader(self.content)

    @staticmethod
    def get_first_matched_file(
        list_of_files: list[IntermediateFileObject], pattern: str, variant: str
    ) -> IntermediateFileObject | None:
        assert variant in ("filename", "glob", "regex")

        if variant == "glob":
            pattern = fnmatch.translate(pattern)

        def _is_pathname_matched(file_object):
            if variant == "filename":
                return file_object.path.name == pattern

            return re.match(pattern, file_object.path.name)

        try:
            return next(filter(_is_pathname_matched, list_of_files))
        except StopIteration:
            return None


sanity_check = True


class BaseFlangInputReader(abc.ABC):
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
    def copy(self) -> BaseFlangInputReader:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def previous(self) -> BaseFlangInputReader:
        raise NotImplementedError


class FlangTextInputReader(BaseFlangInputReader):
    def __init__(
        self,
        data: str | io.StringIO,
        cursor: int | None = None,
        previous: FlangTextInputReader | None = None,
    ) -> None:
        self._data = io.StringIO(data) if isinstance(data, str) else data
        self._cursor = cursor or 0
        self._previous = previous

    def read(self, size=None) -> str:
        self._data.seek(self._cursor)  # look-up correct scope of input stream
        data = self._data.read() if size is None else self._data.read(size)
        self._data.seek(self._cursor)  # return to the initial state
        return data

    def get_key(self):
        import warnings

        warnings.warn("NOT IMPLEMENTED!")
        return 0

    def consume_data(self, data: UserASTTextNode) -> None:
        if sanity_check:
            consumed_data = self.read(data.size())
            assert consumed_data == data.get_raw_content(), "{} {}".format(
                consumed_data, data.get_raw_content()
            )
        self._cursor += data.size()

    def copy(self) -> FlangTextInputReader:
        return FlangTextInputReader(self._data, cursor=self._cursor, previous=self)

    @property
    def previous(self) -> FlangTextInputReader:
        assert self._previous is not None
        return self._previous


class FlangFileInputReader(BaseFlangInputReader):
    def __init__(
        self,
        data: list[IntermediateFileObject],
        filename: str,
        cursor: list | None = None,
        previous: FlangFileInputReader | None = None,
    ) -> None:
        self._data = data
        self._cursor = list(range(len(data))) if cursor is None else cursor.copy()
        self._previous = previous
        self.filename = filename

    def read(self) -> list[IntermediateFileObject]:
        return [self._data[i] for i in self._cursor]

    def get_key(self):
        import warnings

        warnings.warn("NOT IMPLEMENTED!")
        return 0

    def consume_data(self, data: FlangFileInputReader) -> None:
        filenames = [f.path.name for f in self._data]
        self._cursor.remove(filenames.index(data.filename))

        if sanity_check:
            assert len(self._cursor) == len(set(self._cursor))

    def copy(self) -> FlangFileInputReader:
        return FlangFileInputReader(
            self._data, filename=self.filename, cursor=self._cursor.copy(), previous=self
        )

    @property
    def previous(self) -> FlangFileInputReader:
        assert self._previous is not None
        return self._previous
