import abc


class BaseCommand(abc.ABC):
    def serialize(self) -> str: ...

    def deserialize(self, content: str): ...
