import json
import os

import click

from five_cli.core.config import get_five_paths
from five_cli.core.events import _load_completed_tasks, on_ai_agent_start, on_ai_agent_stop
from five_cli.core.models import Conversation, Message, TaskChangePatch
from five_cli.vcs.git_utils import GitRepo


def get_paths(five_config_path, project_path):
    if project_path is None:
        project_path = os.getcwd()
    if five_config_path is None:
        five_config_path = os.path.join(project_path, '.five', 'config.json')
    return five_config_path, project_path


def output_json(data, pretty_print):
    if pretty_print:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(json.dumps(data))


def get_task_by_id(tasks, target_id):
    for task in tasks:
        if task['id'] == target_id:
            return task
    return None


def _create_task_id_matcher(task_id: str):
    """Create a predicate function to match commits by TaskChangePatch ID."""
    def matches(message: str) -> bool:
        patch = TaskChangePatch.decode(message)
        return patch is not None and patch.id == task_id
    return matches


def build_change_detail(task, git_dir, project_path):
    change_data = {
        'id': task['id'],
        'timestamp': task['timestamp'],
        'references': task['references'],
        'patch': None,
    }

    repo = GitRepo(git_dir, project_path)

    # Find commit by matching TaskChangePatch ID
    matcher = _create_task_id_matcher(str(task['id']))
    commit_hash = repo.find_commit_by_message_match(matcher)
    if commit_hash:
        change_data['patch'] = repo.get_commit_diff(commit_hash)

    return change_data


def build_changes_list(tasks):
    return [
        {'id': task['id'], 'timestamp': task['timestamp'], 'references': task['references']}
        for task in reversed(tasks)
    ]


def get_completed_task_by_id(tasks, target_id):
    for task in tasks:
        if task['id'] == target_id:
            return task
    return None


def build_completed_task_detail(task, git_dir, project_path):
    task_data = {
        'references': task['references'],
        'conversation': task['conversation'],
        'changes': task['id'],
    }
    return task_data


def build_completed_task_list_item(task, git_dir, project_path):
    task_data = {
        'references': task['references'],
        'conversation': task['conversation'],
        'changes': None,
    }

    repo = GitRepo(git_dir, project_path)

    # Find commit by matching TaskChangePatch ID
    matcher = _create_task_id_matcher(str(task['id']))
    commit_hash = repo.find_commit_by_message_match(matcher)
    if commit_hash:
        task_data['changes'] = repo.get_commit_diff(commit_hash)

    return task_data


def build_completed_tasks_list(tasks, git_dir, project_path):
    return [build_completed_task_list_item(task, git_dir, project_path) for task in reversed(tasks)]


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.pass_context
def start_conversation(ctx, five_config_path, project_path):
    """Mark the point where the AI assistant prompt begins and record the current project state."""
    import logging

    logger = logging.getLogger('five_cli.cli.task_tracking')
    five_config_path, project_path = get_paths(five_config_path, project_path)
    on_ai_agent_start(five_config_path, project_path, click.echo, logger.info)
    click.echo('Entered Five interface')


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.option('--task-json', default=None, help='JSON-encoded CodeGenerationTask')
@click.pass_context
def stop_conversation(ctx, five_config_path, project_path, task_json):
    """Create a codegen commit with conversation tracking.

    Provide --task-json containing a CodeGenerationTask object as JSON.

    Format (keys are required unless noted):
    {
      "referred_by": ["<commit-hash>", "..."],
      "conversation": {
        "user_prompt": "<string>",
        "messages": [
          {
            "role": "user" | "assistant",
            "content": "<string|null>",
            "arguments": { ... } | null,
            "results": { ... } | null,
            "type": "text" | "tool_use" | "tool_result"
          }
        ],
        "temperature": <number>,
        "model_name": "<string>"
      }
    }

    Notes:
    - id and timestamp are optional; they will be generated if not provided.
    - Conversation/reference hashes are not required and will be ignored.
    """
    import logging

    logger = logging.getLogger('five_cli.cli.task_tracking')
    five_config_path, project_path = get_paths(five_config_path, project_path)

    data = json.loads(task_json)
    conversation_data = data['conversation']
    conversation = Conversation(
        user_prompt=conversation_data['user_prompt'],
        messages=[Message(**m) for m in conversation_data['messages']],
        temperature=float(conversation_data['temperature']),
        model_name=conversation_data['model_name'],
    )
    references = data['referred_by']

    on_ai_agent_stop(
        five_config_path, project_path, references, conversation, click.echo, logger.info
    )
    click.echo('Committed changes')


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.option('--id', 'change_id', default=None, help='Show detailed diff for specific change ID')
@click.option('--pp', is_flag=True, help='Pretty print JSON output')
@click.pass_context
def changes(ctx, five_config_path, project_path, change_id, pp):
    """Show list of changes or detailed view for specific change ID in JSON format."""
    five_config_path, project_path = get_paths(five_config_path, project_path)
    five_path, git_dir = get_five_paths(five_config_path)

    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')

    if not os.path.exists(completed_tasks_file):
        output_json({'error': 'No completed tasks found. Run some AI agent sessions first.'}, pp)
        return

    tasks = _load_completed_tasks(completed_tasks_file)

    if not tasks:
        output_json({'error': 'No completed tasks found.'}, pp)
        return

    if change_id is not None:
        target_id = int(change_id)
        task = get_task_by_id(tasks, target_id)

        if not task:
            output_json({'error': f'Change with ID {target_id} not found.'}, pp)
            return

        change_data = build_change_detail(task, git_dir, project_path)
        output_json(change_data, pp)
    else:
        changes_data = build_changes_list(tasks)
        output_json(changes_data, pp)


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.option('--pp', is_flag=True, help='Pretty print JSON output')
@click.argument('task_id', required=False)
@click.pass_context
def completed_tasks(ctx, five_config_path, project_path, pp, task_id):
    """Show completed tasks in detail or list view in JSON format."""
    five_config_path, project_path = get_paths(five_config_path, project_path)
    five_path, git_dir = get_five_paths(five_config_path)

    completed_tasks_file = os.path.join(five_path, 'completed_tasks.json')

    if not os.path.exists(completed_tasks_file):
        output_json({'error': 'No completed tasks found. Run some AI agent sessions first.'}, pp)
        return

    tasks = _load_completed_tasks(completed_tasks_file)

    if not tasks:
        output_json({'error': 'No completed tasks found.'}, pp)
        return

    if task_id is not None:
        target_id = int(task_id)
        task = get_completed_task_by_id(tasks, target_id)

        if not task:
            output_json({'error': f'Task with ID {target_id} not found.'}, pp)
            return

        task_data = build_completed_task_detail(task, git_dir, project_path)
        output_json(task_data, pp)
    else:
        tasks_data = build_completed_tasks_list(tasks, git_dir, project_path)
        output_json(tasks_data, pp)
