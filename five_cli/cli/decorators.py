from functools import wraps
from pathlib import Path

import click

from five_cli.cli.utils import create_click_logger
from five_cli.core.config import get_config_root, get_db_path, get_project_config_path
from five_cli.managers.db_manager import DatabaseManager
from five_cli.utils import NOOP_LOG
from five_cli.validation import FiveValidator


def _validate_project_path(ctx, param, value):
    value = value or Path.cwd()

    FiveValidator(raises=click.BadParameter, on_errors=None).project_path_exists(value).execute()

    ctx.params['project'] = value
    return value


def _validate_global_config_path(ctx, param, value):
    value = value or get_config_root()

    (
        FiveValidator(raises=click.BadParameter, on_errors=None)
        .config_path_exists(value)
        .setup_exists(value)
        .execute()
    )

    ctx.params['global_config'] = value
    return value


def _validate_project_config_path(ctx, param, value):
    """Validate the project-specific config path (where state or .git are stored)."""

    # Resolve default when not provided: depends on already-validated --project and --global-config
    if value is None:
        project_path: Path | None = ctx.params.get('project')
        global_config_path: Path | None = ctx.params.get('global_config')

        if project_path is None or global_config_path is None:
            raise click.BadParameter(
                'Cannot resolve project config without both --project and --global-config.'
            )

        # Ensure project is initialized in the database using validator
        (
            FiveValidator(raises=click.BadParameter, on_errors=None)
            .project_initialized(project_path, global_config_path)
            .execute()
        )

        # Look up project by absolute path in database bound to the resolved global config
        db_path = get_db_path(global_config_path)
        db_manager = DatabaseManager(NOOP_LOG, db_path)
        db_manager.connect(create_tables=False)

        project = db_manager.get_project_by_path(str(project_path.resolve()))
        value = get_project_config_path(global_config_path, project.name)

    (
        FiveValidator(raises=click.BadParameter, on_errors=None)
        .config_path_exists(value)
        .project_is_git_repository(value)
        .execute()
    )

    # add resolved project config path to ctx.params
    ctx.params['config'] = value

    return value


needs_project_path = click.option(
    '--project',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help='Path to the project directory to track (defaults to current directory)',
    callback=_validate_project_path,
)

needs_global_config_path = click.option(
    '--global-config',
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        'Path to the global five config directory where database is stored '
        '(defaults to XDG: ~/.config/five)'
    ),
    callback=_validate_global_config_path,
)

# Variant that also accepts --config as alias (only safe when project_config_path is not used)
needs_global_config_path_with_alias = click.option(
    '--global-config',
    '--config',
    'global_config',
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        'Path to the global five config directory where database is stored '
        '(defaults to XDG: ~/.config/five)'
    ),
    callback=_validate_global_config_path,
)

needs_project_config_path = click.option(
    '--config',
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=(
        'Path to the project-specific config directory where state and .git are stored '
        '(defaults to ~/.config/five/<project-name>)'
    ),
    callback=_validate_project_config_path,
)

needs_logger = click.option(
    '--verbose',
    '-v',
    is_flag=True,
    default=False,
    help='Enable verbose logging',
)


def five_command(
    *,
    project_path: bool = False,
    global_config_path: bool = False,
    project_config_path: bool = False,
    logger: bool = False,
):
    """Compose CLI decorators and inject resources as keyword-only args.

    - Adds click options using existing validators from this module based on flags.
    - Ensures correct sequencing when resolving project-specific config.
    - Calls the wrapped function with keyword-only injected arguments.
    """

    # If project_config_path is requested, ensure dependencies so default resolution works
    require_project = project_path or project_config_path
    require_global = global_config_path or project_config_path

    def decorator(func):
        @wraps(func)
        @click.pass_context
        def wrapper(ctx: click.Context, *args, **kwargs):
            # Build injected kwargs strictly based on requested resources
            injected: dict = {}

            if project_path:
                injected['project_path'] = kwargs.get('project')

            if global_config_path:
                injected['global_config_path'] = kwargs.get('global_config')

            if project_config_path:
                injected['project_config_path'] = kwargs.get('config')

            if logger:
                verbose = kwargs.get('verbose', False)
                injected['logger'] = create_click_logger(verbose)

            # Pass through all kwargs except those consumed by the decorator
            consumed_params = {'project', 'global_config', 'config', 'verbose'}
            passthrough = {k: v for k, v in kwargs.items() if k not in consumed_params}
            passthrough.update(injected)

            return func(ctx, **passthrough)

        # Apply validators/options in the correct order
        decorated = wrapper

        if require_project:
            decorated = needs_project_path(decorated)
        if require_global:
            # If also requiring project_config_path, avoid alias collision on --config
            if project_config_path:
                decorated = needs_global_config_path(decorated)
            else:
                decorated = needs_global_config_path_with_alias(decorated)
        if project_config_path:
            decorated = needs_project_config_path(decorated)
        if logger:
            decorated = needs_logger(decorated)

        return decorated

    return decorator
