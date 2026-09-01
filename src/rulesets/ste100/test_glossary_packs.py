#!/usr/bin/env python3
"""Tests for the vocabulary-pack registry (core/glossary_packs/__init__.py
-- ruleset-agnostic, but exercised here against its one real consumer) and
for the layer split in lint.py and glossary.py that packs made necessary:
the checks must see manual terms AND every applicable pack's terms, but
register()/unregister()/list_terms() must only ever touch the project
layer -- see lint._load_manual_terms's own docstring for why a pack's
content must never round-trip into the manual glossary.

Also covers the two guarantees core/terms.py added, both of which fail
SILENTLY when broken (the gate keeps running and keeps reporting clean):
packs follow the PATH rather than the ruleset, and a pack may never
introduce a word the real ASD-STE100 dictionary forbids.

Run with:
    cd src && python3 -m unittest rulesets.ste100.test_glossary_packs -v
"""
import json
import os
import tempfile
import unittest

import rulesets
from core import config as core_config, glossary_packs, terms as core_terms
from core.blocks import words
from rulesets.ste100 import lint, glossary
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


class PackIsInertContentTests(unittest.TestCase):
    """A pack names its SOURCE and nothing else.

    Every entry used to carry target=("ste100", "project_terms"). That was
    the same ancestry these files were moved out of ste100's directory to
    escape, surviving one level up -- the MDN Web Docs glossary is not
    ASD-STE100 content, it is vocabulary ste100 happens to read as an allow
    list. Naming the consumer inside the pack pointed the coupling the
    wrong way and made three reasonable things impossible; see the module
    docstring in core/glossary_packs/__init__.py."""

    def test_no_pack_names_a_ruleset_or_a_list(self):
        for pack_id, meta in glossary_packs.AVAILABLE_PACKS.items():
            self.assertNotIn("target", meta,
                              f"{pack_id} still names its own consumer")
            for ruleset_id in ("ste100", "slopwatch", "codewatch"):
                self.assertNotIn(ruleset_id, json.dumps(meta),
                                  f"{pack_id} metadata mentions {ruleset_id}")

    def test_pack_metadata_is_only_facts_about_the_pack_itself(self):
        """The line is SELF-DESCRIPTION vs NAMING A CONSUMER, not field
        count. This assertion originally pinned the exact three source
        fields -- the right guard at the time, in the wrong shape. It fired
        when `content_kind` was added, and content_kind is the opposite of
        the thing being guarded against: "I am a bag of single words" is a
        fact about the pack, true whoever reads it, where "I am for
        ste100.project_terms" was a claim about someone else. A pack may say
        what it IS. It may never say who it is FOR."""
        # "origin" (built-in vs custom) joined the same way content_kind
        # did: it is a fact about the pack's own provenance, never about
        # who reads it -- see _PackRegistry in core/glossary_packs.
        allowed = {"name", "source", "license", "content_kind", "origin"}
        for pack_id, meta in glossary_packs.AVAILABLE_PACKS.items():
            extra = set(meta) - allowed
            self.assertEqual(extra, set(),
                              f"{pack_id} carries {sorted(extra)}. Add a field "
                              f"here only if it describes the PACK; anything "
                              f"naming a reader belongs on the routing rule.")

    def test_content_kind_describes_the_pack_and_names_no_reader(self):
        for pack_id, meta in glossary_packs.AVAILABLE_PACKS.items():
            with self.subTest(pack=pack_id):
                self.assertIn("content_kind", meta,
                               "without a kind, this pack can be bound to a "
                               "list that cannot read its content")
                # A kind is a property of the words themselves. If one ever
                # reads like a list id or a ruleset id, the coupling that
                # `target` used to carry has crept back in a new spelling.
                self.assertNotIn(".", meta["content_kind"])
                self.assertNotIn("_", meta["content_kind"])

    def test_the_registry_offers_every_pack_to_every_list(self):
        # There is no packs_for_list() filter any more: which packs may
        # feed a list is a project decision in config, not a property of
        # the pack. The registry just reports what exists.
        self.assertFalse(hasattr(glossary_packs, "packs_for_list"))
        self.assertEqual(set(glossary_packs.list_packs()),
                          set(glossary_packs.AVAILABLE_PACKS))


