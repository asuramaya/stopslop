#!/usr/bin/env python3
"""Subprocess/stdin-JSON tests for the live PreToolUse hook
(pretool_hook.py) -- previously hand-verified only (see README's gap
list). Runs the real script as a real subprocess, the same way Claude
Code itself invokes it, against a throwaway copy of src/ plus a bare
stopslop.py landmark in a temp directory. paths.find_project_root()
resolves PROJECT_ROOT from the running script's own location, so every
side effect (history log, coaching memory) lands inside that temp copy
and never touches this project's own real gate history -- the same class
of test-pollution bug this project already hit once with a hardcoded
PROJECT_ROOT (see project memory).

Run with:
    cd src && python3 -m unittest test_pretool_hook -v
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class PretoolHookSubprocessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        real_src = os.path.dirname(os.path.abspath(__file__))
        cls.tmp = tempfile.mkdtemp(prefix="stopslop_hook_test_")
        shutil.copytree(real_src, os.path.join(cls.tmp, "src"),
                         ignore=shutil.ignore_patterns("__pycache__"))
        # find_project_root() walks up from pretool_hook.py looking for a
        # file named exactly this -- an empty file satisfies it.
        open(os.path.join(cls.tmp, "stopslop.py"), "w").close()
        cls.hook_path = os.path.join(cls.tmp, "src", "pretool_hook.py")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, tool_name, tool_input):
        payload = {"tool_name": tool_name, "tool_input": tool_input}
        return subprocess.run(
            [sys.executable, self.hook_path],
            input=json.dumps(payload), capture_output=True, text=True, timeout=10,
        )

    def _target(self, name):
        return os.path.join(self.tmp, name)

    # These target notes.md, not README.md -- the repo-root README.md is a
    # real slopwatch default now (see the dedicated ste100-vs-slopwatch
    # tests below), and these are specifically exercising STE100's own
    # rules (semicolon auto-fix, "should"-modal denial), independent of
    # that routing decision.
    def test_clean_write_passes_silently(self):
        proc = self._run("Write", {"file_path": self._target("notes.md"),
                                    "content": "The system starts the service."})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_mechanical_violation_gets_auto_fixed(self):
        proc = self._run("Write", {"file_path": self._target("notes.md"),
                                    "content": "The system starts; it also stops."})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "allow")
        self.assertIn("auto-fixed", decision["permissionDecisionReason"])
        self.assertNotIn(";", decision["updatedInput"]["content"])

    def test_semantic_violation_denies_the_write(self):
        proc = self._run("Write", {"file_path": self._target("notes.md"),
                                    "content": "The system should start the service."})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("should", decision["permissionDecisionReason"])

    def test_bash_heredoc_write_is_detected_and_denied(self):
        command = "cat > {}/notes.md <<'EOF'\nThe system should start.\nEOF".format(self.tmp)
        proc = self._run("Bash", {"command": command})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")

    def test_claude_scoped_write_is_out_of_scope(self):
        proc = self._run("Write", {"file_path": self._target(".claude/foo.md"),
                                    "content": "The system should start."})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_unscoped_extension_write_passes_through_silently(self):
        # .json has no default rule at all (unlike .py, a real codewatch
        # default now -- see the dedicated codewatch test below).
        proc = self._run("Write", {"file_path": self._target("foo.json"),
                                    "content": "{}"})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_root_readme_write_routes_to_slopwatch_by_default(self):
        # Live regression coverage for the new default: the repo-root
        # README.md now resolves to slopwatch, not ste100. Uses an em-dash
        # cluster (4, past slopwatch's own em_dash_threshold of 3) since
        # that check always blocks alone -- a single weasel/filler-style
        # flag would not, under slopwatch's count-4 policy, so it wouldn't
        # actually prove routing changed the live gate's real decision.
        proc = self._run("Write", {"file_path": self._target("README.md"),
                                    "content": "The system works — quickly — reliably — safely — always."})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("em_dash_cluster", decision["permissionDecisionReason"])

    def test_py_write_routes_to_codewatch_by_default(self):
        # Live regression coverage for the new default: .py now resolves to
        # codewatch. A bare `except: pass` always blocks under codewatch's
        # own policy, regardless of flag count.
        proc = self._run("Write", {"file_path": self._target("tool.py"),
                                    "content": "try:\n    risky()\nexcept Exception:\n    pass\n"})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("swallowed_exception", decision["permissionDecisionReason"])

    def test_side_effects_land_in_the_isolated_copy_not_the_real_repo(self):
        self._run("Write", {"file_path": self._target("notes.md"),
                             "content": "The system starts the service."})
        self.assertTrue(os.path.exists(
            os.path.join(self.tmp, ".claude", "stopslop-history.log")))


if __name__ == "__main__":
    unittest.main()
