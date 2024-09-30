import unittest

from flang.runtime.spec_evaluation_runtime import LinkStorage
from flang.structures import ScopeTree

TEST_TREE = {
    "A": {
        "B": {
            "C": {"C1": {"C2": {"C3": {"C4": None, "C5": None, "C6": None}}}},
            "D": None,
        },
        "E": {"F": None, "G": {"H": None}},
        "I": None,
    }
}


class ScopeTreeTestCase(unittest.TestCase):
    TEST_TREE_NODE_ARRAY = (
        ("A", "B"),
        ("A", "E"),
        ("B", "C"),
        ("C", "C1"),
        ("C1", "C2"),
        ("C2", "C3"),
        ("C3", "C4"),
        ("C3", "C5"),
        ("C3", "C6"),
        ("B", "D"),
        ("E", "F"),
        ("E", "G"),
        ("G", "H"),
        ("A", "I"),
    )

    def test_serialization(self):
        tree = ScopeTree.from_dict(TEST_TREE)
        self.assertDictEqual(TEST_TREE, tree.to_dict())

    def test_add_node(self):
        tree = ScopeTree("A", parent=None)

        for parent_id, node_id in self.TEST_TREE_NODE_ARRAY:
            tree.add_node(parent_id, node_id)

        self.assertDictEqual(TEST_TREE, tree.to_dict())
    
    def test_search(self):
        tree = ScopeTree("A", parent=None)

        for parent_id, node_id in self.TEST_TREE_NODE_ARRAY:
            tree.add_node(parent_id, node_id)
        

class LinkStorageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.link_storage = LinkStorage()

    def test_simple(self):
        self.link_storage.declare()


class FlangEventsTestCase(unittest.TestCase): ...
