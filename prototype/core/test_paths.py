#!/usr/bin/env python3
"""Tests for core/paths.py's project-root discovery."""
import os
import unittest

from core import paths


class FindProjectRootTests(unittest.TestCase):
    def test_finds_root_from_prototype_top_level(self):
        fake_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "pretool_hook.py")
        root = paths.find_project_root(fake_file)
        self.assertTrue(os.path.exists(os.path.join(root, "stopslop.py")))

    def test_finds_root_from_nested_ruleset_package(self):
        fake_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "rulesets", "ste100", "lint.py")
        root = paths.find_project_root(fake_file)
        self.assertTrue(os.path.exists(os.path.join(root, "stopslop.py")))

    def test_result_is_consistent_regardless_of_starting_depth(self):
        here = os.path.dirname(os.path.abspath(__file__))
        top_level = paths.find_project_root(os.path.join(here, "..", "pretool_hook.py"))
        nested = paths.find_project_root(os.path.join(here, "..", "rulesets", "ste100", "lint.py"))
        self.assertEqual(top_level, nested)

    def test_raises_if_no_marker_found(self):
        with self.assertRaises(RuntimeError):
            paths.find_project_root("/tmp/definitely/not/a/project/file.py")


if __name__ == "__main__":
    unittest.main()
