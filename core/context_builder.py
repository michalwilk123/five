from ..utils.project_search import FiveProjectSearchEngine


class FiveProjectContextBuilder:
    def __init__(self, settings: dict, project_search: FiveProjectSearchEngine):
        self._context_data: dict = {}
        self._project_settings: dict = settings
        self._search_utility: FiveProjectSearchEngine = project_search
        pass

    def gather_initial_context(self, user_command_str: str):
        pass

    def add_user_input(self, extra_input: str):
        pass

    def compile(self) -> dict:
        return self._context_data.copy()
