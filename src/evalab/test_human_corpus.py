#!/usr/bin/env python3
"""The control corpus, rebuilt rather than redistributed.

Earlier rounds asserted a human baseline of 0.97 to 2.09 structural
flags per 1000 words with no way for a reader to rebuild the corpus it
came from. That is the same failure the p-values had before stats.py:
a number nobody can recompute is not evidence.
"""
import ast
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evalab import human_corpus


class StdlibDocstringTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def _module(self, name, docstring, subdir=""):
        target = os.path.join(self.dir, subdir)
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, name), "w") as f:
            f.write(f'"""{docstring}"""\nX = 1\n')

    def test_it_reads_docstrings_without_importing_anything(self):
        """Importing hundreds of stdlib modules to read their docstrings
        would run every one's module-level code."""
        with open(os.path.join(self.dir, "boom.py"), "w") as f:
            f.write('"""' + "word " * 40 + '"""\nraise SystemExit("ran")\n')
        found = human_corpus.stdlib_docstrings(self.dir)
        self.assertEqual(len(found), 1)

    def test_a_short_docstring_is_not_prose_worth_measuring(self):
        self._module("tiny.py", "Short.")
        self._module("real.py", "word " * 40)
        found = human_corpus.stdlib_docstrings(self.dir)
        self.assertEqual([label for label, _ in found], ["real.py"])

    def test_test_directories_are_excluded(self):
        """A stdlib test module's docstring is not documentation prose,
        and including it would quietly change the baseline."""
        self._module("real.py", "word " * 40)
        self._module("case.py", "word " * 40, subdir="test")
        found = human_corpus.stdlib_docstrings(self.dir)
        self.assertEqual([label for label, _ in found], ["real.py"])

    def test_an_unparseable_file_is_skipped_not_fatal(self):
        with open(os.path.join(self.dir, "broken.py"), "w") as f:
            f.write("def (:\n")
        self._module("real.py", "word " * 40)
        self.assertEqual(len(human_corpus.stdlib_docstrings(self.dir)), 1)

    def test_the_order_is_deterministic(self):
        """Two people on one Python version must build the same corpus,
        or the manifest hash means nothing."""
        for name in ("c.py", "a.py", "b.py"):
            self._module(name, "word " * 40)
        first = [label for label, _ in human_corpus.stdlib_docstrings(self.dir)]
        second = [label for label, _ in human_corpus.stdlib_docstrings(self.dir)]
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first))


class ManifestTests(unittest.TestCase):
    def test_it_names_every_source_and_its_size(self):
        """A corpus whose contents cannot be named is not a control."""
        info = human_corpus.manifest([("a", "one two three"), ("b", "four")])
        self.assertEqual(info["documents"], 2)
        self.assertEqual(info["words"], 4)
        self.assertEqual([s["source"] for s in info["sources"]], ["a", "b"])

    def test_the_same_corpus_hashes_the_same(self):
        entries = [("a", "one two"), ("b", "three")]
        self.assertEqual(human_corpus.manifest(entries)["sha256"],
                          human_corpus.manifest(entries)["sha256"])

    def test_changed_text_changes_the_hash(self):
        a = human_corpus.manifest([("a", "one two")])["sha256"]
        b = human_corpus.manifest([("a", "one three")])["sha256"]
        self.assertNotEqual(a, b)

    def test_the_same_text_under_a_different_source_hashes_differently(self):
        """Provenance is part of what a control corpus IS. Two corpora
        with identical bytes from different files are not the same
        evidence."""
        a = human_corpus.manifest([("stdlib/a.py", "one two")])["sha256"]
        b = human_corpus.manifest([("packages/a.md", "one two")])["sha256"]
        self.assertNotEqual(a, b)


class WriteTests(unittest.TestCase):
    def test_each_source_lands_in_its_own_measurable_file(self):
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out)
        written = human_corpus.write_corpus(
            [("stdlib/json/__init__.py", "one two"), ("stdlib/os.py", "three")],
            out)
        self.assertEqual(len(written), 2)
        for path in written:
            self.assertTrue(os.path.exists(path))
            self.assertTrue(path.endswith(".md"))

    def test_a_nested_source_name_does_not_escape_the_output_directory(self):
        out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, out)
        written = human_corpus.write_corpus(
            [("stdlib/email/mime/text.py", "one two")], out)
        self.assertEqual(os.path.dirname(written[0]), out)


if __name__ == "__main__":
    unittest.main()
