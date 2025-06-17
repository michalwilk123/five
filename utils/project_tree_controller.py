class FiveProjectTreeController:
    """
    Abstraction to interact with the codebase
    """

    def __init__(self, project_location: str):
        self.project_location = project_location

    def create_blueprint(self, rules: list, project_context: dict):
        return {"type": "code_blueprint", "details": "placeholder_blueprint_info"}

    def adjust_change(self, change_item):
        return change_item

    def materialize(self, processed_changes: list):
        pass