class PackAdmissibilityTests(unittest.TestCase):
    """The invariant that used to be a property of how three build scripts
    happened to be written, not of the model.

    All three shipped packs collide with the forbidden list zero times --
    because each build_glossary_pack_*.py hand-excludes words the real
    dictionary already covers. Nothing enforced it. A fourth pack from
    anywhere else containing "utilize" would have silently un-forbidden a
    word the standard explicitly replaces."""

    def test_shipped_packs_still_collide_with_nothing_forbidden(self):
        for pack_id in glossary_packs.AVAILABLE_PACKS:
            collisions = [t for t in glossary_packs.load_pack_terms(pack_id)
                           if not lint._pack_admissible(t)]
            self.assertEqual(collisions, [], f"{pack_id} would override: {collisions}")

    def test_guard_refuses_a_forbidden_word_from_a_pack(self):
        forbidden = next(iter(lint.UNAPPROVED_MAP))
        self.assertFalse(lint._pack_admissible(forbidden))

    def test_guard_refuses_a_modal_from_a_pack(self):
        self.assertFalse(lint._pack_admissible("should"))

    def test_guard_allows_an_ordinary_uncovered_word(self):
        self.assertTrue(lint._pack_admissible("kubernetes"))

    def test_a_hostile_pack_cannot_unforbid_a_word_end_to_end(self):
        forbidden = next(iter(lint.UNAPPROVED_MAP))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "stopslop.config.json")
            with open(path, "w") as f:
                json.dump({"rulesets": [{"glob": "*.md", "ruleset": "ste100",
                                          "packs": {"project_terms": ["nist-security"]}}]}, f)
            orig = glossary_packs.load_pack_terms
            glossary_packs.load_pack_terms = lambda pack_id: {forbidden: {"note": "hostile"}}
            try:
                layers = core_terms.resolve(
                    lint.TERM_LISTS["project_terms"], tmp, "ste100", "project_terms",
                    file_path=os.path.join(tmp, "a.md"), config_file=path)
            finally:
                glossary_packs.load_pack_terms = orig
            self.assertNotIn(forbidden, layers["effective"])
            self.assertEqual(layers["rejected"][forbidden], "nist-security")


class _TempProjectRoot(unittest.TestCase):
    """Shared isolation: a fake project root plus a real config file, so
    nothing here can touch the repo's own stopslop.config.json. Patching
    lint._paths.find_project_root covers ste100/__init__.py too -- both
    reference the same module object in sys.modules."""

    def setUp(self):
        self._orig_find_root = lint._paths.find_project_root
        self._orig_terms = dict(lint.PROJECT_TERMS)
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        lint._paths.find_project_root = lambda _file: self._tmp.name
        core_terms._migration_checked.clear()

    def tearDown(self):
        lint._paths.find_project_root = self._orig_find_root
        lint.PROJECT_TERMS = self._orig_terms
        core_terms._migration_checked.clear()
        self._tmp.cleanup()

    def _config_path(self):
        return os.path.join(self._tmp.name, "stopslop.config.json")

    def _write_rules(self, rules):
        # Merge, never clobber: the same config file also holds the terms
        # this fixture may already have registered.
        data = {}
        if os.path.exists(self._config_path()):
            with open(self._config_path()) as f:
                data = json.load(f)
        data["rulesets"] = rules
        with open(self._config_path(), "w") as f:
            json.dump(data, f)

    def _on_disk(self):
        return core_terms.project_terms(self._tmp.name, "ste100", "project_terms")

    def _fake_pack(self, terms):
        orig = glossary_packs.load_pack_terms
        glossary_packs.load_pack_terms = lambda pack_id: terms
        self.addCleanup(lambda: setattr(glossary_packs, "load_pack_terms", orig))


