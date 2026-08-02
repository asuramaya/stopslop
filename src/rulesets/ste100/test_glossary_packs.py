#!/usr/bin/env python3
"""Tests for the vocabulary-pack registry (glossary_packs/__init__.py) and
for the manual/merged split in lint.py and glossary.py that packs made
necessary: check_vocabulary() must see manual terms AND every enabled
pack's terms, but register()/unregister()/list_terms() must only ever
touch the manual layer -- see lint._load_manual_terms's own docstring for
why a pack's content must never round-trip into project-terms.json.

Run with:
    cd src && python3 -m unittest rulesets.ste100.test_glossary_packs -v
"""
import json
import os
import tempfile
import unittest

import rulesets
from core.blocks import words
from rulesets.ste100 import glossary_packs, lint, glossary
from rulesets import ste100


class BuiltPackKeysSurviveTheRealTokenizerTests(unittest.TestCase):
    """Regression guard: the first version of every pack's build script
    allowed hyphenated, dotted, and digit-bearing headwords (e.g.
    "front-end", "node.js", "base64"). core/blocks.py's real tokenizer
    (words() = re.findall(r"[A-Za-z']+", ...)) matches letters and
    apostrophes only, so any of those, stored as a pack key, could never
    actually match anything check_vocabulary() looks up -- confirmed
    live, 70 silently-inert entries shipped before this was caught.
    Every currently-built pack must have zero such entries; a future
    pack (or a re-run of an existing build script) that regresses this
    fails here, not silently in production."""

    def test_every_built_pack_has_zero_dead_keys(self):
        for pack_id in glossary_packs.AVAILABLE_PACKS:
            terms = glossary_packs.load_pack_terms(pack_id)
            dead = [w for w in terms if words(w) != [w]]
            self.assertEqual(dead, [], f"{pack_id} has dead (unmatchable) keys: {dead}")


class GlossaryPacksRegistryTests(unittest.TestCase):
    def test_unknown_pack_id_raises(self):
        with self.assertRaises(glossary_packs.UnknownPackError):
            glossary_packs.load_pack_terms("__not_a_real_pack__")

    def test_known_pack_with_no_built_file_returns_empty(self):
        # Every pack in AVAILABLE_PACKS is a real, known id even before
        # its data file has been generated -- an unbuilt pack is a no-op,
        # not an error, so enabling it early never breaks the gate.
        with tempfile.TemporaryDirectory() as tmp:
            original = glossary_packs._PACKS_DIR
            glossary_packs._PACKS_DIR = tmp
            try:
                self.assertEqual(glossary_packs.load_pack_terms("microsoft-style-guide"), {})
            finally:
                glossary_packs._PACKS_DIR = original

    def test_pack_meta_includes_term_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = glossary_packs._PACKS_DIR
            glossary_packs._PACKS_DIR = tmp
            try:
                path = os.path.join(tmp, "microsoft_style_guide.json")
                with open(path, "w") as f:
                    json.dump({"_meta": {"extracted": "2026-01-01"},
                               "terms": {"webhook": {"note": "x"}, "endpoint": {"note": "y"}}}, f)
                meta = glossary_packs.pack_meta("microsoft-style-guide")
                self.assertEqual(meta["term_count"], 2)
                self.assertEqual(meta["extracted"], "2026-01-01")
                self.assertEqual(meta["license"], "CC-BY-4.0")
            finally:
                glossary_packs._PACKS_DIR = original

    def test_list_packs_covers_every_available_pack(self):
        listed = glossary_packs.list_packs()
        self.assertEqual(set(listed), set(glossary_packs.AVAILABLE_PACKS))


