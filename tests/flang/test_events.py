import unittest

from flang.runtime.spec_evaluation_runtime import LinkStorage
from flang.structures import (
    FlangAbstractMatchObject,
    FlangComplexMatchObject,
    FlangTextMatchObject,
    ScopeTree,
)
from flang.utils.exceptions import (
    LinkOutOfScopeError,
    UnknownLinkDeclarationError,
    UnknownLinkNameError,
)

TEST_MATCH_OBJECT = FlangAbstractMatchObject(
    identifier="__abstract_match__",
    content=[
        FlangComplexMatchObject(
            identifier="/path/to/project:code[0]",
            content=[
                FlangTextMatchObject(
                    identifier="/path/to/project:code.code-parts.nl[0]",
                    content="\n",
                )
            ],
        ),
        FlangComplexMatchObject(
            identifier="/path/to/project:code[1]",
            content=[
                FlangComplexMatchObject(
                    identifier="/path/to/project:code.code-parts.import[0]",
                    content=[
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.text@0[0]",
                            content="from ",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.module[0]",
                            content="math",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.text@1[0]",
                            content=" import ",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.object[0]",
                            content="sin",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.nl[1]",
                            content="\n",
                        ),
                    ],
                )
            ],
        ),
        FlangComplexMatchObject(
            identifier="/path/to/project:code[2]",
            content=[
                FlangComplexMatchObject(
                    identifier="/path/to/project:code.code-parts.import[1]",
                    content=[
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.text@0[1]",
                            content="from ",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.module[1]",
                            content="math",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.text@1[1]",
                            content=" import ",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.object[1]",
                            content="pi",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.nl[2]",
                            content="\n",
                        ),
                    ],
                )
            ],
        ),
        FlangComplexMatchObject(
            identifier="/path/to/project:code[3]",
            content=[
                FlangComplexMatchObject(
                    identifier="/path/to/project:code.code-parts.import[2]",
                    content=[
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.text@0[2]",
                            content="from ",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.module[2]",
                            content="math",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.text@1[2]",
                            content=" import ",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.import.object[2]",
                            content="cos",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.nl[3]",
                            content="\n",
                        ),
                    ],
                )
            ],
        ),
        FlangComplexMatchObject(
            identifier="/path/to/project:code[4]",
            content=[
                FlangTextMatchObject(
                    identifier="/path/to/project:code.code-parts.nl[4]",
                    content="\n",
                )
            ],
        ),
        FlangComplexMatchObject(
            identifier="/path/to/project:code[5]",
            content=[
                FlangComplexMatchObject(
                    identifier="/path/to/project:code.code-parts.function-call[0]",
                    content=[
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.reference[3]",
                            content="sin",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.text@0[0]",
                            content="(",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.argument[0]",
                            content="10",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.text@1[0]",
                            content=")",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.nl[5]",
                            content="\n",
                        ),
                    ],
                )
            ],
        ),
        FlangComplexMatchObject(
            identifier="/path/to/project:code[6]",
            content=[
                FlangComplexMatchObject(
                    identifier="/path/to/project:code.code-parts.function-call[1]",
                    content=[
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.reference[4]",
                            content="cos",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.text@0[1]",
                            content="(",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.argument[1]",
                            content="pi",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.function-call.text@1[1]",
                            content=")",
                        ),
                        FlangTextMatchObject(
                            identifier="/path/to/project:code.code-parts.nl[6]",
                            content="\n",
                        ),
                    ],
                )
            ],
        ),
    ],
)


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


TEST_SCOPE_TREE = ScopeTree.from_dict(TEST_TREE)


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
        self.assertDictEqual(TEST_TREE, TEST_SCOPE_TREE.to_dict())

    def test_add_node(self):
        tree = ScopeTree("A", parent=None)

        for parent_id, node_id in self.TEST_TREE_NODE_ARRAY:
            tree.add_node(parent_id, node_id)

        self.assertDictEqual(TEST_TREE, tree.to_dict())

    def test_search(self):
        tree = ScopeTree("A", parent=None)

        for parent_id, node_id in self.TEST_TREE_NODE_ARRAY:
            tree.add_node(parent_id, node_id)

        self.assertIsNotNone(tree.get_("C"))
        self.assertIsNotNone(tree.get_("B"))
        self.assertIsNotNone(tree.get_("I"))
        self.assertIsNotNone(tree.get_("C3"))
        self.assertIsNotNone(tree.get_("C6"))

        node = tree.get_("C3")
        self.assertTrue(node.contains("C4"))
        self.assertTrue(node.contains("C6"))

        node = tree.get_("A")
        self.assertTrue(node.contains("C4"))
        self.assertTrue(node.contains("C6"))

        node = tree.get_("E")
        self.assertFalse(node.contains("C4"))
        self.assertFalse(node.contains("C6"))


class LinkStorageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.link_storage = LinkStorage(TEST_SCOPE_TREE)
        self.link_storage.declare(
            "id1", "variable", "python_variable_name", scope_start="C"
        )
        self.link_storage.declare("id2", "variable", "CppVariable", scope_start="C3")
        self.link_storage.declare("id3", "variable", "javaVariable", scope_start="E")

    def test_link_can_be_accessed(self):
        self.assertEqual(
            "id1", self.link_storage.connect("C6", "variable", "python_variable_name")
        )
        self.assertEqual(
            "id1", self.link_storage.connect("C", "variable", "python_variable_name")
        )

        self.assertEqual(
            "id2", self.link_storage.connect("C4", "variable", "CppVariable")
        )

        self.assertEqual(
            "id3", self.link_storage.connect("G", "variable", "javaVariable")
        )
        self.assertEqual(
            "id3", self.link_storage.connect("H", "variable", "javaVariable")
        )
        self.assertEqual(len(self.link_storage.connected_symbols), 5)

    def test_link_out_of_scope(self):
        with self.assertRaises(LinkOutOfScopeError):
            self.link_storage.connect("D", "variable", "python_variable_name")

        with self.assertRaises(LinkOutOfScopeError):
            self.link_storage.connect("H", "variable", "python_variable_name")

        with self.assertRaises(LinkOutOfScopeError):
            self.link_storage.connect("I", "variable", "javaVariable")

        self.assertEqual(len(self.link_storage.connected_symbols), 0)

    def test_unknown_declaration(self):
        with self.assertRaises(UnknownLinkDeclarationError):
            self.link_storage.connect(
                "C", "this_declaration_does_not_exist", "python_variable_name"
            )

    def test_unknown_link_name(self):
        with self.assertRaises(UnknownLinkNameError):
            self.link_storage.connect(
                "C", "variable", "this_variable_name_does_not_exist"
            )


# class SpecEvaluationRuntimeTestCase(unittest.TestCase):
#     def setUp(self) -> None:
#         self.runtime =


class FlangEventsTestCase(unittest.TestCase): ...
