import click

from five_cli.cli.project import project_management, task_tracking, task_history


@click.group()
@click.pass_context
def project(ctx):
    """Manage Five projects and version control."""
    pass


# Add commands from project_management module
project.command()(project_management.init)
project.command()(project_management.status)

# Add commands from task_tracking module
project.command()(task_tracking.start_conversation)
project.command()(task_tracking.stop_conversation)
project.command()(task_tracking.changes)
project.command('completed-tasks')(task_tracking.completed_tasks)

# Add commands from task_history module
project.command()(task_history.undo)
project.command()(task_history.redo)
project.command()(task_history.edit)
