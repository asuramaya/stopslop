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
import types
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
                                             "instead": "do the other thing",
                                             "unit": self.table["plain"].unit.value, "enabled": True})
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


class RunChecksTests(unittest.TestCase):
    """Synthetic checks covering every Unit -- see rulesets/codewatch/
    test_lint.py's own DispatcherMigrationTests for the differential
    (byte-identical-to-the-old-hand-written-loop) proof against a real
    ruleset."""

    def _check(self, unit, fn, **overrides):
        return checks.Check(id=overrides.pop("id", "c"), unit=unit, fn=fn,
                             catches="x", instead="y", **overrides)

    def test_line_unit_calls_fn_per_line_no_extra(self):
        table = {"c": self._check(checks.Unit.LINE,
                                   lambda line: [{"word": line}] if line == "bad" else [])}
        mech, sem = checks.run_checks(table, lines=["good", "bad", "good"])
        self.assertEqual(mech, [])
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0], {"kind": "c", "label": "bad", "detail": {"word": "bad"}, "text": "bad"})

    def test_line_unit_with_extra_passed_positionally(self):
        table = {"c": self._check(checks.Unit.LINE,
                                   lambda line, extra: [{"word": extra}] if line == "x" else [])}
        mech, sem = checks.run_checks(table, lines=["x"], extra_by_check={"c": "injected"})
        self.assertEqual(sem[0]["detail"], {"word": "injected"})

    def test_line_unit_skipped_when_no_lines_given(self):
        table = {"c": self._check(checks.Unit.LINE, lambda line: [{"word": line}])}
        mech, sem = checks.run_checks(table, sentences=["x"])  # lines never supplied
        self.assertEqual((mech, sem), ([], []))

    def test_line_lookahead_sees_next_line_and_none_at_eof(self):
        seen = []

        def fn(line, next_line):
            seen.append((line, next_line))
            return []
        table = {"c": self._check(checks.Unit.LINE_LOOKAHEAD, fn)}
        checks.run_checks(table, lines=["a", "b"])
        self.assertEqual(seen, [("a", "b"), ("b", None)])

    def test_lines_indexed_receives_whole_list_and_index(self):
        seen = []

        def fn(lines, i):
            seen.append((tuple(lines), i))
            return []
        table = {"c": self._check(checks.Unit.LINES_INDEXED, fn)}
        checks.run_checks(table, lines=["a", "b"])
        self.assertEqual(seen, [(("a", "b"), 0), (("a", "b"), 1)])

    def test_sentence_unit_calls_fn_per_sentence(self):
        table = {"c": self._check(checks.Unit.SENTENCE,
                                   lambda s: [{"phrase": s}] if "bad" in s else [])}
        mech, sem = checks.run_checks(table, sentences=["ok.", "a bad one."])
        self.assertEqual(len(sem), 1)
        self.assertEqual(sem[0]["text"], "a bad one.")

    def test_sentences_unit_calls_fn_once_with_all_sentences(self):
        calls = []

        def fn(sentences):
            calls.append(list(sentences))
            return [{"phrase": "x", "text": "combined"}]
        table = {"c": self._check(checks.Unit.SENTENCES, fn)}
        mech, sem = checks.run_checks(table, sentences=["a", "b"])
        self.assertEqual(calls, [["a", "b"]])
        self.assertEqual(sem[0]["text"], "combined")

    def test_document_unit_calls_fn_once_with_whole_text_label_none(self):
        table = {"c": self._check(checks.Unit.DOCUMENT,
                                   lambda text: [{"count": 3, "note": "x"}])}
        mech, sem = checks.run_checks(table, text="whole document")
        self.assertEqual(sem[0], {"kind": "c", "label": None,
                                    "detail": {"count": 3, "note": "x"}, "text": None})

    def test_document_unit_with_extra(self):
        table = {"c": self._check(checks.Unit.DOCUMENT,
                                   lambda text, extra: [{"phrase": extra}])}
        mech, sem = checks.run_checks(table, text="x", extra_by_check={"c": "ctx"})
        self.assertEqual(sem[0]["detail"], {"phrase": "ctx"})

    def test_classify_literal_mechanical(self):
        table = {"c": self._check(checks.Unit.LINE, lambda line: [{"word": line}],
                                   classify="mechanical")}
        mech, sem = checks.run_checks(table, lines=["x"])
        self.assertEqual(len(mech), 1)
        self.assertEqual(sem, [])

    def test_classify_callable_decides_per_violation(self):
        table = {"c": self._check(
            checks.Unit.LINE, lambda line: [{"word": line, "auto_fix": line == "fixable"}],
            classify=lambda v: "mechanical" if v["auto_fix"] else "semantic")}
        mech, sem = checks.run_checks(table, lines=["fixable", "not"])
        self.assertEqual([m["text"] for m in mech], ["fixable"])
        self.assertEqual([s["text"] for s in sem], ["not"])

    def test_label_falls_back_through_word_phrase_modal(self):
        table = {"c": self._check(checks.Unit.LINE, lambda line: [{"modal": "should"}])}
        _, sem = checks.run_checks(table, lines=["x"])
        self.assertEqual(sem[0]["label"], "should")

    def test_order_is_item_major_check_minor_not_the_reverse(self):
        # The bug this guards: a per-check outer loop (all of line 0's
        # matches, all of line 1's, ...) produces a DIFFERENT flag order
        # than a hand-written loop's actual shape (check_a(line) then
        # check_b(line), for every line) -- a denial message's flag
        # order is real, observable behavior, not an implementation
        # detail free to shuffle during a refactor.
        table = {
            "a": self._check(checks.Unit.LINE, lambda line: [{"word": "a-" + line}], id="a"),
            "b": self._check(checks.Unit.LINE, lambda line: [{"word": "b-" + line}], id="b"),
        }
        _, sem = checks.run_checks(table, lines=["x", "y"])
        self.assertEqual([s["detail"]["word"] for s in sem],
                          ["a-x", "b-x", "a-y", "b-y"])

    def test_two_checks_in_one_table_both_dispatch(self):
        table = {
            "a": self._check(checks.Unit.LINE, lambda line: [{"word": "A"}], id="a"),
            "b": self._check(checks.Unit.DOCUMENT, lambda text: [{"word": "B"}], id="b"),
        }
        mech, sem = checks.run_checks(table, lines=["x"], text="whole")
        self.assertEqual({s["kind"] for s in sem}, {"a", "b"})


