#!/usr/bin/env python3
"""Tests for rulesets/__init__.py's own custom-ruleset registry glue:
rescan_custom_rulesets() (pick up a freshly-scaffolded package with no
restart) and unregister_ruleset() (drop a removed one just as live).

Touches the real repo's .claude/stopslop/custom_rulesets/ and the live
_REGISTRY/_CUSTOM_RULESET_IDS -- there's no test seam around either
(rulesets/__init__.py resolves project root the same un-overridable way
every other un-seamed module here does, and the registry is genuinely
process-global). Every test cleans up in tearDown, always, so
core/test_config.py's own pinning test (registry resolves to exactly
{"ste100", "slopwatch", "codewatch"}) never sees a leftover.

Run with:
    cd src && ../.venv/bin/python3 -m unittest rulesets.test_custom_rulesets_registry -v
"""
import os
import unittest

import rulesets
from core import custom_rulesets as cr
from core import paths as core_paths

PROJECT_ROOT = core_paths.find_project_root(__file__)


class CustomRulesetRegistryTests(unittest.TestCase):
    RULESET_ID = "webui_test_scratch_ruleset"

    def tearDown(self):
        if self.RULESET_ID in rulesets._REGISTRY:
            rulesets.unregister_ruleset(self.RULESET_ID)
        cr.remove_ruleset(PROJECT_ROOT, self.RULESET_ID)

    def test_scaffold_then_rescan_registers_it_live(self):
        self.assertNotIn(self.RULESET_ID, rulesets._REGISTRY)
        cr.scaffold_ruleset(PROJECT_ROOT, self.RULESET_ID, "Scratch",
                             existing_ids=set(rulesets._REGISTRY))
        rulesets.rescan_custom_rulesets()
        self.assertIn(self.RULESET_ID, rulesets._REGISTRY)
        module = rulesets.get_ruleset(self.RULESET_ID)
        self.assertEqual(module.RULESET_NAME, "Scratch")
        self.assertIn(self.RULESET_ID, [m.RULESET_ID for m in rulesets.list_rulesets()])

    def test_unregister_then_gone_from_the_live_registry(self):
        cr.scaffold_ruleset(PROJECT_ROOT, self.RULESET_ID, "Scratch",
                             existing_ids=set(rulesets._REGISTRY))
        rulesets.rescan_custom_rulesets()
        rulesets.unregister_ruleset(self.RULESET_ID)
        with self.assertRaises(rulesets.UnknownRulesetError):
            rulesets.get_ruleset(self.RULESET_ID)

    def test_unregister_refuses_a_built_in(self):
        with self.assertRaises(rulesets.InvalidRulesetError):
            rulesets.unregister_ruleset("codewatch")
        self.assertIn("codewatch", rulesets._REGISTRY)

    def test_unregister_refuses_an_unknown_id(self):
        with self.assertRaises(rulesets.UnknownRulesetError):
            rulesets.unregister_ruleset("never-registered-anything")

    def test_the_pinning_set_is_undisturbed_after_a_full_round_trip(self):
        cr.scaffold_ruleset(PROJECT_ROOT, self.RULESET_ID, "Scratch",
                             existing_ids=set(rulesets._REGISTRY))
        rulesets.rescan_custom_rulesets()
        rulesets.unregister_ruleset(self.RULESET_ID)
        cr.remove_ruleset(PROJECT_ROOT, self.RULESET_ID)
        self.assertEqual({m.RULESET_ID for m in rulesets.list_rulesets()},
                          {"ste100", "slopwatch", "codewatch"})


if __name__ == "__main__":
    unittest.main()