class ManualVsEffectiveTermsTests(_TempProjectRoot):
    """lint._load_manual_terms() and lint.effective_project_terms() must
    stay genuinely different views -- the first is what register()/
    unregister()/list_terms() operate on, the second is what the checks run
    against. Collapsing them back into one is the bug this pack feature
    could introduce."""

    def setUp(self):
        super().setUp()
        core_terms.save_project_terms(
            self._tmp.name, "ste100", "project_terms",
            {"manualword": {"note": "hand-registered"}})
        self._write_rules([{"glob": "*.md", "ruleset": "ste100",
                             "packs": {"project_terms": ["microsoft-style-guide"]}}])

    def test_manual_terms_excludes_pack_content(self):
        self._fake_pack({"packword": {"note": "from a pack"}})
        self.assertEqual(lint._load_manual_terms(),
                          {"manualword": {"note": "hand-registered"}})

    def test_effective_terms_includes_both(self):
        self._fake_pack({"packword": {"note": "from a pack"}})
        merged = lint.effective_project_terms(os.path.join(self._tmp.name, "a.md"))
        self.assertIn("manualword", merged)
        self.assertIn("packword", merged)

    def test_manual_registration_wins_on_conflict_with_a_pack(self):
        self._fake_pack({"manualword": {"note": "pack's own definition"}})
        merged = lint.effective_project_terms(os.path.join(self._tmp.name, "a.md"))
        self.assertEqual(merged["manualword"]["note"], "hand-registered")

    def test_pack_resolution_failure_never_breaks_the_merge(self):
        orig = glossary_packs.load_pack_terms

        def boom(pack_id):
            raise OSError("boom")
        glossary_packs.load_pack_terms = boom
        self.addCleanup(lambda: setattr(glossary_packs, "load_pack_terms", orig))
        merged = lint.effective_project_terms(os.path.join(self._tmp.name, "a.md"))
        self.assertEqual(merged, {"manualword": {"note": "hand-registered"}})

    def test_module_global_holds_the_manual_layer_only(self):
        # PROJECT_TERMS can no longer include packs: pack content depends on
        # which file is being written, so there is no correct import-time
        # answer. The strictest sensible default is the manual layer.
        self._fake_pack({"packword": {"note": "from a pack"}})
        self.assertNotIn("packword", lint._load_manual_terms())


class PacksFollowThePathTests(_TempProjectRoot):
    """The reshape this refactor exists for: two paths, one ruleset, two
    different effective glossaries."""

    def setUp(self):
        super().setUp()
        self._write_rules([
            {"glob": "docs/*.md", "ruleset": "ste100",
             "packs": {"project_terms": ["nist-security"]}},
            {"glob": "*.md", "ruleset": "ste100"},
        ])
        self._fake_pack({"kubernetes": {"note": "from the security pack"}})

    def test_pack_word_is_allowed_on_the_glob_that_enables_the_pack(self):
        merged = lint.effective_project_terms(os.path.join(self._tmp.name, "docs/a.md"))
        self.assertIn("kubernetes", merged)

    def test_same_word_is_not_allowed_on_a_path_with_no_pack(self):
        merged = lint.effective_project_terms(os.path.join(self._tmp.name, "a.md"))
        self.assertNotIn("kubernetes", merged)

    def test_lint_and_gate_honours_the_path(self):
        text = "The kubernetes cluster is ready."
        flagged_here = [v["word"].lower()
                         for f in lint.lint_and_gate(
                             text, file_path=os.path.join(self._tmp.name, "a.md")
                         )["semantic_flags"] for v in [f.get("detail", {})]
                         if isinstance(v, dict) and v.get("word")]
        in_docs = lint.lint_and_gate(
            text, file_path=os.path.join(self._tmp.name, "docs/a.md"))
        docs_words = [v["word"].lower()
                       for f in in_docs["semantic_flags"] for v in [f.get("detail", {})]
                       if isinstance(v, dict) and v.get("word")]
        self.assertIn("kubernetes", flagged_here)
        self.assertNotIn("kubernetes", docs_words)


class RegisterUnregisterNeverTouchPackContentTests(_TempProjectRoot):
    """The regression this file exists to guard: register()/unregister()
    used to load the MERGED view, mutate it, and write the whole thing
    back -- so the first registration after enabling any pack silently
    copied every one of that pack's terms into the manual glossary.
    Confirmed live during development."""

    def setUp(self):
        super().setUp()
        self._write_rules([{"glob": "*.md", "ruleset": "ste100",
                             "packs": {"project_terms": ["microsoft-style-guide"]}}])
        self._fake_pack({f"packword{i}": {"note": "x"} for i in range(50)})

    def test_register_does_not_leak_pack_terms_onto_disk(self):
        glossary.register("newword", "a real registration")
        self.assertEqual(set(self._on_disk()), {"newword"})

    def test_list_terms_never_includes_pack_content(self):
        glossary.register("newword", "a real registration")
        self.assertEqual(set(glossary.list_terms()), {"newword"})

    def test_unregister_does_not_leak_pack_terms_onto_disk(self):
        glossary.register("newword", "a real registration")
        glossary.unregister("newword")
        self.assertEqual(self._on_disk(), {})


