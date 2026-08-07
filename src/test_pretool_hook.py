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


class ResultingTextTests(unittest.TestCase):
    """The pure half of the ratchet: what text gets judged. The judged
    text is where two real cheats lived -- delta-linting let a file
    accrete slop threshold-1 flags per Edit, and handed Edit a free pass
    on the embedded-prose pass (a new_string fragment almost never
    parses as Python, so the extractor saw nothing)."""

    def setUp(self):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import pretool_hook
        self.hook = pretool_hook

    def test_write_results_in_exactly_its_content(self):
        self.assertEqual(
            self.hook._resulting_text("Write", {"content": "whole new file"},
                                        "old stuff"),
            "whole new file")

    def test_edit_reconstructs_the_post_edit_file(self):
        after = self.hook._resulting_text(
            "Edit", {"old_string": "TARGET", "new_string": "bbb"},
            "aaa\nTARGET\nccc\n")
        self.assertEqual(after, "aaa\nbbb\nccc\n")

    def test_edit_replaces_once_unless_replace_all(self):
        before = "x xx x xx"
        self.assertEqual(self.hook._resulting_text(
            "Edit", {"old_string": "xx", "new_string": "y"}, before), "x y x xx")
        self.assertEqual(self.hook._resulting_text(
            "Edit", {"old_string": "xx", "new_string": "y",
                      "replace_all": True}, before), "x y x y")

    def test_an_unfindable_old_string_yields_none(self):
        # The Edit tool itself will fail on this; the gate falls back to
        # judging the chunk rather than inventing a file state.
        self.assertIsNone(self.hook._resulting_text(
            "Edit", {"old_string": "absent", "new_string": "y"}, "content"))
        self.assertIsNone(self.hook._resulting_text(
            "Edit", {"old_string": "", "new_string": "y"}, "content"))


class RatchetSubprocessTests(unittest.TestCase):
    """The gate judges the RESULTING file, ratcheted against the current
    one. Each test names the cheat it retires. Own temp project with its
    own config: the ratchet cases need slopwatch (the density policy) on
    every .md file and the embedded-prose pass on .py, neither of which
    DEFAULT_RULES gives."""

    @classmethod
    def setUpClass(cls):
        real_src = os.path.dirname(os.path.abspath(__file__))
        cls.tmp = tempfile.mkdtemp(prefix="stopslop_ratchet_test_")
        shutil.copytree(real_src, os.path.join(cls.tmp, "src"),
                         ignore=shutil.ignore_patterns("__pycache__"))
        open(os.path.join(cls.tmp, "stopslop.py"), "w").close()
        with open(os.path.join(cls.tmp, "stopslop.config.json"), "w") as f:
            json.dump({
                "rulesets": [
                    {"glob": "*.md", "ruleset": "slopwatch"},
                    {"glob": "*.py", "ruleset": "codewatch",
                     "embedded_prose": "slopwatch"},
                ],
                # Every check defaults to action="warn" now -- the ratchet
                # cases below need a check that actually denies once its
                # own threshold is crossed, the same way em_dash_cluster
                # already does by default; these two are the checks the
                # fixture text below happens to exercise.
                "check_config": {"slopwatch": {
                    "vague_intensifier": {"threshold": 4, "action": "block"},
                    "marketing_adjective": {"threshold": 4, "action": "block"},
                }},
            }, f)
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

    def _put(self, name, content):
        path = self._target(name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_accretion_cheat_is_dead_an_edit_cannot_push_a_file_past_the_bar(self):
        # Three flags on disk (under slopwatch's threshold of 4); the edit
        # adds one more. Delta-linting saw a one-flag chunk and allowed it.
        path = self._put("accrete.md",
                          "It is very fast. It is really fast. It is quite fast.\n")
        proc = self._run("Edit", {"file_path": path,
                                    "old_string": "quite fast.",
                                    "new_string": "quite fast. It is significantly fast."})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("Ratchet", decision["permissionDecisionReason"])

    def test_a_legacy_sloppy_file_stays_editable_when_the_edit_adds_nothing(self):
        # Five flags already on disk -- past the threshold -- and the edit
        # touches something unrelated. Absolute judgment of the resulting
        # file would freeze every sloppy file forever; the ratchet only
        # refuses to make things worse.
        path = self._put("legacy.md",
                          "It is very fast, really smooth, quite light, "
                          "significantly small and very neat.\nVersion 1.\n")
        proc = self._run("Edit", {"file_path": path,
                                    "old_string": "Version 1.",
                                    "new_string": "Version 2."})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    def test_monotony_cheat_is_dead_repeats_count_as_occurrences(self):
        # One label repeated four times used to dedup to a single flag and
        # pass; the policy now weighs occurrences.
        proc = self._run("Write", {"file_path": self._target("mono.md"),
                                    "content": "Very fast. Very light. "
                                                "Very small. Very neat.\n"})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")

    def test_edit_cheat_is_dead_embedded_prose_sees_the_resulting_file(self):
        # A new_string fragment never parses as Python, so the embedded
        # pass judged nothing on Edit -- reconstruct, and it does.
        path = self._put("emb.py", "X = 1\n")
        doc = ('DOC = ("Undoubtedly a seamless, robust, cutting-edge and "\n'
               '       "very powerful module.")\nX = 1\n')
        proc = self._run("Edit", {"file_path": path,
                                    "old_string": "X = 1\n", "new_string": doc})
        decision = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("embedded prose", decision["permissionDecisionReason"])

    def test_config_writes_are_logged_not_silent(self):
        # Self-serve deregulation: the config file is the gate's own
        # control surface. Still allowed -- it is the human's file -- but
        # the event lands in history now.
        proc = self._run("Write", {"file_path": self._target("stopslop.config.json"),
                                    "content": "{}"})
        self.assertEqual(proc.returncode, 0)
        log = os.path.join(self.tmp, ".claude", "stopslop-history.log")
        with open(log) as f:
            self.assertIn("config_write", f.read())


if __name__ == "__main__":
    unittest.main()
