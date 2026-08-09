#!/usr/bin/env python3
"""Tests for core/text.py's n() -- the shared pluralization helper.

The bug this guards: every count-reporting message in this project used
to hand-roll its own "{n} word(s)" -- eighteen sites in configure.py
alone, plus the hook's own deny message, the CLI, status reports. A
one-word list read "1 words". This project polices exactly that tell in
someone else's prose; its own messages don't get to keep it.
"""
import unittest

from core.text import n


class NTests(unittest.TestCase):

    def test_singular(self):
        self.assertEqual(n(1, "word"), "1 word")

    def test_plural(self):
        self.assertEqual(n(2, "word"), "2 words")

    def test_zero_is_plural(self):
        self.assertEqual(n(0, "word"), "0 words")

    def test_irregular_plural_override(self):
        self.assertEqual(n(3, "fix", plural="fixes"), "3 fixes")

    def test_irregular_plural_not_applied_to_singular(self):
        self.assertEqual(n(1, "fix", plural="fixes"), "1 fix")

    def test_multi_word_noun(self):
        self.assertEqual(n(2, "blocking flag"), "2 blocking flags")
        self.assertEqual(n(1, "blocking flag"), "1 blocking flag")


if __name__ == "__main__":
    unittest.main()
