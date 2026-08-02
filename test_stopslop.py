#!/usr/bin/env python3
"""Direct-function tests for stopslop.py's ruleset-resolution and
capability-gating logic -- the CLI dispatcher itself still has no
end-to-end subprocess test coverage (see README's gap list), but the two
pieces of genuinely new logic the pluggable-ruleset refactor added
(_resolve's explicit-vs-config-driven resolution, _require_glossary's
capability gate) are exercised directly here against the real registered
rulesets (ste100 has "glossary", slopwatch doesn't -- a real fixture
already on hand, not a mock).

Run with:
    python3 -m unittest test_stopslop -v
"""
import io
import unittest
from contextlib import redirect_stderr

import stopslop


class ResolveTests(unittest.TestCase):
    def test_explicit_ruleset_wins_regardless_of_path(self):
        ruleset = stopslop._resolve("slopwatch", stopslop.REPO_ROOT + "/README.md")
        self.assertEqual(ruleset.RULESET_ID, "slopwatch")

    def test_no_explicit_ruleset_resolves_via_config(self):
        ruleset = stopslop._resolve(None, stopslop.REPO_ROOT + "/README.md")
        self.assertEqual(ruleset.RULESET_ID, "ste100")

    def test_synthetic_stdin_path_resolves_like_a_real_md_file(self):
        ruleset = stopslop._resolve(None, stopslop._SYNTHETIC_STDIN_PATH)
        self.assertEqual(ruleset.RULESET_ID, "ste100")

    def test_unresolvable_path_exits_with_message(self):
        out_of_scope = stopslop.REPO_ROOT + "/somefile.py"
        with redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit):
                stopslop._resolve(None, out_of_scope)
        self.assertIn("doesn't resolve to any ruleset", err.getvalue())

    def test_unknown_explicit_ruleset_raises(self):
        with self.assertRaises(Exception):
            stopslop._resolve("__not_a_real_ruleset__", stopslop.REPO_ROOT + "/README.md")


class RequireGlossaryTests(unittest.TestCase):
    def test_glossary_capable_ruleset_passes_through(self):
        ruleset = stopslop._resolve("ste100", stopslop._SYNTHETIC_STDIN_PATH)
        stopslop._require_glossary(ruleset, "register")  # must not raise/exit

    def test_non_glossary_ruleset_exits_with_clear_message(self):
        ruleset = stopslop._resolve("slopwatch", stopslop._SYNTHETIC_STDIN_PATH)
        with redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit):
                stopslop._require_glossary(ruleset, "register")
        self.assertIn("no glossary", err.getvalue())


if __name__ == "__main__":
    unittest.main()
