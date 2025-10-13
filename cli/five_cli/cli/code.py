import logging
import os
import shlex
import subprocess
import sys
import time

import click

from five_cli.utils.net import find_running_proxy, proxy_env_vars

DEFAULT_PORT = 8089


def ensure_proxy():
    port = find_running_proxy(DEFAULT_PORT, 100)
    if port:
        return port
    from five_cli.proxy import control

    control.main(['start'])
    time.sleep(1)
    return find_running_proxy(DEFAULT_PORT, 100)


@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.option(
    '--claude-command', help='Command to run Claude (e.g., "claude" or "python -m claude")'
)
@click.option('--no-proxy', is_flag=True, help='Skip proxy and run claude directly')
@click.pass_context
def code(ctx, claude_command, no_proxy):
    """
    Launch Claude Code with optional proxy support.

    Starts Claude Code and, unless --no-proxy is used, manages a proxy server
    to capture conversation data for Five tracking. Any extra args are passed through.

    Examples:
        five code                    # Start Claude Code with proxy
        five code -p "Fix this bug"  # Pass prompt directly to Claude
        five code --no-proxy         # Start without proxy
    """
    verbose = ctx.parent.obj.get('verbose', False) if ctx.parent else False
    logger = logging.getLogger('five_cli.cli.code')

    env = os.environ.copy()

    if not no_proxy:
        port = ensure_proxy()
        if port:
            env.update(proxy_env_vars(port))
            logger.info(f'Using proxy on port {port}')
        else:
            logger.info('No proxy available - running claude directly')

    try:
        base = shlex.split(claude_command) if claude_command else ['claude']
        cmd = base + list(ctx.args)
        if verbose:
            logger.info(f'Running: {" ".join(cmd)}')

        result = subprocess.run(cmd, env=env)
        sys.exit(result.returncode)
    except FileNotFoundError:
        click.echo('claude command not found')
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
