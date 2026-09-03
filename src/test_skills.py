#!/usr/bin/env python3
"""The shipped skills.

`.claude/skills/slopwatch/SKILL.md` is this project's own free half --
the instruction block, packaged the way the rest of the category ships.
It is generated from the check table, so it goes stale the moment a
check is added, renamed or switched off, and a stale skill asks a model
for something nothing here enforces.
"""
import os
import re
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rulesets
from core import paths as core_paths

REPO_ROOT = core_paths.find_project_root(__file__)
SKILLS = os.path.join(REPO_ROOT, ".claude", "skills")


def _rules(path):
    with open(path) as f:
        text = f.read()
    return {line[2:].strip() for line in text.splitlines()
             if line.startswith("- ")}


class SlopwatchSkillTests(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(SKILLS, "slopwatch", "SKILL.md")
        if not os.path.exists(self.path):
            self.skipTest("slopwatch skill not present")
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_it_asks_for_exactly_what_the_ruleset_enforces(self):
        """A skill naming a check that no longer exists asks a model for
        something nothing here enforces, and nothing would ever say so."""
        table = self.ruleset.list_checks()
        shipped = _rules(self.path)
        for check_id, meta in table.items():
            if not meta.get("enabled", True):
                continue
            instead = (meta.get("instead") or "").strip()
            if not instead:
                continue
            self.assertTrue(
                any(instead in rule for rule in shipped),
                f"{check_id} is enabled but the skill does not ask for it -- "
                f"regenerate with `stopslop.py rules --ruleset slopwatch`")

    def test_it_asks_for_nothing_the_ruleset_has_switched_off(self):
        table = self.ruleset.list_checks()
        shipped = " ".join(_rules(self.path))
        for check_id, meta in table.items():
            if meta.get("enabled", True):
                continue
            instead = (meta.get("instead") or "").strip()
            if instead and not any(
                    instead == (m.get("instead") or "").strip()
                    for cid, m in table.items()
                    if cid != check_id and m.get("enabled", True)):
                self.assertNotIn(instead, shipped)

    def test_it_carries_its_own_regeneration_command(self):
        with open(self.path) as f:
            self.assertIn("stopslop.py rules --ruleset slopwatch", f.read())

    def test_it_says_what_it_is_worth_rather_than_asserting_it_works(self):
        """Every competing skill file asserts. This one has numbers and
        must keep them, including the one that favours the competition."""
        with open(self.path) as f:
            text = f.read()
        self.assertIn("p = 0.84", text)
        self.assertIn("107 to 60", text)

    def test_it_tells_a_gate_user_to_regenerate_with_the_complement(self):
        """The shipped block repeats what the gate already enforces,
        which measurement says barely helps (26 against 30, p = 0.17).
        A user who installs both and never hears about --complement gets
        the arm that does not stack, from the file they trusted."""
        with open(self.path) as f:
            text = f.read()
        self.assertIn("--complement", text)
        self.assertIn("0.0007", text)

    def test_it_cites_a_findings_file_that_exists(self):
        """A skill quoting numbers with no reachable source is an
        assertion wearing evidence's clothes -- which is the thing this
        project says every other skill file does."""
        with open(self.path) as f:
            text = f.read()
        cited = re.findall(r"evalab-runs/[\w.-]+/FINDINGS\.md", text)
        self.assertTrue(cited, "the skill cites no findings file")
        for rel in cited:
            self.assertTrue(os.path.exists(os.path.join(REPO_ROOT, rel)),
                             f"{rel} does not exist")

    def test_it_names_the_frontmatter_a_loader_needs(self):
        with open(self.path) as f:
            head = f.read(400)
        self.assertTrue(head.startswith("---"))
        # Inline (?m), not a flags argument: assertRegex's third
        # positional is `msg`, so re.MULTILINE would silently become the
        # failure message and the anchor would never match.
        self.assertRegex(head, r"(?m)^name:\s*slopwatch")
        self.assertIn("description:", head)

    def test_it_does_not_recommend_itself_for_procedural_text(self):
        """ste100 wants the opposite register. A skill that grabs a
        runbook would make that file worse."""
        with open(self.path) as f:
            text = f.read()
        self.assertIn("ste100", text)


class EverySkillTests(unittest.TestCase):
    def test_every_shipped_skill_passes_this_project_s_own_gate(self):
        if not os.path.isdir(SKILLS):
            self.skipTest("no skills directory")
        for name in sorted(os.listdir(SKILLS)):
            path = os.path.join(SKILLS, name, "SKILL.md")
            if not os.path.exists(path):
                continue
            proc = subprocess.run(
                [sys.executable, os.path.join(REPO_ROOT, "stopslop.py"),
                 "scan", path], capture_output=True, text=True, cwd=REPO_ROOT)
            self.assertEqual(proc.returncode, 0,
                              f"{name} would fail a live write:\n{proc.stdout}")


if __name__ == "__main__":
    unittest.main()
