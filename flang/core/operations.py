"""
Location is a
"""


def read(flang_ast, user_ast, location): ...


def insert(flang_ast, user_ast, location, change_dict): ...


def delete(flang_ast, user_ast, location): ...


def commit(flang_ast, user_ast):
    """
    Validates user_ast

    Easiest way to validate user_ast is to generate the project from tree, reparse the project
    and then compare if old and generated trees are the same
    """
    ...
