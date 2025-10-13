import logging
import os
import subprocess
import sys
import time
from typing import Callable

import click

from five_cli.utils.net import find_free_port, find_running_proxy, is_proxy_healthy
from five_cli.utils.proc import (
    find_proxy_processes,
    is_process_running,
    kill_process,
    read_pid_file,
    remove_pid_file,
    write_pid_file,
)

DEFAULT_PORT = 8089


def setup_logging(verbosity):
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level, format='[%(asctime)s] %(levelname)s %(message)s', datefmt='%H:%M:%S'
    )


def mitmproxy_available():
    try:
        import mitmproxy  # noqa: F401

        return True
    except Exception:
        return False


def get_proxy_runner_path():
    return os.path.join(os.path.dirname(__file__), '..', 'proxy_runner.py')


def spawn_proxy_process(port, log_file, verbosity):
    if not mitmproxy_available():
        logging.error('mitmproxy is not installed in this Python environment')
        return None

    selected_port = port
    if selected_port is None:
        free = find_free_port(DEFAULT_PORT, 10)
        if free is None:
            logging.error('could not find a free port near %d', DEFAULT_PORT)
            return None
        selected_port = free

    runner_path = get_proxy_runner_path()
    if not os.path.exists(runner_path):
        logging.error('proxy runner script not found: %s', runner_path)
        return None

    cmd = [
        sys.executable,
        runner_path,
        str(selected_port),
        os.path.abspath(log_file),
        str(verbosity),
    ]

    logging.info('starting proxy on port %d', selected_port)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=os.environ.copy(),
        )

        if not write_pid_file(selected_port, process.pid):
            logging.warning('failed to write PID file for port %d', selected_port)

        return selected_port
    except Exception as e:
        logging.error('error starting proxy: %s', e)
        return None


def stop_proxy_process(port, sh: Callable[[str], None]):
    pid = read_pid_file(port)
    stopped = False

    if pid and is_process_running(pid):
        if kill_process(pid):
            stopped = True
            sh(f'Stopped proxy process {pid}')
        else:
            logging.warning('failed to stop process %d', pid)

    remove_pid_file(port)

    if not stopped:
        proxy_pids = find_proxy_processes()
        for pid in proxy_pids:
            if kill_process(pid):
                stopped = True
                sh(f'Stopped proxy process {pid}')

    return stopped


def get_proxy_status(port):
    pid = read_pid_file(port)

    if pid and is_process_running(pid):
        if is_proxy_healthy(port):
            return True

    return False


def start_proxy(port, log_file, verbosity, sh: Callable[[str], None]):
    selected_port = spawn_proxy_process(port, log_file, verbosity)
    if not selected_port:
        return False

    time.sleep(3)  # Give proxy more time to start
    if not is_proxy_healthy(selected_port):
        logging.error('proxy failed health check on port %d', selected_port)
        # Try one more time after a longer wait
        time.sleep(2)
        if not is_proxy_healthy(selected_port):
            logging.error('proxy still failing health check, stopping')
            stop_proxy_process(selected_port, sh)
            return False
        else:
            logging.info('proxy health check passed on retry')

    sh(f'Proxy started on port {selected_port}')
    sh(f'Log file: {os.path.abspath(log_file)}')
    sh('Health: https://api.anthropic.com/custom-proxy-health-check')
    return True


def stop_proxy(sh: Callable[[str], None]):
    found_any = False

    for port in range(DEFAULT_PORT, DEFAULT_PORT + 100):
        if get_proxy_status(port):
            found_any = True
            if stop_proxy_process(port, sh):
                break

    if not found_any:
        sh('No proxy processes found')
        return False

    return True


def status_proxy(sh: Callable[[str], None]):
    running = find_running_proxy(DEFAULT_PORT, 100)
    if running:
        sh(f'Proxy is running on port {running}')
        sh('Health: https://api.anthropic.com/custom-proxy-health-check')
        return True
    sh('Proxy is not running')
    return False


@click.group()
@click.option('-v', '--verbose', count=True, help='Increase verbosity (use multiple times)')
@click.pass_context
def server(ctx, verbose):
    """Manage Claude proxy server."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@server.command()
@click.option('--port', type=int, help='Port to run proxy on')
@click.option('--log-file', default='claude_proxy.log', help='Log file path')
@click.pass_context
def start(ctx, port, log_file):
    """
    Start the proxy server for capturing Claude conversations.

    The proxy server intercepts requests to Claude API to capture
    conversation data for Five project tracking.
    """
    verbose = ctx.obj.get('verbose', 0)

    running = find_running_proxy(DEFAULT_PORT, 100)
    if running:
        click.echo(f'Proxy already running on port {running}')
        sys.exit(0)

    ok = start_proxy(port, log_file, verbose, click.echo)
    sys.exit(0 if ok else 1)


@server.command()
@click.pass_context
def stop(ctx):
    """
    Stop the running proxy server.

    Finds and terminates any running proxy processes.
    """
    ok = stop_proxy(click.echo)
    sys.exit(0 if ok else 1)


@server.command()
@click.pass_context
def status(ctx):
    """
    Show proxy server status and health information.

    Displays whether the proxy is running and provides health check URL.
    """
    ok = status_proxy(click.echo)
    sys.exit(0 if ok else 1)


@server.command()
@click.pass_context
def restart(ctx):
    """
    Restart the proxy server.

    Stops any running proxy processes and starts a new one.
    """
    verbose = ctx.obj.get('verbose', 0)

    stop_proxy(click.echo)
    time.sleep(1)
    ok = start_proxy(None, 'claude_proxy.log', verbose, click.echo)
    sys.exit(0 if ok else 1)
