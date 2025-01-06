"""
Location is a
"""


def select(log, template_tree, flang_tree, location):
    """
    returns the list of specification of flang_tree at given location query. Location can be fuzzy.
    """
    ...


def insert(log, template_tree, flang_tree, location, change_dict):
    """
    Modifies the
    """
    ...


def delete(log, template_tree, flang_tree, location):
    """
    Modifies the
    """
    ...


def update(log, template_tree, flang_tree, location, change_dict): ...


def commit(log, template_tree, flang_tree):
    """
    Validates flang_tree

    Easiest way to validate flang_tree is to generate the project from tree, reparse the project
    and then compare if old and generated trees are the same
    """
    ...
