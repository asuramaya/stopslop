#!/usr/bin/env python3
"""Tests for core/checks.py's shared check-configuration scaffolding.

Pure stdlib unittest against a small synthetic CheckTable -- no dependency
on any real ruleset, so this suite stays meaningful independent of which
ruleset has migrated onto it. See src/rulesets/codewatch/test_lint.py etc.
for the per-ruleset migration's own byte-identical-behavior tests.

Run with:
    cd src && python3 -m unittest core.test_checks -v
or, together with everything else:
    python3 -m unittest discover -s src -p 'test_*.py'
"""
import json
import os
import tempfile
import unittest

from core import checks


def _table(**overrides):
    """A two-check table: `plain` (no params, defaults to warn) and
    `strict` (one param, defaults to block) -- enough surface to exercise
    every scaffolding function without a real ruleset."""
    base = {
        "plain": checks.Check(
            id="plain", unit=checks.Unit.LINE, fn=lambda line: [],
            catches="a plain thing", instead="do the other thing",
        ),
        "strict": checks.Check(
            id="strict", unit=checks.Unit.SENTENCE, fn=lambda sentence: [],
            catches="a strict thing", instead="stop doing it",
            default_threshold=2, default_action="block",
            params={"limit": 10},
        ),
    }
    base.update(overrides)
    return base


class ScaffoldingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project_root = self._tmp.name
        self.table = _table()

    def tearDown(self):
        self._tmp.cleanup()

    def _write_config(self, data):
        path = os.path.join(self.project_root, "stopslop.config.json")
        with open(path, "w") as f:
            json.dump(data, f)

    def test_all_check_ids(self):
        self.assertEqual(checks.all_check_ids(self.table), frozenset({"plain", "strict"}))

    def test_default_check_config(self):
        defaults = checks.default_check_config(self.table)
        self.assertEqual(defaults["plain"], {"threshold": 1, "action": "warn"})
        self.assertEqual(defaults["strict"], {"threshold": 2, "action": "block", "limit": 10})

    def test_check_config_no_config_file(self):
        # No stopslop.config.json at all -- defaults govern unchanged,
        # the same invariant every other config-driven knob in this
        # project gives an unconfigured clone.
        merged = checks.check_config(self.table, self.project_root, "fake")
        self.assertEqual(merged, checks.default_check_config(self.table))

    def test_check_config_valid_override(self):
        self._write_config({"check_config": {"fake": {
            "plain": {"threshold": 5, "action": "block"},
            "strict": {"limit": 20},
        }}})
        merged = checks.check_config(self.table, self.project_root, "fake")
        self.assertEqual(merged["plain"], {"threshold": 5, "action": "block"})
        self.assertEqual(merged["strict"], {"threshold": 2, "action": "block", "limit": 20})

    def test_check_config_invalid_override_ignored_per_field(self):
        # Bad values are dropped field-by-field, never raise into a live
        # gate call reading a hand-edited config.
        self._write_config({"check_config": {"fake": {
            "plain": {"threshold": -1, "action": "sideways"},
            "strict": {"limit": "not a number"},
            "unknown_check": {"threshold": 9},
        }}})
        merged = checks.check_config(self.table, self.project_root, "fake")
        self.assertEqual(merged["plain"], {"threshold": 1, "action": "warn"})
        self.assertEqual(merged["strict"], {"threshold": 2, "action": "block", "limit": 10})
        self.assertNotIn("unknown_check", merged)

    def test_enabled_check_ids_default_all(self):
        self.assertEqual(checks.enabled_check_ids(self.table, self.project_root, "fake"),
                          frozenset({"plain", "strict"}))

    def test_enabled_check_ids_respects_disabled(self):
        self._write_config({"disabled_checks": {"fake": ["strict"]}})
        self.assertEqual(checks.enabled_check_ids(self.table, self.project_root, "fake"),
                          frozenset({"plain"}))

    def test_list_checks(self):
        listing = checks.list_checks(self.table, self.project_root, "fake")
        self.assertEqual(listing["plain"], {"catches": "a plain thing",
                                             "instead": "do the other thing", "enabled": True})
        self.assertTrue(listing["strict"]["enabled"])

    def test_set_enabled_checks_replace_semantics(self):
        checks.set_enabled_checks(self.table, self.project_root, "fake", ["plain"])
        listing = checks.list_checks(self.table, self.project_root, "fake")
        self.assertTrue(listing["plain"]["enabled"])
        self.assertFalse(listing["strict"]["enabled"])
        # A second call re-enabling only "strict" must disable "plain" too
        # -- replace, not merge.
        checks.set_enabled_checks(self.table, self.project_root, "fake", ["strict"])
        listing = checks.list_checks(self.table, self.project_root, "fake")
        self.assertFalse(listing["plain"]["enabled"])
        self.assertTrue(listing["strict"]["enabled"])

    def test_set_enabled_checks_unknown_id_raises(self):
        with self.assertRaises(ValueError):
            checks.set_enabled_checks(self.table, self.project_root, "fake", ["nope"])

    def test_set_checks_enabled_merge_semantics(self):
        # Disable "strict" first, directly.
        checks.set_checks_enabled(self.table, self.project_root, "fake", {"strict": False})
        listing = checks.list_checks(self.table, self.project_root, "fake")
        self.assertTrue(listing["plain"]["enabled"])
        self.assertFalse(listing["strict"]["enabled"])
        # Toggling "plain" off must leave "strict"'s disabled state alone
        # -- merge, not replace. This is the exact shape of the dashboard
        # bug the merge/replace split exists to prevent.
        checks.set_checks_enabled(self.table, self.project_root, "fake", {"plain": False})
        listing = checks.list_checks(self.table, self.project_root, "fake")
        self.assertFalse(listing["plain"]["enabled"])
        self.assertFalse(listing["strict"]["enabled"])

    def test_set_checks_enabled_unknown_id_raises(self):
        with self.assertRaises(ValueError):
            checks.set_checks_enabled(self.table, self.project_root, "fake", {"nope": True})

    def test_list_check_config_shape(self):
        listing = checks.list_check_config(self.table, self.project_root, "fake")
        self.assertEqual(listing["plain"], {"threshold": 1, "action": "warn",
                                             "default_threshold": 1, "default_action": "warn"})
        self.assertEqual(listing["strict"]["params"], {"limit": {"value": 10, "default": 10}})

    def test_set_check_config_threshold_and_action(self):
        checks.set_check_config(self.table, self.project_root, "fake", "plain",
                                 threshold=3, action="block")
        listing = checks.list_check_config(self.table, self.project_root, "fake")
        self.assertEqual(listing["plain"]["threshold"], 3)
        self.assertEqual(listing["plain"]["action"], "block")

    def test_set_check_config_param(self):
        checks.set_check_config(self.table, self.project_root, "fake", "strict", limit=42)
        listing = checks.list_check_config(self.table, self.project_root, "fake")
        self.assertEqual(listing["strict"]["params"]["limit"]["value"], 42)
        # threshold/action untouched by a params-only call.
        self.assertEqual(listing["strict"]["threshold"], 2)

    def test_set_check_config_merges_not_replaces(self):
        checks.set_check_config(self.table, self.project_root, "fake", "strict", threshold=9)
        checks.set_check_config(self.table, self.project_root, "fake", "strict", limit=5)
        listing = checks.list_check_config(self.table, self.project_root, "fake")
        self.assertEqual(listing["strict"]["threshold"], 9)
        self.assertEqual(listing["strict"]["params"]["limit"]["value"], 5)

    def test_set_check_config_unknown_check_raises(self):
        with self.assertRaises(ValueError):
            checks.set_check_config(self.table, self.project_root, "fake", "nope", threshold=1)

    def test_set_check_config_unknown_param_raises(self):
        with self.assertRaises(ValueError):
            checks.set_check_config(self.table, self.project_root, "fake", "plain", bogus=1)

    def test_set_check_config_invalid_threshold_raises(self):
        with self.assertRaises(ValueError):
            checks.set_check_config(self.table, self.project_root, "fake", "plain", threshold=0)

    def test_set_check_config_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            checks.set_check_config(self.table, self.project_root, "fake", "plain", action="sideways")

    def test_set_check_config_invalid_param_raises(self):
        with self.assertRaises(ValueError):
            checks.set_check_config(self.table, self.project_root, "fake", "strict", limit=-5)


class BlockingSemanticFlagsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project_root = self._tmp.name
        self.table = _table()

    def tearDown(self):
        self._tmp.cleanup()

    def _flag(self, kind, occurrences=1):
        return {"kind": kind, "label": kind, "detail": {"occurrences": occurrences}, "text": kind}

    def test_below_threshold_never_blocks(self):
        # "strict" defaults to threshold=2, action="block" -- one
        # occurrence must not block.
        flags = [self._flag("strict")]
        self.assertEqual(checks.blocking_semantic_flags(
            self.table, self.project_root, "fake", flags), [])

    def test_at_threshold_blocks_when_action_is_block(self):
        flags = [self._flag("strict", occurrences=2)]
        self.assertEqual(checks.blocking_semantic_flags(
            self.table, self.project_root, "fake", flags), flags)

    def test_warn_action_never_blocks_regardless_of_occurrences(self):
        # "plain" defaults to action="warn".
        flags = [self._flag("plain", occurrences=50)]
        self.assertEqual(checks.blocking_semantic_flags(
            self.table, self.project_root, "fake", flags), [])

    def test_unknown_kind_never_blocks(self):
        flags = [self._flag("not_a_declared_check", occurrences=99)]
        self.assertEqual(checks.blocking_semantic_flags(
            self.table, self.project_root, "fake", flags), [])

    def test_occurrences_not_deduped_count(self):
        # Ten repeats of the same label must weigh as 10 occurrences of
        # one flag entry, matching core.flags.flag_weight's own contract.
        flags = [self._flag("strict", occurrences=10)]
        self.assertEqual(checks.blocking_semantic_flags(
            self.table, self.project_root, "fake", flags), flags)


if __name__ == "__main__":
    unittest.main()
