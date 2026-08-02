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
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from types import SimpleNamespace

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


class CmdInitTests(unittest.TestCase):
    def test_force_preserves_unknown_top_level_keys(self):
        # Regression: found live while verifying the prototype->src rename.
        # cmd_init used to overwrite SETTINGS_REAL wholesale from the
        # template, silently dropping "enabledMcpjsonServers" -- a key
        # Claude Code itself writes there the first time a user approves
        # the MCP server, never present in the template at all.
        with tempfile.TemporaryDirectory() as tmp:
            real_path = os.path.join(tmp, "settings.local.json")
            with open(real_path, "w") as f:
                json.dump({"hooks": {"stale": True},
                           "enabledMcpjsonServers": ["stopslop"]}, f)
            original = stopslop.SETTINGS_REAL
            stopslop.SETTINGS_REAL = real_path
            try:
                stopslop.cmd_init(SimpleNamespace(force=True))
                with open(real_path) as f:
                    written = json.load(f)
            finally:
                stopslop.SETTINGS_REAL = original
        self.assertEqual(written["enabledMcpjsonServers"], ["stopslop"])
        self.assertIn("PreToolUse", written["hooks"])


class VersionTests(unittest.TestCase):
    def test_version_string_is_importable(self):
        self.assertRegex(stopslop.VERSION, r"^\d+\.\d+\.\d+$")

    def test_version_flag_prints_it_and_exits_cleanly(self):
        proc = subprocess.run([sys.executable, stopslop.__file__, "--version"],
                               capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0)
        self.assertIn(stopslop.VERSION, proc.stdout)


if __name__ == "__main__":
    unittest.main()
