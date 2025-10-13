import os
import signal
import subprocess


def get_pid_file_path(port):
    return f'/tmp/five-proxy-{port}.pid'


def write_pid_file(port, pid):
    try:
        with open(get_pid_file_path(port), 'w') as f:
            f.write(str(pid))
        return True
    except Exception:
        return False


def read_pid_file(port):
    try:
        with open(get_pid_file_path(port), 'r') as f:
            return int(f.read().strip())
    except Exception:
        return None


def remove_pid_file(port):
    try:
        os.remove(get_pid_file_path(port))
        return True
    except Exception:
        return False


def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_process(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except OSError:
        return False


def find_proxy_processes():
    try:
        result = subprocess.run(['pgrep', '-f', 'proxy_runner.py'], capture_output=True, text=True)
        if result.returncode == 0:
            return [int(p) for p in result.stdout.strip().split('\n') if p]
        return []
    except Exception:
        return []
