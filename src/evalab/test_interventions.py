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


class CombinedArmTests(unittest.TestCase):
    """Does instruction STACK with enforcement, or compete with it?

    The leaderboard found a clean division of labour: skill files
    generalise (10 to 12 held-out flags) while the gate enforces (8
    enforced flags). Every arm before this one was either/or, so nobody
    had tested both at once -- which is the arm that decides whether this
    project should recommend the hook INSTEAD of a skill file or
    ALONGSIDE one.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def _run(self, combined, names=()):
        chosen = {n: interventions.load(n) for n in names}
        generator = ScriptedGenerator(
            ["Needless to say, this is a seamless and very robust tool.",
             "The cache stores query results on disk."] * 30)
        return harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                            generator, max_iterations=3,
                            instructions=chosen or None, combined=combined)

    def test_a_combined_arm_is_scored_like_any_other(self):
        result = self._run(["instructed"])
        row = result["rows"][0]
        self.assertIn("instructed+gated", row)
        self.assertIn("held_out_per_1k", row["instructed+gated"]["scores"])

    def test_it_runs_the_real_loop_and_can_spend_more_than_one_generation(self):
        """If it generated once it would be an instructed arm wearing the
        gate's name, and the comparison would be meaningless."""
        result = self._run(["instructed"])
        self.assertGreater(result["rows"][0]["instructed+gated"]["iterations"], 1)
        self.assertIn("passed", result["rows"][0]["instructed+gated"])

    def test_the_instruction_leads_the_first_prompt(self):
        generator = ScriptedGenerator(["clean text."] * 30)
        harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                     generator, max_iterations=1, combined=["instructed"])
        prompt = prompts.by_ids(["readme-section"])[0]["text"]
        self.assertTrue(any(m[0]["content"].endswith(prompt)
                             and harness.INSTRUCTION_HEADER in m[0]["content"]
                             for m in generator.seen))

    def test_a_revision_keeps_the_instruction_rather_than_dropping_it(self):
        """A revision that restates the bare prompt would quietly remove
        the very thing this arm is testing, halfway through the loop."""
        generator = ScriptedGenerator(
            ["Needless to say, this is seamless."] * 30)
        harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                     generator, max_iterations=3, combined=["instructed"])
        revisions = [m for m in generator.seen if len(m) == 3]
        self.assertTrue(revisions)
        # The plain gated arm revises in this run too and carries no
        # instruction by design, so the claim is that the combined arm's
        # revisions keep theirs -- not that every revision has one.
        instructed = [m for m in revisions
                       if harness.INSTRUCTION_HEADER in m[0]["content"]]
        self.assertTrue(instructed, "the combined arm dropped its "
                                     "instruction on revision")

    def test_the_plain_gated_arm_still_carries_no_instruction(self):
        """The combined arm is only interpretable against a gate that was
        told nothing."""
        generator = ScriptedGenerator(["clean text."] * 30)
        harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                     generator, max_iterations=1, combined=["instructed"])
        prompt = prompts.by_ids(["readme-section"])[0]["text"]
        self.assertTrue(any(m[0]["content"] == prompt for m in generator.seen))

    def test_a_competitor_can_be_combined_too(self):
        result = self._run(["stop-slop"], names=["stop-slop"])
        self.assertIn("stop-slop+gated", result["rows"][0])

    def test_combining_something_that_never_ran_is_ignored_not_fatal(self):
        result = self._run(["no-such-tool"])
        self.assertEqual(result["combined_arms"], [])

    def test_the_result_names_its_combined_arms(self):
        result = self._run(["instructed"])
        self.assertEqual(result["combined_arms"], ["instructed+gated"])


class ComplementInstructionTests(unittest.TestCase):
    """An instruction built from what the gate does NOT enforce.

    The combined run found the mechanism. A block generated from the
    enforced check table restates what the gate is about to enforce
    anyway and barely stacks with it (23 tells against 30, p = 0.17).
    stop-slop stacks properly (15, p = 0.017) because it names things no
    check here enforces. This arm asks whether the complement of the
    enforced set reproduces that advantage from this project's own table.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def _run(self, **kwargs):
        generator = ScriptedGenerator(
            ["Needless to say, this is a seamless and very robust tool.",
             "The cache stores query results on disk."] * 40)
        return harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                            generator, enforced="structural",
                            max_iterations=3, complement=True, **kwargs)

    def _bullets(self, text):
        return {line[2:].strip() for line in text.splitlines()
                 if line.startswith("- ")}

    def _bullet_for(self, check_id):
        meta = self.ruleset.list_checks()[check_id]
        catches = (meta.get("catches") or "").strip()
        instead = (meta.get("instead") or "").strip()
        return f"{catches} -- {instead}" if catches and instead else (
            catches or instead)

    def test_it_names_only_checks_the_gate_does_not_enforce(self):
        """If it named an enforced check it would be the block that
        already exists, and the experiment would compare a thing to
        itself.

        Compared BULLET BY BULLET, not by substring: solicit_criticism's
        remedy is "cut them", which is a prefix of a held-out check's
        longer line, and a substring test calls that a leak when nothing
        leaked.
        """
        enforced, _ = harness.split_checks(self.ruleset, "structural")
        bullets = self._bullets(self._run()["instructions"]["complement"])
        for check_id in enforced:
            self.assertNotIn(self._bullet_for(check_id), bullets,
                              f"{check_id} leaked into the complement")

    def test_it_asks_for_every_held_out_check(self):
        _, held_out = harness.split_checks(self.ruleset, "structural")
        bullets = self._bullets(self._run()["instructions"]["complement"])
        for check_id in held_out:
            self.assertIn(self._bullet_for(check_id), bullets,
                           f"{check_id} was not asked for")

    def test_it_differs_from_the_enforced_block(self):
        result = self._run()
        self.assertNotEqual(result["instructions"]["complement"],
                             result["instructions"]["instructed"])

    def test_it_can_be_combined_with_the_gate(self):
        row = self._run(combined=["complement"])["rows"][0]
        self.assertIn("complement+gated", row)
        self.assertGreater(row["complement+gated"]["iterations"], 1)

    def test_it_is_absent_unless_asked_for(self):
        """Seven committed runs have no complement arm and their reports
        must keep rendering."""
        generator = ScriptedGenerator(["clean text."] * 20)
        result = harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                              generator, enforced="structural",
                              max_iterations=1)
        self.assertNotIn("complement", result["rows"][0])
