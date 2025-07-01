import os
import shelve
from contextlib import contextmanager


def setup_config_path(path_to_config_dir: str):
    if not os.path.exists(path_to_config_dir):
        os.makedirs(path_to_config_dir, exist_ok=True)

    return path_to_config_dir


def get_db_path(config_path: str, db_file_name: str):
    db_path = f"{db_file_name}.shelve"
    setup_config_path(config_path)

    return os.path.join(config_path, db_path)


import json


@contextmanager
def get_symbol_declarations_db(root_path: str):
    with shelve.open(get_db_path(root_path, "symbol-declarations"), "c") as _db:
        yield _db


@contextmanager
def get_symbol_file_locations_db(root_path: str):
    with shelve.open(get_db_path(root_path, "symbol-file-locations"), "c") as _db:
        yield _db
