import copy
import filecmp
import os
import tempfile
import unittest

from flang.structures import (
    FileOperation,
    FileRepresentation,
    VirtualFileRepresentation,
)

PATH_TO_MODULE = "tests/flang/test_files/test_virtual_file"

module_baseline = VirtualFileRepresentation(
    name="test_virtual_file",
    content=[
        VirtualFileRepresentation(
            name="module",
            content=[
                VirtualFileRepresentation(
                    name="files",
                    content=[
                        VirtualFileRepresentation(
                            name="different.txt",
                            content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec sodales eu ex quis imperdiet. Pellentesque eget eros id nisi eleifend dignissim.",
                        ),
                        VirtualFileRepresentation(name="empty", content=[]),
                        VirtualFileRepresentation(name="empty_file.txt", content=""),
                    ],
                ),
                VirtualFileRepresentation(
                    name="other.txt",
                    content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec sodales eu ex quis imperdiet. Pellentesque eget eros id nisi eleifend dignissim.\ntest test 1111",
                ),
                VirtualFileRepresentation(
                    name="some_file.txt",
                    content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec sodales eu ex quis imperdiet. Pellentesque eget eros id nisi eleifend dignissim.\n\n\n\ntest test",
                ),
            ],
        )
    ],
)
test_vfr = VirtualFileRepresentation(
    name="some",
    content=[
        VirtualFileRepresentation(name="empty", content=[]),
        VirtualFileRepresentation(name="empty2", content=[]),
        VirtualFileRepresentation(name="text_file", content="lorem ipsum"),
        VirtualFileRepresentation(name="text_file2", content="lorem ipsum dolor amet"),
    ],
)


def are_directories_identical(dir1, dir2):
    comparison = filecmp.dircmp(dir1, dir2)

    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False

    if comparison.diff_files:
        return False

    for subdir in comparison.common_dirs:
        subdir1 = os.path.join(dir1, subdir)
        subdir2 = os.path.join(dir2, subdir)
        if not are_directories_identical(subdir1, subdir2):
            return False

    return True


class VirtualFileTestCase(unittest.TestCase):
    def test_create_virtual_file_from_real(self):
        fr = FileRepresentation(path=PATH_TO_MODULE)
        vfr = VirtualFileRepresentation.from_real(fr)

        self.assertEqual(vfr, module_baseline)

    def test_create_files_from_virtual_representation(self):
        diffs = test_vfr.diff()

        self.assertEqual(len(diffs), 5)
        self.assertTrue(all(diff.operation == FileOperation.CREATE for diff in diffs))

    def test_generate_files_in_virtual_representation(self):
        with tempfile.TemporaryDirectory() as tf:
            diffs = test_vfr.diff(root=tf)
            self.assertEqual(len(diffs), 5)
            self.assertTrue(all(diff.operation == FileOperation.CREATE for diff in diffs))

            diffs.apply_all()

            fr = FileRepresentation(tf).get_content()[0]
            generated_vfr = VirtualFileRepresentation.from_real(fr)

        self.assertEqual(generated_vfr, test_vfr)

    def test_delete_files_in_virtual_representation(self):
        vfr_copy: VirtualFileRepresentation = copy.deepcopy(test_vfr)

        with tempfile.TemporaryDirectory() as tf:
            diffs = vfr_copy.diff(root=tf)
            self.assertEqual(len(diffs), 5)
            self.assertTrue(all(diff.operation == FileOperation.CREATE for diff in diffs))

            diffs.apply_all()

            vfr_copy.content.pop(0)
            vfr_copy.content.pop(1)

            diffs = vfr_copy.diff(root=tf)
            self.assertEqual(len(diffs), 2)
            self.assertTrue(all(diff.operation == FileOperation.DELETE for diff in diffs))

            diffs.apply_all()
            fr = FileRepresentation(tf).get_content()[0]
            generated_vfr = VirtualFileRepresentation.from_real(fr)

        self.assertEqual(generated_vfr, vfr_copy)

    def test_modify_files_in_virtual_representation(self):
        vfr_copy: VirtualFileRepresentation = copy.deepcopy(test_vfr)

        with tempfile.TemporaryDirectory() as tf:
            diffs = vfr_copy.diff(root=tf)
            self.assertEqual(len(diffs), 5)
            self.assertTrue(all(diff.operation == FileOperation.CREATE for diff in diffs))

            diffs.apply_all()

            vfr_copy.content[3].content = f"{vfr_copy.content[3].content} NEW TEXT"
            new_text = vfr_copy.content[3].content

            diffs = vfr_copy.diff(root=tf)
            self.assertEqual(len(diffs), 1)
            self.assertTrue(all(diff.operation == FileOperation.MODIFY for diff in diffs))

            diffs.apply_all()
            fr = FileRepresentation(tf).get_content()[0]
            generated_vfr = VirtualFileRepresentation.from_real(fr)

            self.assertEqual(fr.get_content()[3].get_content(), new_text)

        self.assertEqual(generated_vfr, vfr_copy)
