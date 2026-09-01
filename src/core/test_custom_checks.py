#!/usr/bin/env python3
"""Tests for core/custom_checks.py -- the per-ruleset custom-check
discovery/loading and validate-then-write machinery. Unlike
core/glossary_packs.py's custom packs, this module takes project_root as
an explicit parameter rather than a module-level global, so every test
here just points at its own tempdir -- nothing touches this repo's own
real .claude/stopslop/custom_checks/.

Run with:
    cd src && ../.venv/bin/python3 -m unittest core.test_custom_checks -v
"""
import os
import tempfile
import unittest

from core import checks as _checks
from core import custom_checks as cc


class _TempProjectRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        self.built_in_ids = {"built_in_check"}


class AddCustomCheckTests(_TempProjectRoot):
    def test_add_then_visible_in_effective_table(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "TODO left in prose", "file it as a real task",
                             1, "warn", 'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertIn("no_todo", table)
        self.assertEqual(table["no_todo"].unit, _checks.Unit.SENTENCE)
        self.assertEqual(table["no_todo"].fn("a TODO here"), [{"phrase": "TODO"}])
        self.assertEqual(table["no_todo"].fn("clean"), [])

    def test_document_unit_check_reaches_the_whole_text(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "banned_phrase",
                             "document", "a banned phrase anywhere in the document", "cut it",
                             1, "warn", 'return [{"phrase": "xyzzy"}] if "xyzzy" in text else []')
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertEqual(table["banned_phrase"].fn("some xyzzy text"), [{"phrase": "xyzzy"}])

    def test_default_threshold_and_action_land_on_the_check(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 3, "block", "return []")
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertEqual(table["no_todo"].default_threshold, 3)
        self.assertEqual(table["no_todo"].default_action, "block")

    def test_refuses_an_id_colliding_with_a_built_in(self):
        with self.assertRaises(ValueError):
            cc.add_custom_check(self.root, "demo", self.built_in_ids, "built_in_check",
                                 "sentence", "x", "y", 1, "warn", "return []")
        self.assertEqual(cc.custom_check_ids(self.root, "demo"), [])

    def test_refuses_re_adding_an_existing_custom_check(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        with self.assertRaises(ValueError):
            cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                                 "sentence", "different", "text", 1, "warn", "return []")

    def test_refuses_a_unit_this_ruleset_does_not_allow(self):
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.add_custom_check(self.root, "demo", self.built_in_ids, "bad_unit",
                                 "line", "x", "y", 1, "warn", "return []",
                                 allowed_units=frozenset({_checks.Unit.SENTENCE}))
        self.assertEqual(cc.custom_check_ids(self.root, "demo"), [])

    def test_a_ruleset_that_allows_line_units_gets_them(self):
        cc.add_custom_check(self.root, "codewatch", self.built_in_ids, "no_fixme",
                             "line", "a FIXME comment", "resolve it or file a real issue",
                             1, "warn", 'return [{"phrase": "FIXME"}] if "FIXME" in line else []',
                             allowed_units=frozenset({_checks.Unit.LINE}))
        table = cc.effective_checks_table({}, self.root, "codewatch",
                                           allowed_units=frozenset({_checks.Unit.LINE}))
        self.assertEqual(table["no_fixme"].fn("# FIXME: this"), [{"phrase": "FIXME"}])

    def test_rejects_a_malformed_check_id(self):
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.add_custom_check(self.root, "demo", self.built_in_ids, "Not-Valid",
                                 "sentence", "x", "y", 1, "warn", "return []")

    def test_a_syntax_error_in_the_body_never_writes_a_file(self):
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.add_custom_check(self.root, "demo", self.built_in_ids, "broken",
                                 "sentence", "x", "y", 1, "warn", "this is not python (")
        self.assertEqual(cc.custom_check_ids(self.root, "demo"), [])

    def test_a_syntax_error_leaves_no_tmp_file_behind(self):
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.add_custom_check(self.root, "demo", self.built_in_ids, "broken",
                                 "sentence", "x", "y", 1, "warn", "this is not python (")
        checks_dir = os.path.join(self.root, ".claude", "stopslop", "custom_checks", "demo")
        leftover = os.listdir(checks_dir) if os.path.isdir(checks_dir) else []
        self.assertEqual(leftover, [])

    def test_a_hand_edited_mechanical_classify_is_refused_on_load(self):
        # Regression: apply_mechanical_fixes is a fixed, hand-written
        # function per ruleset, not data-driven off CHECKS_TABLE -- it has
        # no way to apply a custom check's own fix. A custom check
        # classified "mechanical" would land in mechanical_violations and
        # the live gate would report "auto-fixed" and ALLOW the write
        # while the actual violation goes through untouched. The template
        # never generates classify= at all (Check.classify defaults to
        # "semantic"), so this can only happen via a hand-edit -- exactly
        # what this project's own docs call these files "safe" for.
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        path = cc._check_path(self.root, "demo", "no_todo")
        with open(path) as f:
            src = f.read()
        self.assertIn("default_action='warn',", src)
        src = src.replace("default_action='warn',",
                           "default_action='warn', classify='mechanical',")
        with open(path, "w") as f:
            f.write(src)
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.effective_checks_table({}, self.root, "demo")

    def test_extra_parameter_is_always_available_to_the_matcher(self):
        # Every generated matcher takes a trailing extra=() whether or
        # not a terms_list binds one now -- so binding one later never
        # requires touching a signature the author already wrote against.
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn",
                             'return [{"word": w} for w in extra if w in sentence]')
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertEqual(table["no_todo"].fn("has widget in it", ["widget"]),
                          [{"word": "widget"}])
        self.assertEqual(table["no_todo"].fn("clean", ["widget"]), [])
        # and the default still works when no extra is passed at all
        self.assertEqual(table["no_todo"].fn("clean"), [])

    def test_terms_list_binding_lands_on_the_check_object(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []",
                             terms_list="jargon")
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertEqual(table["no_todo"].terms_list, "jargon")

    def test_no_terms_list_given_leaves_the_check_unbound(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertIsNone(table["no_todo"].terms_list)


class UpdateCustomCheckTests(_TempProjectRoot):
    def test_update_replaces_the_matcher_body(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        cc.update_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                                "sentence", "TODO left in prose", "file it as a real task",
                                2, "block", 'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertEqual(table["no_todo"].fn("a TODO here"), [{"phrase": "TODO"}])
        self.assertEqual(table["no_todo"].default_threshold, 2)
        self.assertEqual(table["no_todo"].default_action, "block")

    def test_a_failed_update_leaves_the_old_version_intact(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn",
                             'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.update_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                                    "sentence", "x", "y", 1, "warn", "this is not python (")
        table = cc.effective_checks_table({}, self.root, "demo")
        self.assertEqual(table["no_todo"].fn("a TODO here"), [{"phrase": "TODO"}])

    def test_refuses_updating_a_check_that_does_not_exist(self):
        with self.assertRaises(ValueError):
            cc.update_custom_check(self.root, "demo", self.built_in_ids, "never_added",
                                    "sentence", "x", "y", 1, "warn", "return []")


class RemoveCustomCheckTests(_TempProjectRoot):
    def test_remove_then_gone_from_the_effective_table(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        cc.remove_custom_check(self.root, "demo", "no_todo")
        self.assertNotIn("no_todo", cc.effective_checks_table({}, self.root, "demo"))

    def test_removing_a_never_added_check_is_a_no_op(self):
        cc.remove_custom_check(self.root, "demo", "never-existed")  # must not raise


class EffectiveCheckTableTests(_TempProjectRoot):
    def test_built_in_wins_on_a_theoretical_collision(self):
        # load_custom_checks refuses a colliding id at ADD time already
        # (AddCustomCheckTests.test_refuses_an_id_colliding_with_a_built_in);
        # this covers the belt-and-suspenders merge-time guard for a check
        # that became a built-in AFTER it was already saved as a custom
        # one (no built-ins named "no_todo" existed yet when it was added).
        cc.add_custom_check(self.root, "demo", set(), "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        built_in = _checks.Check(id="no_todo", unit=_checks.Unit.SENTENCE,
                                  fn=lambda s: [], catches="c", instead="i")
        with self.assertRaises(cc.InvalidCustomCheckError):
            cc.effective_checks_table({"no_todo": built_in}, self.root, "demo")

    def test_no_custom_checks_directory_is_not_an_error(self):
        self.assertEqual(cc.effective_checks_table({}, self.root, "demo"), {})

    def test_render_source_indents_a_multi_line_body(self):
        source = cc.render_source("demo", "no_todo", "sentence", "c", "i", 1, "warn",
                                   "x = 1\nif x:\n    return []\nreturn [x]")
        self.assertIn("    x = 1\n", source)
        self.assertIn("    if x:\n", source)
        self.assertIn("        return []\n", source)


class GetCustomCheckFieldsTests(_TempProjectRoot):
    def test_round_trips_every_field_including_a_multi_line_body(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "TODO left in prose", "file it as a real task",
                             2, "block", 'x = "TODO"\nif x in sentence:\n    return [{"phrase": x}]\nreturn []')
        fields = cc.get_custom_check_fields(self.root, "demo", "no_todo")
        self.assertEqual(fields, {
            "id": "no_todo", "unit": "sentence", "catches": "TODO left in prose",
            "instead": "file it as a real task", "threshold": 2, "action": "block",
            "fn_body": 'x = "TODO"\nif x in sentence:\n    return [{"phrase": x}]\nreturn []',
            "terms_list": None,
        })

    def test_a_terms_list_binding_round_trips_too(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []",
                             terms_list="jargon")
        fields = cc.get_custom_check_fields(self.root, "demo", "no_todo")
        self.assertEqual(fields["terms_list"], "jargon")

    def test_a_single_line_body_round_trips_too(self):
        cc.add_custom_check(self.root, "demo", self.built_in_ids, "no_todo",
                             "sentence", "x", "y", 1, "warn", "return []")
        fields = cc.get_custom_check_fields(self.root, "demo", "no_todo")
        self.assertEqual(fields["fn_body"], "return []")

    def test_refuses_a_check_that_was_never_added(self):
        with self.assertRaises(ValueError):
            cc.get_custom_check_fields(self.root, "demo", "never_added")

    def test_refuses_a_check_id_that_is_only_a_built_in(self):
        with self.assertRaises(ValueError):
            cc.get_custom_check_fields(self.root, "demo", "built_in_check")


class ExtraByCheckForCustomTests(_TempProjectRoot):
    def test_resolves_words_for_a_custom_check_bound_via_feeds(self):
        from core import config as _config, terms as _terms
        spec = _config.add_custom_term_list(self.root, "demo", "jargon", {}, feeds="no_todo")
        _terms.add_term("demo", {"jargon": spec}, self.root, "jargon", "widget")
        effective_lists = _config.effective_term_lists({}, "demo", self.root)
        extra = cc.extra_by_check_for_custom(self.root, "demo", {"no_todo"}, effective_lists)
        self.assertEqual(extra, {"no_todo": ["widget"]})

    def test_a_list_not_bound_to_any_check_produces_nothing(self):
        from core import config as _config
        _config.add_custom_term_list(self.root, "demo", "jargon", {})
        effective_lists = _config.effective_term_lists({}, "demo", self.root)
        extra = cc.extra_by_check_for_custom(self.root, "demo", {"no_todo"}, effective_lists)
        self.assertEqual(extra, {})

    def test_a_list_feeding_an_id_outside_custom_check_ids_is_ignored(self):
        # feeds naming an id that is NOT in custom_check_ids (e.g. a
        # built-in's own list) never produces an entry here -- that
        # check already gets its extra from the ruleset's own
        # hand-written extra_by_check dict.
        from core import config as _config
        _config.add_custom_term_list(self.root, "demo", "jargon", {}, feeds="some_built_in")
        effective_lists = _config.effective_term_lists({}, "demo", self.root)
        extra = cc.extra_by_check_for_custom(self.root, "demo", {"no_todo"}, effective_lists)
        self.assertEqual(extra, {})


if __name__ == "__main__":
    unittest.main()
