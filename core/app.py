from core.context_builder import FiveProjectContextBuilder
from core.project_config import FiveProjectConfig
from user_interface.console import FiveConsoleInterface
from utils.chatbot_controller import FiveChatbotController
from utils.project_tree_controller import FiveProjectTreeController
from utils.project_search import FiveProjectSearchEngine
from utils.version_control import FiveProjectVersionControl


def run_local_shell(config_path: str, project_location: str):
    config = FiveProjectConfig(config_path)
    project_tree_controller = FiveProjectTreeController(project_location)

    shell = FiveConsoleInterface(config)
    chatbot_controller = FiveChatbotController()

    project_searcher = FiveProjectSearchEngine(project_tree_controller)
    context_builder = FiveProjectContextBuilder(config.settings, project_searcher)

    version_control = FiveProjectVersionControl()

    run_shell_flow(
        config,
        shell,
        context_builder,
        project_tree_controller,
        chatbot_controller,
        version_control,
    )


def index_project(config_path: str, project_location: str):
    config = FiveProjectConfig(config_path)
    project_tree_controller = FiveProjectTreeController(project_location)
    chatbot_controller = FiveChatbotController()

    project_searcher = FiveProjectSearchEngine(
        config, project_tree_controller, chatbot_controller
    )
    project_searcher.index_project()


def run_shell_flow(
    config: FiveProjectConfig,
    shell: FiveConsoleInterface,
    context_builder: FiveProjectContextBuilder,
    project_tree_controller: FiveProjectTreeController,
    chatbot_controller: FiveChatbotController,
    version_control: FiveProjectVersionControl,
):
    user_command_str = shell.prompt_initial_command()

    project_context = gather_context(context_builder, shell, user_command_str)
    generation_plan = create_ai_plan(
        project_tree_controller, config, chatbot_controller, project_context
    )
    processed_changes = review_changes(shell, project_tree_controller, generation_plan)
    finalize_execution(
        project_tree_controller, version_control, shell, processed_changes, user_command_str
    )


def gather_context(
    context_builder: FiveProjectContextBuilder,
    shell: FiveConsoleInterface,
    user_command_str: str,
) -> dict:
    context_builder.gather_initial_context(user_command_str)

    while extra_input := shell.ask_context_question():
        context_builder.add_user_input(extra_input)

    return context_builder.compile()


def create_ai_plan(
    project_tree_controller: FiveProjectTreeController,
    config: FiveProjectConfig,
    chatbot_controller: FiveChatbotController,
    project_context: dict,
) -> list:
    blueprint = project_tree_controller.create_blueprint(config.rules, project_context)
    return chatbot_controller.generate_plan(blueprint)


def review_changes(
    shell: FiveConsoleInterface,
    project_tree_controller: FiveProjectTreeController,
    generation_plan: list,
) -> list:
    approved_changes = []
    for change_item in generation_plan:
        while shell.confirm_change(change_item):
            modified_version = project_tree_controller.adjust_change(change_item)
            approved_changes.append(modified_version)
    return approved_changes


def finalize_execution(
    project_tree_controller: FiveProjectTreeController,
    version_control: FiveProjectVersionControl,
    shell: FiveConsoleInterface,
    processed_changes: list,
    user_command_str: str,
):
    project_tree_controller.materialize(processed_changes)
    version_control.create_snapshot(f"Implemented: {user_command_str}")
    shell.show_results(
        changes_applied=len(processed_changes), git_hash=version_control.last_commit
    )
