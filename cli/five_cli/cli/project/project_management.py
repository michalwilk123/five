import os

import click

from five_cli.core.project import five_init, five_status


def get_paths(five_config_path, project_path):
    if project_path is None:
        project_path = os.getcwd()
    if five_config_path is None:
        five_config_path = os.path.join(project_path, '.five', 'config.json')
    return five_config_path, project_path


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.option(
    '--dont-track', is_flag=True, default=False, help='Add Five directory to project ignore list'
)
@click.pass_context
def init(ctx, five_config_path, project_path, dont_track):
    """Initialize a new Five project with version control."""
    import logging

    logger = logging.getLogger('five_cli.cli.project_management')
    five_config_path, project_path = get_paths(five_config_path, project_path)
    result = five_init(five_config_path, project_path, dont_track, click.echo, logger.info)

    if result.get('already_initialized'):
        click.echo(click.style('Warning: ' + result['error'], fg='yellow'))
        return

    click.echo(f'Five initialized successfully at {result["five_path"]}')


@click.option('--five-config-path', default=None, help='Path to Five config directory')
@click.option('--project-path', default=None, help='Path to project directory')
@click.option('--max-count', default=20, help='Maximum number of commits to show')
@click.pass_context
def status(ctx, five_config_path, project_path, max_count):
    """Show project status with commit history and uncommitted changes."""
    import logging

    logger = logging.getLogger('five_cli.cli.project_management')
    five_config_path, project_path = get_paths(five_config_path, project_path)
    result = five_status(
        five_config_path=five_config_path,
        project_path=project_path,
        max_count=max_count,
        sh=None,
        logger=logger.debug,
    )

    if not result['initialized']:
        click.echo(result['error'])
        return

    click.echo(f'Five Project Status ({result["total_commits"]} commits)')
    click.echo('=' * 50)

    # Show uncommitted changes if any
    uncommitted_changes = result.get('uncommitted_changes', [])
    if uncommitted_changes:
        click.echo(click.style('Uncommitted Changes:', fg='cyan', bold=True))
        for change in uncommitted_changes:
            # Format file status with color
            status_color = {
                'added': 'green',
                'modified': 'yellow',
                'deleted': 'red',
                'renamed': 'blue',
                'untracked': 'magenta',
            }.get(change['status'], 'white')

            status_str = click.style(f'[{change["status"]}]', fg=status_color)

            # Format additions/deletions like GitHub
            changes_str = ''
            if change['additions'] > 0 or change['deletions'] > 0:
                additions_str = (
                    click.style(f'+{change["additions"]}', fg='green')
                    if change['additions'] > 0
                    else ''
                )
                deletions_str = (
                    click.style(f'-{change["deletions"]}', fg='red')
                    if change['deletions'] > 0
                    else ''
                )
                if additions_str and deletions_str:
                    changes_str = f' ({additions_str}, {deletions_str})'
                elif additions_str:
                    changes_str = f' ({additions_str})'
                elif deletions_str:
                    changes_str = f' ({deletions_str})'

            click.echo(f'  {status_str} {change["file"]}{changes_str}')
        click.echo()

    for commit in result['commits']:
        # Format type with color
        type_color = (
            'green'
            if commit['type'] == 'user'
            else 'blue'
            if commit['type'] == 'codegen'
            else 'yellow'
        )
        type_str = click.style(f'[{commit["type"]}]', fg=type_color)

        # Show commit info
        click.echo(f'{click.style(commit["hash"], fg="yellow")} {type_str} {commit["date"]}')

        if commit['is_init']:
            click.echo('  └─ Initial Five setup')
        elif commit['type'] == 'codegen' and commit['conversation_hash']:
            click.echo(f'  └─ Conversation: {commit["conversation_hash"][:8]}...')

        click.echo()
