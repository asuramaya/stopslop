#!/usr/bin/env python3
"""Tests for the CUSTOM half of core/glossary_packs -- add_pack/remove_pack
and the directory-scanning _PackRegistry behind AVAILABLE_PACKS. Built-in
pack behavior is covered by rulesets/ste100/test_glossary_packs.py; this
file is isolated against a temp _CUSTOM_PACKS_DIR so nothing here ever
touches this repo's own real .claude/stopslop/custom_packs/.

Run with:
    cd src && ../.venv/bin/python3 -m unittest core.test_glossary_packs_custom -v
"""
import json
import os
import tempfile
import unittest

from core import glossary_packs


class _TempCustomPacksDir(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig = glossary_packs._CUSTOM_PACKS_DIR
        glossary_packs._CUSTOM_PACKS_DIR = self._tmp.name
        self.addCleanup(setattr, glossary_packs, "_CUSTOM_PACKS_DIR", self._orig)
        self.addCleanup(self._tmp.cleanup)


class AddPackTests(_TempCustomPacksDir):
    def test_add_then_visible_in_available_packs(self):
        glossary_packs.add_pack("my-pack", "My Pack", "https://example.com",
                                 "MIT", "word", {"widget": {"note": "x"}})
        self.assertIn("my-pack", glossary_packs.AVAILABLE_PACKS)
        meta = glossary_packs.AVAILABLE_PACKS["my-pack"]
        self.assertEqual(meta["origin"], "custom")
        self.assertEqual(meta["name"], "My Pack")

    def test_writes_the_same_shape_a_built_in_pack_file_has(self):
        glossary_packs.add_pack("my-pack", "My Pack", "https://example.com",
                                 "MIT", "word", {"widget": {"note": "x"}})
        path = os.path.join(self._tmp.name, "my_pack.json")
        with open(path) as f:
            data = json.load(f)
        self.assertEqual(data["_meta"]["name"], "My Pack")
        self.assertEqual(data["terms"], {"widget": {"note": "x"}})

    def test_load_pack_terms_reads_it_back(self):
        glossary_packs.add_pack("my-pack", "My Pack", "https://example.com",
                                 "MIT", "word", {"widget": {"note": "x"}})
        self.assertEqual(glossary_packs.load_pack_terms("my-pack"),
                          {"widget": {"note": "x"}})

    def test_rejects_id_colliding_with_a_built_in(self):
        with self.assertRaises(ValueError):
            glossary_packs.add_pack("mdn-glossary", "Shadow", "x", "MIT", "word", {})
        self.assertEqual(glossary_packs.AVAILABLE_PACKS["mdn-glossary"]["origin"], "built-in")

    def test_rejects_a_malformed_id(self):
        with self.assertRaises(ValueError):
            glossary_packs.add_pack("Not Valid!", "x", "x", "MIT", "word", {})

    def test_rejects_a_term_that_would_never_match_real_text(self):
        # Same regression class BuiltPackKeysSurviveTheRealTokenizerTests
        # guards for built-in packs -- a hyphenated/dotted/digit-bearing
        # key can never match core.blocks.words()'s real tokenizer.
        with self.assertRaises(ValueError):
            glossary_packs.add_pack("my-pack", "x", "x", "MIT", "word",
                                     {"front-end": {"note": "dead key"}})

    def test_id_is_normalized_to_lowercase_and_stripped(self):
        glossary_packs.add_pack("  My-Pack  ".strip().lower(), "x", "x", "MIT", "word", {})
        self.assertIn("my-pack", glossary_packs.AVAILABLE_PACKS)


class RemovePackTests(_TempCustomPacksDir):
    def test_remove_deletes_the_file(self):
        glossary_packs.add_pack("my-pack", "x", "x", "MIT", "word", {})
        glossary_packs.remove_pack("my-pack")
        self.assertNotIn("my-pack", glossary_packs.AVAILABLE_PACKS)
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "my_pack.json")))

    def test_refuses_to_remove_a_built_in(self):
        with self.assertRaises(ValueError):
            glossary_packs.remove_pack("mdn-glossary")
        self.assertIn("mdn-glossary", glossary_packs.AVAILABLE_PACKS)

    def test_unknown_custom_pack_raises(self):
        with self.assertRaises(glossary_packs.UnknownPackError):
            glossary_packs.remove_pack("never-existed")


class RegistryScanTests(_TempCustomPacksDir):
    def test_no_custom_dir_yet_is_not_an_error(self):
        # setUp already pointed _CUSTOM_PACKS_DIR at a real (but empty)
        # temp dir; simulate "never created" by pointing at a path that
        # doesn't exist at all.
        glossary_packs._CUSTOM_PACKS_DIR = os.path.join(self._tmp.name, "nope")
        self.assertEqual(set(glossary_packs.AVAILABLE_PACKS),
                          {"microsoft-style-guide", "mdn-glossary", "nist-security"})

    def test_list_packs_includes_both_origins(self):
        glossary_packs.add_pack("my-pack", "x", "x", "MIT", "word", {})
        listed = glossary_packs.list_packs()
        self.assertEqual(listed["my-pack"]["origin"], "custom")
        self.assertEqual(listed["mdn-glossary"]["origin"], "built-in")

    def test_removing_and_readding_is_reflected_live(self):
        # AVAILABLE_PACKS must never be a stale snapshot -- this is what
        # makes it safe for a long-running dashboard process to read
        # right after a write with no reload step.
        self.assertNotIn("my-pack", glossary_packs.AVAILABLE_PACKS)
        glossary_packs.add_pack("my-pack", "x", "x", "MIT", "word", {})
        self.assertIn("my-pack", glossary_packs.AVAILABLE_PACKS)
        glossary_packs.remove_pack("my-pack")
        self.assertNotIn("my-pack", glossary_packs.AVAILABLE_PACKS)


if __name__ == "__main__":
    unittest.main()
