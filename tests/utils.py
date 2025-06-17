from utils.chatbot_controller import FiveChatbotController
from utils.project_tree_controller import FiveProjectTreeController


class FiveChatbotControllerMock(FiveChatbotController):
    def __init__(self):
        super().__init__(api_key="mock_api_key") # Call super if it has own __init__
        self.create_index_json_response = []
        self.search_index_string_response = ""

    def run(self, prompt: str, output_format: str = "string", **kwargs) -> any:
        if output_format == "json":
            # Simulate response for CREATE_INDEX_PROMPT
            # This can be customized per test case by setting self.create_index_json_response
            return self.create_index_json_response
        elif output_format == "string":
            # Simulate response for SEARCH_INDEX_PROMPT
            # This can be customized per test case by setting self.search_index_string_response
            return self.search_index_string_response
        return None


class FiveProjectTreeControllerMock(FiveProjectTreeController):
    def __init__(self, project_location: str = "dummy_project_location"):
        super().__init__(project_location) # Call super if it has own __init__
        # self.project_location is already set by the super().__init__
        self.passages_data = [] # To be set by the test

    def get_passages(self, globs: list[str]) -> list[tuple[str, str]]:
        # Return predefined passages, globs are ignored for this mock
        return self.passages_data
