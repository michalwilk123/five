from five_cli.utils import LogFunction


class BaseManager:
    def __init__(self, logger: LogFunction):
        self._log = logger
