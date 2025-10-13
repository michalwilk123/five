import json
import os

import click

from five_cli.core.project import (
    five_edit_confirm,
    five_edit_current,
    five_edit_run,
    five_edit_start,
    five_redo,
    five_undo,
)


def get_paths(five_config_path, project_path):
    if project_path is None:
        project_path = os.getcwd()
    if five_config_path is None:
        five_config_path = os.path.join(project_path, '.five', 'config.json')
    return five_config_path, project_path


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.argument('task_id', required=False, type=int)
@click.pass_context
def undo(ctx, five_config_path, project_path, task_id):
    """Undo a completed task by removing its commit from history.

    If TASK_ID is not provided, undoes the most recent task.
    This will save the undone task to undo_items.json for potential redo later.
    """
    import logging

    logger = logging.getLogger('five_cli.cli.task_history')
    five_config_path, project_path = get_paths(five_config_path, project_path)
    result = five_undo(five_config_path, project_path, task_id, click.echo, logger.info)

    if 'error' in result:
        click.echo(click.style(f'Error: {result["error"]}', fg='red'))
        return

    click.echo(
        click.style(
            f'Successfully undone task {result["undone_task_id"]} (commit {result["commit_hash"]})',
            fg='green',
        )
    )


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.argument('task_id', required=False, type=int)
@click.pass_context
def redo(ctx, five_config_path, project_path, task_id):
    """Redo a previously undone task by reapplying its changes.

    If TASK_ID is not provided, redoes the most recently undone task.
    """
    import logging

    logger = logging.getLogger('five_cli.cli.task_history')
    five_config_path, project_path = get_paths(five_config_path, project_path)
    result = five_redo(five_config_path, project_path, task_id, click.echo, logger.info)

    if 'error' in result:
        click.echo(click.style(f'Error: {result["error"]}', fg='red'))
        return

    click.echo(
        click.style(
            f'Successfully redone task {result["redone_task_id"]}',
            fg='green',
        )
    )


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.option('--current', is_flag=True, help='Show current edit state as JSON')
@click.option('--run', 'run_prompt', default=None, help='Run claude with modified prompt')
@click.option('--confirm', is_flag=True, help='Confirm and commit edit changes')
@click.argument('task_id', required=False, type=int)
@click.pass_context
def edit(ctx, five_config_path, project_path, current, run_prompt, confirm, task_id):
    """Edit a completed task by modifying its commit.

    TASK_ID is required when starting an edit session.

    Subcommands:
    - five project edit TASK_ID: Start edit mode for a task
    - five project edit --current: Show current edit state
    - five project edit --run "prompt": Reset changes and prepare for claude run
    - five project edit --confirm: Commit changes and finish edit
    """
    import logging

    logger = logging.getLogger('five_cli.cli.task_history')
    five_config_path, project_path = get_paths(five_config_path, project_path)

    if current:
        result = five_edit_current(five_config_path, project_path, click.echo, logger.info)
        if 'error' in result:
            click.echo(click.style(f'Error: {result["error"]}', fg='red'))
            return
        click.echo(json.dumps(result['task'], indent=2))
        return

    if run_prompt is not None:
        result = five_edit_run(five_config_path, project_path, run_prompt, click.echo, logger.info)
        if 'error' in result:
            click.echo(click.style(f'Error: {result["error"]}', fg='red'))
            return
        click.echo(click.style(f'Cleared all changes for task {result["task_id"]}', fg='yellow'))
        click.echo(f'Run: claude -m "{run_prompt}"')
        return

    if confirm:
        result = five_edit_confirm(five_config_path, project_path, click.echo, logger.info)
        if 'error' in result:
            click.echo(click.style(f'Error: {result["error"]}', fg='red'))
            return
        click.echo(click.style(f'Edit confirmed for task {result["task_id"]}', fg='green'))
        return

    if task_id is None:
        click.echo(click.style('Error: TASK_ID is required to start edit mode', fg='red'))
        return

    result = five_edit_start(five_config_path, project_path, task_id, click.echo, logger.info)
    if 'error' in result:
        click.echo(click.style(f'Error: {result["error"]}', fg='red'))
        return

    click.echo(click.style(f'Edit mode started for task {result["task_id"]}', fg='green'))
    click.echo('Use the following commands:')
    click.echo('  five project edit --current          # Show current task')
    click.echo('  five project edit --run "prompt"     # Reset and prepare for claude')
    click.echo('  five project edit --confirm          # Commit changes')