class ManualVsMergedTermsTests(unittest.TestCase):
    """lint._load_manual_terms() and lint._load_project_terms() must stay
    genuinely different views -- the first is what register()/unregister()/
    list_terms() operate on, the second is what check_vocabulary() checks
    against. Collapsing them back into one was the actual bug this pack
    feature could have introduced (see PR/commit notes)."""

    def setUp(self):
        self._orig_path = lint.PROJECT_TERMS_PATH
        self._orig_enabled = _CoreConfigPatch.enabled_glossary_packs
        self._tmp = tempfile.TemporaryDirectory()
        lint.PROJECT_TERMS_PATH = os.path.join(self._tmp.name, "project-terms.json")
        with open(lint.PROJECT_TERMS_PATH, "w") as f:
            json.dump({"manualword": {"note": "hand-registered"}}, f)

    def tearDown(self):
        lint.PROJECT_TERMS_PATH = self._orig_path
        lint._core_config.enabled_glossary_packs = self._orig_enabled
        self._tmp.cleanup()

    def _enable_fake_pack(self, terms):
        lint._core_config.enabled_glossary_packs = lambda *a, **k: ["microsoft-style-guide"]
        self._orig_load = glossary_packs.load_pack_terms
        glossary_packs.load_pack_terms = lambda pack_id: terms
        self.addCleanup(lambda: setattr(glossary_packs, "load_pack_terms", self._orig_load))

    def test_manual_terms_excludes_pack_content(self):
        self._enable_fake_pack({"packword": {"note": "from a pack"}})
        self.assertEqual(lint._load_manual_terms(), {"manualword": {"note": "hand-registered"}})

    def test_merged_terms_includes_both(self):
        self._enable_fake_pack({"packword": {"note": "from a pack"}})
        merged = lint._load_project_terms()
        self.assertIn("manualword", merged)
        self.assertIn("packword", merged)

    def test_manual_registration_wins_on_conflict_with_a_pack(self):
        self._enable_fake_pack({"manualword": {"note": "pack's own definition"}})
        merged = lint._load_project_terms()
        self.assertEqual(merged["manualword"]["note"], "hand-registered")

    def test_pack_resolution_failure_never_breaks_the_merge(self):
        lint._core_config.enabled_glossary_packs = lambda *a, **k: (_ for _ in ()).throw(OSError("boom"))
        merged = lint._load_project_terms()
        self.assertEqual(merged, {"manualword": {"note": "hand-registered"}})


class _CoreConfigPatch:
    """Snapshot of the function ManualVsMergedTermsTests patches, read once
    at class-definition time so setUp/tearDown can restore it exactly."""
    enabled_glossary_packs = lint._core_config.enabled_glossary_packs


class RegisterUnregisterNeverTouchPackContentTests(unittest.TestCase):
    """The regression this whole file exists to guard: register()/
    unregister() used to load lint._load_project_terms() (post-pack-
    feature, the MERGED view), mutate it, and write the WHOLE THING back
    to project-terms.json -- meaning the first registration after enabling
    any pack would have silently copied every one of that pack's terms
    into the manual glossary file. Confirmed live during development;
    these tests keep it from coming back."""

    def setUp(self):
        self._orig_path = lint.PROJECT_TERMS_PATH
        self._tmp = tempfile.TemporaryDirectory()
        lint.PROJECT_TERMS_PATH = os.path.join(self._tmp.name, "project-terms.json")
        with open(lint.PROJECT_TERMS_PATH, "w") as f:
            json.dump({}, f)
        lint.PROJECT_TERMS = lint._load_project_terms()
        self._orig_load = glossary_packs.load_pack_terms
        glossary_packs.load_pack_terms = lambda pack_id: {
            f"packword{i}": {"note": "x"} for i in range(50)}
        lint._core_config.enabled_glossary_packs = lambda *a, **k: ["microsoft-style-guide"]

    def tearDown(self):
        lint.PROJECT_TERMS_PATH = self._orig_path
        glossary_packs.load_pack_terms = self._orig_load
        lint._core_config.enabled_glossary_packs = _CoreConfigPatch.enabled_glossary_packs
        lint.PROJECT_TERMS = lint._load_project_terms()
        self._tmp.cleanup()

    def test_register_does_not_leak_pack_terms_onto_disk(self):
        glossary.register("newword", "a real registration")
        with open(lint.PROJECT_TERMS_PATH) as f:
            on_disk = json.load(f)
        self.assertEqual(set(on_disk), {"newword"})

    def test_list_terms_never_includes_pack_content(self):
        glossary.register("newword", "a real registration")
        self.assertEqual(set(glossary.list_terms()), {"newword"})

    def test_unregister_does_not_leak_pack_terms_onto_disk(self):
        glossary.register("newword", "a real registration")
        glossary.unregister("newword")
        with open(lint.PROJECT_TERMS_PATH) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk, {})


class PackEnableDisableTests(unittest.TestCase):
    """list_glossary_packs()/set_enabled_glossary_packs() on the ste100
    contract surface -- isolated against a temp project root so this
    never touches the real repo's own stopslop.config.json."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = ste100.paths.find_project_root
        ste100.paths.find_project_root = lambda _file: self._tmp.name

    def tearDown(self):
        ste100.paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_no_packs_enabled_by_default(self):
        packs = ste100.list_glossary_packs()
        self.assertTrue(all(not meta["enabled"] for meta in packs.values()))

    def test_unknown_pack_id_raises_and_does_not_write(self):
        with self.assertRaises(glossary_packs.UnknownPackError):
            ste100.set_enabled_glossary_packs(["__not_a_real_pack__"])
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_enabling_a_pack_is_reflected_in_list_glossary_packs(self):
        ste100.set_enabled_glossary_packs(["microsoft-style-guide"])
        packs = ste100.list_glossary_packs()
        self.assertTrue(packs["microsoft-style-guide"]["enabled"])
        self.assertFalse(packs["mdn-glossary"]["enabled"])


if __name__ == "__main__":
    unittest.main()
