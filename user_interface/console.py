class FiveConsoleInterface:
    def __init__(self):
        pass

    def prompt_initial_command(self) -> str:
        command_text = "Placeholder: Implement feature X"
        return command_text

    def ask_context_question(self) -> str | None:
        return None

    def confirm_change(self, change_item) -> bool:
        return False

    def show_results(self, changes_applied: int, git_hash: str | None):
        pass