class RegisterValidationTests(_TempProjectRoot):
    """ste100's validator -- the one real difference between its term list
    and slopwatch's, now a callback on the shared primitive rather than a
    parallel API."""

    def test_word_already_in_the_standard_is_a_no_op(self):
        approved = next(iter(lint.APPROVED_WORDS))
        r = glossary.register(approved)
        self.assertEqual(r["status"], "no-op")
        self.assertEqual(self._on_disk(), {})

    def test_forbidden_word_is_refused_without_an_override(self):
        forbidden = next(iter(lint.UNAPPROVED_MAP))
        r = glossary.register(forbidden)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "refused")
        self.assertEqual(self._on_disk(), {})

    def test_forbidden_word_registers_with_an_explicit_reason(self):
        forbidden = next(iter(lint.UNAPPROVED_MAP))
        r = glossary.register(forbidden, override_unapproved="domain term of art here")
        self.assertTrue(r["ok"])
        self.assertTrue(self._on_disk()[forbidden]["overrides_unapproved"])
        self.assertEqual(self._on_disk()[forbidden]["note"], "domain term of art here")

    def test_multi_word_input_is_refused(self):
        r = glossary.register("two words")
        self.assertFalse(r["ok"])

    def test_uniform_add_term_reaches_the_same_validation(self):
        forbidden = next(iter(lint.UNAPPROVED_MAP))
        r = ste100.add_term("project_terms", forbidden)
        self.assertEqual(r["status"], "refused")

    def test_uniform_add_term_rejects_an_unknown_list(self):
        with self.assertRaises(core_terms.UnknownTermListError):
            ste100.add_term("__not_real__", "x")


class MigrateLegacyProjectTermsTests(_TempProjectRoot):
    """_migrate_legacy_project_terms() -- the one-time move of the
    pre-pluggable-ruleset project-terms.json (this project's own real copy
    held 69 hand-registered terms, migrated live during this session's
    refactor and verified byte-identical against a backup) into
    stopslop.config.json. Isolated against a temp project root AND a fake
    legacy-file path, so this never touches the real repo's files."""

    def setUp(self):
        super().setUp()
        self._orig_legacy_path = lint._LEGACY_PROJECT_TERMS_PATH
        lint._LEGACY_PROJECT_TERMS_PATH = os.path.join(
            self._tmp.name, "legacy-project-terms.json")

    def tearDown(self):
        lint._LEGACY_PROJECT_TERMS_PATH = self._orig_legacy_path
        super().tearDown()

    def _write_legacy(self, terms):
        with open(lint._LEGACY_PROJECT_TERMS_PATH, "w") as f:
            json.dump(terms, f)

    def test_no_legacy_file_is_a_no_op(self):
        lint._migrate_legacy_project_terms(self._tmp.name)  # must not raise
        self.assertEqual(self._on_disk(), {})

    def test_legacy_content_migrates_byte_for_byte(self):
        legacy = {"api": {"note": "software term", "overrides_unapproved": False},
                   "cli": {"note": "another one", "overrides_unapproved": True}}
        self._write_legacy(legacy)
        lint._migrate_legacy_project_terms(self._tmp.name)
        self.assertEqual(self._on_disk(), legacy)

    def test_legacy_file_removed_after_successful_migration(self):
        self._write_legacy({"api": {"note": "x", "overrides_unapproved": False}})
        lint._migrate_legacy_project_terms(self._tmp.name)
        self.assertFalse(os.path.exists(lint._LEGACY_PROJECT_TERMS_PATH))

    def test_does_not_overwrite_already_migrated_terms(self):
        core_terms.save_project_terms(self._tmp.name, "ste100", "project_terms",
                                       {"current": {"note": "the real one"}})
        self._write_legacy({"stale": {"note": "should never appear"}})
        lint._migrate_legacy_project_terms(self._tmp.name)
        self.assertEqual(self._on_disk(), {"current": {"note": "the real one"}})
        # Untouched: an already-migrated project should never lose its
        # legacy file silently, in case something still expects to find it.
        self.assertTrue(os.path.exists(lint._LEGACY_PROJECT_TERMS_PATH))

    def test_malformed_legacy_json_is_a_safe_no_op(self):
        with open(lint._LEGACY_PROJECT_TERMS_PATH, "w") as f:
            f.write("{not valid json")
        lint._migrate_legacy_project_terms(self._tmp.name)  # must not raise
        self.assertEqual(self._on_disk(), {})

    def test_empty_legacy_file_is_a_no_op(self):
        self._write_legacy({})
        lint._migrate_legacy_project_terms(self._tmp.name)
        self.assertEqual(self._on_disk(), {})

    def test_load_manual_terms_triggers_migration_end_to_end(self):
        self._write_legacy({"api": {"note": "x", "overrides_unapproved": False}})
        self.assertEqual(lint._load_manual_terms(),
                          {"api": {"note": "x", "overrides_unapproved": False}})
        self.assertFalse(os.path.exists(lint._LEGACY_PROJECT_TERMS_PATH))


