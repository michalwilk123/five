import os
from pathlib import Path


def load_env():
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value


load_env()
