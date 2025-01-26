import signal
from contextlib import contextmanager


# https://stackoverflow.com/questions/366682/how-to-limit-execution-time-of-a-function-call
@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