class PackEnableDisableTests(_TempProjectRoot):
    """Packs are enabled on a path GLOB now, via core.config -- there is no
    ruleset method for it, because a pack was never a ruleset-scoped
    thing. list_glossary_packs()/set_enabled_glossary_packs() on ste100 are
    gone, not moved."""

    def test_no_packs_enabled_by_default(self):
        self._write_rules([{"glob": "*.md", "ruleset": "ste100"}])
        self.assertEqual(
            core_config.packs_for_path(self._tmp.name,
                                        os.path.join(self._tmp.name, "a.md"),
                                        list_id="project_terms",
                                        config_file=self._config_path()),
            [])

    def test_unknown_pack_id_is_rejected(self):
        self._write_rules([{"glob": "*.md", "ruleset": "ste100"}])
        with self.assertRaises(ValueError):
            core_config.set_rule_packs(
                self._tmp.name, "*.md", "project_terms", ["__not_a_real_pack__"],
                known_packs=glossary_packs.AVAILABLE_PACKS,
                config_file=self._config_path())

    def test_enabling_a_pack_is_reflected_per_path_and_list(self):
        self._write_rules([{"glob": "*.md", "ruleset": "ste100"}])
        core_config.set_rule_packs(self._tmp.name, "*.md", "project_terms",
                                    ["microsoft-style-guide"],
                                    known_packs=glossary_packs.AVAILABLE_PACKS,
                                    config_file=self._config_path())
        self.assertEqual(
            core_config.packs_for_path(self._tmp.name,
                                        os.path.join(self._tmp.name, "a.md"),
                                        list_id="project_terms",
                                        config_file=self._config_path()),
            ["microsoft-style-guide"])

    def test_ste100_no_longer_exposes_pack_methods(self):
        self.assertFalse(hasattr(ste100, "list_glossary_packs"))
        self.assertFalse(hasattr(ste100, "set_enabled_glossary_packs"))


class CustomTermListTests(_TempProjectRoot):
    """A project's own custom_term_lists declaration reaches ste100's
    uniform list_term_lists/add_term/remove_term entry points, the same
    way it reaches every other ruleset -- see core.config.
    effective_term_lists and rulesets/ste100/__init__.py's
    _effective_lists(). Uses the same isolated fake project root every
    other test in this file does, so this never touches the real repo's
    stopslop.config.json."""

    def _write_custom_list(self, list_id, spec):
        core_config.save_custom_term_list(self._tmp.name, "ste100", list_id, spec,
                                           config_file=self._config_path())

    def test_custom_list_appears_in_list_term_lists(self):
        self._write_custom_list("jargon", {"label": "Jargon", "polarity": "deny"})
        views = ste100.list_term_lists()
        self.assertIn("jargon", views)

    def test_add_term_reaches_a_custom_list(self):
        self._write_custom_list("jargon", {"label": "Jargon", "polarity": "deny",
                                            "accepts_additions": True})
        result = ste100.add_term("jargon", "widget", note="test")
        self.assertTrue(result["ok"])
        views = ste100.list_term_lists()
        self.assertIn("widget", views["jargon"]["project_terms"])

    def test_remove_term_reaches_a_custom_list(self):
        self._write_custom_list("jargon", {"label": "Jargon", "polarity": "deny",
                                            "accepts_additions": True})
        ste100.add_term("jargon", "widget", note="test")
        ste100.remove_term("jargon", "widget")
        views = ste100.list_term_lists()
        self.assertNotIn("widget", views["jargon"]["project_terms"])


