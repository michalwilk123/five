import dataclasses
import unittest

from flang.structures import SearchableTree
from flang.utils.exceptions import (
    DuplicateNodeInsertionError,
    ExactSameNodeInsertionError,
)


@dataclasses.dataclass
class TestTreeStructure(SearchableTree):
    some_data: str
    test_data: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SimpleTree(SearchableTree):
    pass


tree_native = SimpleTree(name="A", children=[SimpleTree(name="B"), SimpleTree(name="C")])
tree_dict = {
    "name": "A",
    "children": [
        {
            "name": "B",
            "children": [
                {
                    "name": "C",
                    "children": [
                        {
                            "name": "C1",
                            "children": [
                                {
                                    "name": "C2",
                                    "children": [
                                        {
                                            "name": "C3",
                                            "children": [
                                                {"name": "C4", "children": None},
                                                {"name": "C5", "children": None},
                                                {"name": "C6", "children": None},
                                            ],
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                },
                {"name": "D", "children": None},
            ],
        },
        {
            "name": "E",
            "children": [
                {"name": "F", "children": None},
                {
                    "name": "G",
                    "children": [
                        {"name": "H", "children": None},
                    ],
                },
            ],
        },
        {"name": "I", "children": None},
    ],
}


class SearchableTreeTestCase(unittest.TestCase):
    TEST_TREE_NODE_ARRAY = (
        ("A", "B"),
        ("A", "E"),
        ("A.B", "C"),
        ("A.B.C", "C1"),
        ("A.B.C.C1", "C2"),
        ("A.B.C.C1.C2", "C3"),
        ("A.B.C.C1.C2.C3", "C4"),
        ("A.B.C.C1.C2.C3", "C5"),
        ("A.B.C.C1.C2.C3", "C6"),
        ("A.B", "D"),
        ("A.E", "F"),
        ("A.E", "G"),
        ("A.E.G", "H"),
        ("A", "I"),
    )

    def test_simple_example(self):
        TestTreeStructure(name="somename", some_data="lalala")

    def test_serialization(self):
        tree_native_dict = tree_native.to_dict()

        self.assertEqual(SimpleTree.from_dict(tree_native_dict), tree_native)

        simple_tree = SimpleTree.from_dict(tree_dict)
        self.assertDictEqual(simple_tree.to_dict(), tree_dict)
        self.assertDictEqual(
            SimpleTree.from_dict(simple_tree.to_dict()).to_dict(), tree_dict
        )

    def test_search(self):
        tree = SimpleTree.from_dict(tree_dict)

        for path in set(it for it, _ in self.TEST_TREE_NODE_ARRAY):
            node = tree.full_search(path)
            self.assertIsNotNone(node)
            self.assertEqual(node.location, path)
            self.assertIs(node.root, tree)

            node_name = path.split(node.path_separator)[-1]
            self.assertEqual(node.name, node_name)

        self.assertIsNone(tree.full_search("wrong.path"))

    def test_adding_nodes(self):
        tree = SimpleTree.from_dict(tree_dict)

        for path in set(it for it, _ in self.TEST_TREE_NODE_ARRAY):
            parent = tree.full_search(path)
            node = SearchableTree(name="NEW_NODE")
            parent.add_node(node, allow_duplicates=False)

        for path in set(it for it, _ in self.TEST_TREE_NODE_ARRAY):
            self.assertIsNotNone(tree.full_search(f"{path}{tree.path_separator}NEW_NODE"))

    def test_search_down(self):
        tree = SimpleTree.from_dict(tree_dict)
        node = tree.full_search("A.B.C.C1")

        self.assertIsNotNone(node.search_down("C2"))
        self.assertIsNotNone(node.search_down("C2.C3"))
        self.assertIsNotNone(node.search_down("C2.C3.C6"))

        self.assertIsNone(node.search_down_full_path("A.B.C"))
        self.assertIsNone(node.search_down_full_path("wrong_path"))

    def test_relative_search(self):
        tree = SimpleTree.from_dict(tree_dict)

        node = tree.full_search("A.B.C.C1.C2.C3.C4")
        needle = node.relative_search(".C5")
        self.assertIsNotNone(needle)
        self.assertEqual(needle.name, "C5")

        node = tree.full_search("A.E.G")
        needle = node.relative_search("..B.D")
        self.assertIsNotNone(needle)
        self.assertEqual(needle.name, "D")

        needle = node.relative_search("..B.C.C1.C2.C3.C6")
        self.assertIsNotNone(needle)
        self.assertEqual(needle.name, "C6")

    def test_adding_nodes_duplicates(self):
        tree = SimpleTree.from_dict(tree_dict)
        node = tree.full_search("A.B.C.C1.C2.C3")
        start_size = len(node.children)

        for _ in range(3):
            new_node = SimpleTree(name="Duplicate")
            node.add_node(new_node)

        self.assertEqual(start_size, 3)

    def test_should_throw_error_when_adding_same_node(self):
        tree = SimpleTree.from_dict(tree_dict)

        tree = SimpleTree.from_dict(tree_dict)
        node = tree.full_search("A.B.C.C1.C2.C3")
        new_node = SimpleTree(name="Duplicate")

        with self.assertRaises(ExactSameNodeInsertionError):
            for _ in range(2):
                node.add_node(new_node)

    def test_should_throw_error_when_duplicate_not_allowed(self):
        tree = SimpleTree.from_dict(tree_dict)

        tree = SimpleTree.from_dict(tree_dict)
        node = tree.full_search("A.B.C.C1.C2.C3")

        with self.assertRaises(DuplicateNodeInsertionError):
            for _ in range(2):
                new_node = SimpleTree(name="Duplicate")
                node.add_node(new_node, allow_duplicates=False)
