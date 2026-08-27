#!/usr/bin/env python3
"""Tests for rulesets/__init__.py's own custom-ruleset registry glue:
rescan_custom_rulesets() (pick up a freshly-scaffolded package with no
restart), unregister_ruleset() (drop a removed one just as live), and
the quarantine behavior a broken custom ruleset gets (BrokenRulesetTests
below) -- a single malformed file under custom_rulesets/ used to make
"import rulesets" itself raise, taking down the live gate hook, the CLI,
the MCP server, and the dashboard all at once. Confirmed live before the
fix (a fresh interpreter, a broken file already on disk); ImportResilienceTests
reproduces that exact scenario with importlib.reload, which re-executes
this module's own top-level code -- including _discover_and_register() --
the same way a fresh process's first `import rulesets` would.

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
import importlib
import os
import shutil
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


class BrokenRulesetTests(unittest.TestCase):
    """A malformed custom ruleset must never take any OTHER ruleset down
    with it -- see _discover_custom_rulesets()'s own docstring for why
    this differs from a built-in's load failure."""

    BROKEN_ID = "webui_test_broken_ruleset"

    def _broken_dir(self):
        return os.path.join(PROJECT_ROOT, ".claude", "stopslop", "custom_rulesets", self.BROKEN_ID)

    def setUp(self):
        os.makedirs(self._broken_dir())
        with open(os.path.join(self._broken_dir(), "__init__.py"), "w") as f:
            f.write(f'RULESET_ID = {self.BROKEN_ID!r}\n')  # missing everything else required

    def tearDown(self):
        rulesets._CUSTOM_RULESET_ERRORS.pop(self.BROKEN_ID, None)
        shutil.rmtree(self._broken_dir(), ignore_errors=True)

    def test_rescan_does_not_raise_and_quarantines_the_error(self):
        rulesets.rescan_custom_rulesets()  # must not raise
        self.assertNotIn(self.BROKEN_ID, rulesets._REGISTRY)
        errors = rulesets.custom_ruleset_errors()
        self.assertIn(self.BROKEN_ID, errors)
        self.assertIn("RULESET_NAME", errors[self.BROKEN_ID])

    def test_every_built_in_still_works_alongside_a_broken_custom_one(self):
        rulesets.rescan_custom_rulesets()
        for ruleset_id in ("ste100", "slopwatch", "codewatch"):
            module = rulesets.get_ruleset(ruleset_id)
            result = module.lint_and_gate("plain text")  # must not raise
            self.assertIn(result["status"], ("clean", "semantic_flags", "mechanical_violations"))

    def test_a_fixed_file_is_picked_up_on_the_next_scan(self):
        rulesets.rescan_custom_rulesets()
        self.assertIn(self.BROKEN_ID, rulesets.custom_ruleset_errors())
        cr.remove_ruleset(PROJECT_ROOT, self.BROKEN_ID)
        cr.scaffold_ruleset(PROJECT_ROOT, self.BROKEN_ID, "Fixed",
                             existing_ids=set(rulesets._REGISTRY))
        rulesets.rescan_custom_rulesets()
        try:
            self.assertNotIn(self.BROKEN_ID, rulesets.custom_ruleset_errors())
            self.assertIn(self.BROKEN_ID, rulesets._REGISTRY)
        finally:
            rulesets.unregister_ruleset(self.BROKEN_ID)


class ImportResilienceTests(unittest.TestCase):
    """Reproduces the exact scenario that used to break every consumer of
    this package at once: a broken custom ruleset already on disk BEFORE
    `import rulesets` runs for the first time in a process. importlib.
    reload re-executes rulesets/__init__.py's top-level code -- including
    _discover_and_register() -- the same way a fresh interpreter's first
    import would; this is the closest a same-process test can get to that
    without actually spawning a subprocess."""

    BROKEN_ID = "webui_test_import_time_broken_ruleset"

    def _broken_dir(self):
        return os.path.join(PROJECT_ROOT, ".claude", "stopslop", "custom_rulesets", self.BROKEN_ID)

    def tearDown(self):
        shutil.rmtree(self._broken_dir(), ignore_errors=True)
        importlib.reload(rulesets)  # restore a clean registry for every later test

    def test_a_fresh_import_with_a_broken_ruleset_already_on_disk_does_not_raise(self):
        os.makedirs(self._broken_dir())
        with open(os.path.join(self._broken_dir(), "__init__.py"), "w") as f:
            f.write(f'RULESET_ID = {self.BROKEN_ID!r}\n')
        importlib.reload(rulesets)  # must not raise
        self.assertEqual({m.RULESET_ID for m in rulesets.list_rulesets()},
                          {"ste100", "slopwatch", "codewatch"})
        self.assertIn(self.BROKEN_ID, rulesets.custom_ruleset_errors())


if __name__ == "__main__":
    unittest.main()