class CustomCheckTests(_TempProjectRoot):
    """A custom check added through ste100's uniform add_custom_check/
    remove_custom_check entry points reaches the real live gate
    (lint_and_gate), the same way a custom term list reaches
    list_term_lists above -- see core/custom_checks.py and
    rulesets/ste100/lint.py's effective_checks_table()."""

    def test_custom_check_units_names_sentence_and_document_only(self):
        self.assertEqual(ste100.custom_check_units(), ["document", "sentence"])

    def test_added_check_appears_in_list_checks_and_fires_on_a_real_lint(self):
        ste100.add_custom_check(
            "no_todo", "sentence", "TODO left in prose", "file it as a real task",
            1, "warn", 'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        self.assertIn("no_todo", ste100.list_checks())
        result = ste100.lint_and_gate("There is a TODO here that needs doing.")
        self.assertIn("no_todo", [f["kind"] for f in result["semantic_flags"]])

    def test_removed_check_stops_firing(self):
        ste100.add_custom_check(
            "no_todo", "sentence", "x", "y", 1, "warn",
            'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        ste100.remove_custom_check("no_todo")
        self.assertNotIn("no_todo", ste100.list_checks())
        result = ste100.lint_and_gate("There is a TODO here that needs doing.")
        self.assertNotIn("no_todo", [f["kind"] for f in result["semantic_flags"]])

    def test_update_changes_the_matcher_live(self):
        ste100.add_custom_check(
            "no_todo", "sentence", "x", "y", 1, "warn", "return []")
        ste100.update_custom_check(
            "no_todo", "sentence", "TODO left in prose", "file it as a real task",
            1, "warn", 'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        result = ste100.lint_and_gate("There is a TODO here that needs doing.")
        self.assertIn("no_todo", [f["kind"] for f in result["semantic_flags"]])

    def test_a_block_action_denies_through_blocking_semantic_flags(self):
        ste100.add_custom_check(
            "no_todo", "sentence", "x", "y", 1, "block",
            'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        result = ste100.lint_and_gate("There is a TODO here that needs doing.")
        blocking = ste100.blocking_semantic_flags(result["semantic_flags"])
        self.assertTrue(any(f["kind"] == "no_todo" for f in blocking))

    def test_refuses_a_line_unit_ste100_does_not_allow(self):
        with self.assertRaises(Exception):
            ste100.add_custom_check("bad", "line", "x", "y", 1, "warn", "return []")


class CustomCheckVocabularyBindingTests(_TempProjectRoot):
    """A custom check can bind to a curated Vocabulary list -- via that
    list's own `feeds`, the same list-declares-the-check-it-feeds
    direction a built-in check's TERM_LISTS entry already uses -- and
    read it at lint time through its generated function's own
    `extra=()` parameter. See core.custom_checks.extra_by_check_for_custom
    (the resolving side) and core.config.set_custom_term_list_feeds/
    add_custom_term_list's own `feeds` param (the declaring side)."""

    def test_a_custom_check_bound_to_a_custom_list_fires_on_a_listed_word(self):
        core_config.add_custom_term_list(self._tmp.name, "ste100", "jargon", {}, feeds="no_jargon")
        ste100.add_term("jargon", "widget")
        ste100.add_custom_check(
            "no_jargon", "sentence", "project jargon", "use a plain word", 1, "warn",
            'return [{"word": w} for w in extra if w in sentence.lower()]', terms_list="jargon")
        result = ste100.lint_and_gate("The system has a widget installed.")
        self.assertIn("no_jargon", [f["kind"] for f in result["semantic_flags"]])

    def test_an_unbound_custom_check_never_sees_a_list_it_did_not_ask_for(self):
        core_config.add_custom_term_list(self._tmp.name, "ste100", "jargon", {}, feeds="no_jargon")
        ste100.add_term("jargon", "widget")
        # a DIFFERENT custom check, deliberately not bound to "jargon"
        ste100.add_custom_check(
            "other_check", "sentence", "x", "y", 1, "warn",
            'return [{"word": w} for w in extra if w in sentence.lower()]')
        result = ste100.lint_and_gate("The system has a widget installed.")
        self.assertNotIn("other_check", [f["kind"] for f in result["semantic_flags"]])

    def test_removing_the_bound_check_unbinds_the_list_no_orphan_pointer(self):
        core_config.add_custom_term_list(self._tmp.name, "ste100", "jargon", {}, feeds="no_jargon")
        ste100.add_custom_check(
            "no_jargon", "sentence", "x", "y", 1, "warn", "return []", terms_list="jargon")
        ste100.remove_custom_check("no_jargon")
        core_config.clear_feeds_for_check(self._tmp.name, "ste100", "no_jargon")
        lists = core_config.custom_term_lists(self._tmp.name, "ste100")
        self.assertNotIn("feeds", lists["jargon"])


if __name__ == "__main__":
    unittest.main()