if __name__ == "__main__":
    unittest.main()


class BlockingSignatureCompatibilityTests(unittest.TestCase):
    """`file_path` is a LATER addition to the ruleset contract.

    Custom rulesets are a shipped feature and live outside this
    repository under `.claude/stopslop/`. One written against the older
    two-name signature must keep working, and it must keep working
    SILENTLY -- a project author who scaffolded a ruleset months ago did
    nothing wrong.
    """

    def _ruleset(self, fn):
        return types.SimpleNamespace(blocking_semantic_flags=fn)

    def test_an_old_two_name_signature_still_works(self):
        seen = []
        ruleset = self._ruleset(lambda flags: seen.append(flags) or ["old"])
        got = checks.call_blocking_semantic_flags(ruleset, ["f"], "a.md")
        self.assertEqual(got, ["old"])
        self.assertEqual(seen, [["f"]])

    def test_a_new_signature_receives_the_path(self):
        seen = {}

        def fn(flags, file_path=None):
            seen["path"] = file_path
            return ["new"]

        got = checks.call_blocking_semantic_flags(self._ruleset(fn), ["f"], "a.md")
        self.assertEqual(got, ["new"])
        self.assertEqual(seen["path"], "a.md")

    def test_a_type_error_inside_a_check_is_not_read_as_an_old_signature(self):
        """Wrapping the call in `except TypeError` would swallow a real
        TypeError from inside a check and report it as an old signature,
        which is the kind of misdiagnosis that costs an afternoon."""

        def fn(flags, file_path=None):
            raise TypeError("a real bug inside the check")

        with self.assertRaises(TypeError):
            checks.call_blocking_semantic_flags(self._ruleset(fn), ["f"], "a.md")

    def test_an_uninspectable_callable_falls_back_to_the_old_form(self):
        class Callable:
            def __call__(self, flags):
                return ["called"]

        got = checks.call_blocking_semantic_flags(
            self._ruleset(Callable().__call__), ["f"], "a.md")
        self.assertEqual(got, ["called"])


class CheckKindTests(unittest.TestCase):
    """What a check's SILENCE means.

    "19 of 31 fired zero times" is alarming and unactionable until the
    silent ones are split. A tell that stopped firing has stopped
    describing anything. A defect that never fires is rare, which is the
    outcome you wanted -- pruning it reads success as failure. Frequency
    alone cannot separate them, so each check declares its own kind.
    """

    def test_a_check_is_a_tell_unless_it_says_otherwise(self):
        """The safe default. A new check is a correlate until someone has
        thought about whether it is wrong whatever wrote it."""
        check = checks.Check(id="x", unit=checks.Unit.SENTENCE, fn=lambda s: [],
                              catches="c", instead="i")
        self.assertEqual(check.kind, "tell")

    def test_every_check_declares_a_valid_kind(self):
        import rulesets
        for module in rulesets.list_rulesets():
            table = getattr(module, "CHECKS_TABLE", None)
            if table is None:
                continue
            for check_id, check in table.items():
                self.assertIn(getattr(check, "kind", "tell"),
                               ("tell", "defect"),
                               f"{module.RULESET_ID}.{check_id}")

    def test_the_defect_checks_are_the_ones_wrong_whatever_wrote_them(self):
        """Named explicitly so that widening this set is a decision
        somebody made rather than a default that drifted."""
        import rulesets
        slopwatch = rulesets.get_ruleset("slopwatch")
        defects = {cid for cid, c in slopwatch.CHECKS_TABLE.items()
                    if getattr(c, "kind", "tell") == "defect"}
        self.assertEqual(defects, {"ai_markup_remnant", "emoji_in_prose",
                                    "entity_encoded_punctuation",
                                    "id_label_lead"})

    def test_a_blocking_check_is_a_defect(self):
        """A check that DENIES a write on evidence that is only a
        correlate is the unsound-gate criticism this project accepted.
        Blocking implies the thing caught is wrong on its own terms."""
        import rulesets
        for module in rulesets.list_rulesets():
            table = getattr(module, "CHECKS_TABLE", None)
            if table is None or module.RULESET_ID == "ste100":
                continue
            for check_id, check in table.items():
                if check.default_action == "block":
                    self.assertEqual(getattr(check, "kind", "tell"), "defect",
                                      f"{module.RULESET_ID}.{check_id} blocks "
                                      "a write but is only declared a tell")
