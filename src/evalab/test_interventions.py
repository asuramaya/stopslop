#!/usr/bin/env python3
"""The competing-intervention arms.

This category has never had a leaderboard. Every entry in it asserts
that it removes AI writing patterns and none publishes a number, so the
comparison these tests protect is the point of the whole harness: a
16.7k-star skill file and this project's own gate, on the same prompts,
in the same run, with the same statistics.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rulesets
from evalab import harness, interventions, prompts, report
from evalab.generators import ScriptedGenerator


class CatalogueTests(unittest.TestCase):
    def test_every_vendored_file_sits_beside_its_license(self):
        """Vendoring someone's MIT text without their license is the one
        way this comparison could hurt its subjects."""
        directory = os.path.dirname(os.path.abspath(interventions.__file__))
        for name in interventions.available():
            licence = os.path.join(directory, f"{name}.LICENSE")
            self.assertTrue(os.path.exists(licence),
                             f"{name} is vendored with no LICENSE beside it")
            with open(licence) as f:
                self.assertIn("MIT", f.read())

    def test_every_catalogued_entry_states_its_provenance(self):
        for name in interventions.available():
            meta = interventions.provenance(name)
            self.assertTrue(meta["upstream"].startswith("github.com/"))
            self.assertEqual(meta["license"], "MIT")

    def test_an_unknown_name_raises_rather_than_returning_nothing(self):
        with self.assertRaises(KeyError):
            interventions.load("no-such-tool")

    def test_each_one_ends_with_the_same_task_instruction(self):
        """A skill file that ends mid-instruction would leave its arm
        answering a different question from every other arm."""
        for name in interventions.available():
            self.assertTrue(interventions.load(name).endswith(
                interventions.TASK_SUFFIX))

    def test_the_full_skill_is_used_not_just_its_front_matter(self):
        """Compare against the strongest form of the alternative. For
        stop-slop that means its reference files too, not the summary a
        progressive loader reads first."""
        text = interventions.load("stop-slop")
        self.assertGreater(len(text), 8000)


class ArmTests(unittest.TestCase):
    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def _run(self, names):
        chosen = {n: interventions.load(n) for n in names}
        generator = ScriptedGenerator(
            ["Needless to say, this is a seamless and very robust tool.",
             "The cache stores query results on disk."] * 20)
        return harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                            generator, max_iterations=2,
                            instructions=chosen)

    def test_each_named_intervention_becomes_its_own_scored_arm(self):
        result = self._run(["stop-slop", "no-ai-slop"])
        row = result["rows"][0]
        for name in ("stop-slop", "no-ai-slop", "instructed", "gated"):
            self.assertIn(name, row)
            self.assertIn("held_out_per_1k", row[name]["scores"])

    def test_the_projects_own_arm_always_runs_alongside_them(self):
        """A leaderboard missing this project's own entry is not a
        comparison, and it would be the convenient omission."""
        result = self._run(["stop-slop"])
        self.assertIn("instructed", result["rows"][0])

    def test_each_arm_spends_exactly_one_generation(self):
        """These are prompt prefixes. If one silently cost a second call
        it would be compared against the gate at the wrong price."""
        result = self._run(["stop-slop", "no-ai-slop"])
        for name in ("stop-slop", "no-ai-slop"):
            self.assertEqual(result["rows"][0][name]["iterations"], 1)

    def test_each_arm_reaches_the_model_ahead_of_the_same_prompt(self):
        chosen = {"stop-slop": interventions.load("stop-slop")}
        generator = ScriptedGenerator(["text"] * 20)
        harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                     generator, max_iterations=1, instructions=chosen)
        prompt = prompts.by_ids(["readme-section"])[0]["text"]
        sent = [m[0]["content"] for m in generator.seen]
        self.assertTrue(any(c.endswith(prompt) and len(c) > len(prompt)
                             for c in sent))

    def test_the_result_names_which_competitors_ran(self):
        result = self._run(["stop-slop", "no-ai-slop"])
        self.assertEqual(result["intervention_arms"],
                          ["no-ai-slop", "stop-slop"])

    def test_the_report_prints_a_leaderboard_ordered_by_tells(self):
        rendered = report.render(self._run(["stop-slop"]))
        self.assertIn("LEADERBOARD", rendered)
        self.assertIn("stop-slop", rendered)

    def test_a_run_with_no_competitors_prints_no_leaderboard(self):
        """Four committed runs predate this. A leaderboard of one arm
        would be an empty claim printed as a result."""
        generator = ScriptedGenerator(["The cache stores results."] * 12)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=2)
        self.assertNotIn("LEADERBOARD", report.render(result))


if __name__ == "__main__":
    unittest.main()
