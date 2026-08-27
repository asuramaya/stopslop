#!/usr/bin/env python3
"""Tests for core/custom_rulesets.py -- scaffolding, discovery, and
removal of a whole custom ruleset package. Every test points at its own
tempdir project root, so nothing here touches this repo's own real
.claude/stopslop/custom_rulesets/.

Run with:
    cd src && ../.venv/bin/python3 -m unittest core.test_custom_rulesets -v
"""
import os
import tempfile
import unittest

from core import custom_rulesets as cr


class _TempProjectRoot(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = self._tmp.name
        open(os.path.join(self.root, "stopslop.py"), "w").close()


class ScaffoldRulesetTests(_TempProjectRoot):
    def test_scaffold_then_loadable_and_satisfies_the_contract(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo Ruleset", existing_ids=set())
        module = cr.load_ruleset_module(self.root, "demo_ruleset")
        self.assertEqual(module.RULESET_ID, "demo_ruleset")
        self.assertEqual(module.RULESET_NAME, "Demo Ruleset")
        for attr in ("lint_and_gate", "blocking_semantic_flags", "apply_mechanical_fixes"):
            self.assertTrue(callable(getattr(module, attr)))
        self.assertEqual(module.TERM_LISTS, {})
        self.assertEqual(module.CHECKS_TABLE, {})

    def test_lint_and_gate_runs_clean_with_no_checks_yet(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo", existing_ids=set())
        module = cr.load_ruleset_module(self.root, "demo_ruleset")
        result = module.lint_and_gate("Ordinary prose, nothing special.")
        self.assertEqual(result["status"], "clean")
        self.assertEqual(result["semantic_flags"], [])

    def test_a_custom_check_added_afterward_reaches_the_live_gate(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo", existing_ids=set())
        module = cr.load_ruleset_module(self.root, "demo_ruleset")
        module.add_custom_check(
            "no_todo", "sentence", "a TODO left in prose", "file it as a real task",
            1, "warn", 'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        result = module.lint_and_gate("There is a TODO here.")
        self.assertIn("no_todo", [f["kind"] for f in result["semantic_flags"]])

    def test_a_custom_term_list_reaches_list_term_lists(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo", existing_ids=set())
        module = cr.load_ruleset_module(self.root, "demo_ruleset")
        from core import config as core_config
        core_config.save_custom_term_list(self.root, "demo_ruleset", "jargon",
                                           {"label": "Jargon", "polarity": "deny",
                                            "accepts_additions": True})
        views = module.list_term_lists()
        self.assertIn("jargon", views)

    def test_refuses_a_malformed_id(self):
        with self.assertRaises(cr.InvalidCustomRulesetError):
            cr.scaffold_ruleset(self.root, "Not-Valid", "x", existing_ids=set())
        self.assertEqual(cr.custom_ruleset_ids(self.root), [])

    def test_refuses_an_id_already_known(self):
        with self.assertRaises(ValueError):
            cr.scaffold_ruleset(self.root, "ste100", "x", existing_ids={"ste100"})
        self.assertEqual(cr.custom_ruleset_ids(self.root), [])

    def test_a_pre_existing_directory_not_in_existing_ids_raises_a_clean_value_error(self):
        # Regression: a leftover directory from an interrupted previous
        # scaffold (or two concurrent submissions racing each other) used
        # to raise a raw FileExistsError from os.makedirs -- neither
        # ValueError nor InvalidCustomRulesetError, so it escaped every
        # caller's except clause. Confirmed live via the webui before this
        # was fixed at the source: a plain 500 with no error banner.
        os.makedirs(os.path.join(self.root, ".claude", "stopslop",
                                  "custom_rulesets", "ghost"))
        with self.assertRaises(ValueError):
            cr.scaffold_ruleset(self.root, "ghost", "Ghost", existing_ids=set())

    def test_refuses_re_scaffolding_an_existing_custom_ruleset(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo", existing_ids=set())
        with self.assertRaises(ValueError):
            cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo Again",
                                 existing_ids={"demo_ruleset"})

    def test_default_name_falls_back_to_the_id(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "  ", existing_ids=set())
        module = cr.load_ruleset_module(self.root, "demo_ruleset")
        self.assertEqual(module.RULESET_NAME, "demo_ruleset")


class RemoveRulesetTests(_TempProjectRoot):
    def test_remove_then_gone_from_custom_ruleset_ids(self):
        cr.scaffold_ruleset(self.root, "demo_ruleset", "Demo", existing_ids=set())
        cr.remove_ruleset(self.root, "demo_ruleset")
        self.assertEqual(cr.custom_ruleset_ids(self.root), [])

    def test_removing_a_never_scaffolded_ruleset_is_a_no_op(self):
        cr.remove_ruleset(self.root, "never-existed")  # must not raise


class DiscoveryTests(_TempProjectRoot):
    def test_no_custom_rulesets_directory_is_not_an_error(self):
        self.assertEqual(cr.custom_ruleset_ids(self.root), [])

    def test_multiple_scaffolded_rulesets_all_discovered(self):
        cr.scaffold_ruleset(self.root, "ruleset_a", "A", existing_ids=set())
        cr.scaffold_ruleset(self.root, "ruleset_b", "B", existing_ids={"ruleset_a"})
        self.assertEqual(cr.custom_ruleset_ids(self.root), ["ruleset_a", "ruleset_b"])

    def test_a_directory_with_no_init_py_is_not_a_ruleset(self):
        os.makedirs(os.path.join(self.root, ".claude", "stopslop", "custom_rulesets", "junk"))
        self.assertEqual(cr.custom_ruleset_ids(self.root), [])


if __name__ == "__main__":
    unittest.main()
