#!/usr/bin/env python3
"""Tests for the A/B harness.

The harness is an instrument, so what needs pinning is the properties
that make its output mean anything: the gated arm never sees a held-out
check, the two sets partition the ruleset with nothing dropped, and the
metrics that detect a flattened register actually detect one.

No test here calls a model. ScriptedGenerator supplies the text.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rulesets
from evalab import harness, metrics, prompts, report
from evalab.generators import GeneratorError, ScriptedGenerator


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_enforced_and_held_out_partition_every_check(self):
        enforced, held_out = harness.split_checks(self.ruleset)
        self.assertEqual(enforced | held_out, set(self.ruleset.list_checks()))
        self.assertEqual(enforced & held_out, set())

    def test_a_new_check_lands_in_held_out_rather_than_nowhere(self):
        """A ruleset gaining a check must not silently leave it unscored
        in both arms. Held-out is computed as the complement, so this is
        a property of the split rather than a list someone remembers to
        update."""
        enforced, held_out = harness.split_checks(
            self.ruleset, enforced={"colon_reveal"})
        every = set(self.ruleset.list_checks())
        self.assertEqual(enforced, {"colon_reveal"})
        self.assertEqual(held_out, every - {"colon_reveal"})

    def test_an_enforced_id_the_ruleset_lacks_is_dropped_not_invented(self):
        enforced, held_out = harness.split_checks(
            self.ruleset, enforced={"colon_reveal", "__not_a_check__"})
        self.assertEqual(enforced, {"colon_reveal"})
        self.assertNotIn("__not_a_check__", held_out)


class GatedArmTests(unittest.TestCase):
    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")
        self.enforced, self.held_out = harness.split_checks(self.ruleset)

    def test_the_revision_prompt_never_names_a_held_out_check(self):
        """The load-bearing property of the whole experiment. If a
        held-out check reached the model, its own score would measure
        instruction-following and the run would prove nothing."""
        dirty = ("Needless to say, this is a seamless solution. "
                  "The best part: it just works. Studies show it is very fast.")
        clean = "The cache stores query results on disk. It expires them after an hour."
        generator = ScriptedGenerator([dirty, clean])
        harness.run_arm_gated(generator, "write something", self.ruleset,
                               self.enforced, max_iterations=3)
        revision = generator.seen[-1][-1]["content"]
        for check_id in self.held_out:
            self.assertNotIn(check_id, revision,
                              f"held-out {check_id!r} leaked into the revision")

    def test_a_clean_first_draft_costs_one_generation(self):
        clean = "The cache stores query results on disk. It expires them after an hour."
        generator = ScriptedGenerator([clean])
        arm = harness.run_arm_gated(generator, "write something", self.ruleset,
                                     self.enforced, max_iterations=4)
        self.assertEqual(arm["iterations"], 1)
        self.assertTrue(arm["passed"])

    def test_the_loop_stops_at_the_budget_and_says_it_did_not_pass(self):
        dirty = "Needless to say, this is a seamless and very robust solution."
        generator = ScriptedGenerator([dirty] * 3)
        arm = harness.run_arm_gated(generator, "write something", self.ruleset,
                                     self.enforced, max_iterations=3)
        self.assertEqual(arm["iterations"], 3)
        self.assertFalse(arm["passed"])

    def test_both_arms_start_from_the_identical_prompt(self):
        text = "The cache stores query results on disk."
        generator = ScriptedGenerator([text, text])
        harness.run_arm_ungated(generator, "write something")
        harness.run_arm_gated(generator, "write something", self.ruleset,
                               self.enforced, max_iterations=2)
        self.assertEqual(generator.seen[0], generator.seen[1])


class MetricsTests(unittest.TestCase):
    def test_uniform_sentences_score_a_lower_stdev_than_varied_ones(self):
        """The monotone detector, on the shape it exists to catch."""
        monotone = ("The gate reads the text. It finds a problem. It stops "
                     "the write. It shows the flag. The user makes a fix.")
        varied = ("The gate reads the text. When it finds something it "
                   "cannot resolve on its own, and that happens more often "
                   "than the docs admit, it stops the write and hands back a "
                   "list. You fix it.")
        self.assertLess(metrics.sentence_length_stats(monotone)["stdev"],
                         metrics.sentence_length_stats(varied)["stdev"])

    def test_repetition_lowers_the_type_token_ratio(self):
        repetitive = "the cache stores the cache stores the cache stores data"
        varied = "the cache keeps recent query results on local disk storage"
        self.assertLess(metrics.type_token_ratio(repetitive),
                         metrics.type_token_ratio(varied))

    def test_flags_per_1k_is_length_normalized(self):
        """A gated arm may answer more briefly. A raw count would read
        that as an improvement, so the rate is what gets compared."""
        kinds = ["colon_reveal"] * 2
        short = " ".join(["word"] * 100)
        long = " ".join(["word"] * 1000)
        self.assertAlmostEqual(metrics.flags_per_1k(kinds, short), 20.0)
        self.assertAlmostEqual(metrics.flags_per_1k(kinds, long), 2.0)

    def test_code_fences_do_not_count_as_prose_sentences(self):
        text = "Run the tool.\n\n```\nx = 1. y = 2. z = 3.\n```\n\nIt finishes."
        self.assertEqual(len(metrics.prose_sentences(text)), 2)

    def test_empty_text_does_not_divide_by_zero(self):
        self.assertEqual(metrics.flags_per_1k(["colon_reveal"], ""), 0.0)
        self.assertEqual(metrics.type_token_ratio(""), 0.0)
        self.assertEqual(metrics.shape("")["sentences"], 0)


class PromptSetTests(unittest.TestCase):
    def test_ids_are_unique(self):
        ids = [p["id"] for p in prompts.PROMPTS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_prompt_mentions_style_or_a_check_name(self):
        """A prompt that primed either arm would hide the effect being
        measured."""
        ruleset = rulesets.get_ruleset("slopwatch")
        banned = set(ruleset.list_checks()) | {
            "concise", "plain language", "avoid", "do not use"}
        for prompt in prompts.PROMPTS:
            lowered = prompt["text"].lower()
            for term in banned:
                self.assertNotIn(term.replace("_", " "), lowered)

    def test_by_ids_refuses_an_unknown_id(self):
        with self.assertRaises(ValueError):
            prompts.by_ids(["__no_such_prompt__"])


class ReportTests(unittest.TestCase):
    def _result(self):
        ruleset = rulesets.get_ruleset("slopwatch")
        text = "The cache stores query results on disk."
        # Three: ungated, control, gated. The control arm is not optional
        # decoration -- see harness.run.
        generator = ScriptedGenerator([text, text, text])
        return harness.run(prompts.by_ids(["readme-section"]), ruleset,
                            generator, max_iterations=1)

    def test_render_names_the_held_out_reading_rule(self):
        rendered = report.render(self._result())
        self.assertIn("HELD-OUT", rendered)
        self.assertIn("Enforced flags falling proves nothing on its own",
                       rendered)

    def test_render_records_which_generator_produced_the_text(self):
        self.assertIn("scripted", report.render(self._result()))


class RecordedGeneratorTests(unittest.TestCase):
    def test_a_missing_recording_raises_rather_than_inventing_text(self):
        from evalab.generators import RecordedGenerator
        generator = RecordedGenerator("/nonexistent/recordings")
        with self.assertRaises(GeneratorError):
            generator([{"role": "user", "content": "anything"}])


class ControlArmTests(unittest.TestCase):
    """The control arm is what separates a finding from sampling noise."""

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_run_produces_a_control_arm_from_the_same_prompt(self):
        a = "The cache keeps results on disk for an hour."
        b = "Results live on local disk until they expire."
        generator = ScriptedGenerator([a, b, a])
        result = harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                              generator, max_iterations=1)
        row = result["rows"][0]
        self.assertEqual(row["control"]["text"], b)
        # Same first prompt for all three arms, or the comparison is
        # between different questions.
        self.assertEqual(generator.seen[0], generator.seen[1])
        self.assertEqual(generator.seen[1], generator.seen[2])

    def test_report_prints_a_noise_floor_next_to_every_gate_delta(self):
        a = "The cache keeps results on disk for an hour."
        generator = ScriptedGenerator([a, a, a])
        result = harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                              generator, max_iterations=1)
        rendered = report.render(result)
        self.assertIn("noise floor", rendered)
        self.assertIn("A gate delta smaller than that is not a finding",
                       rendered)

    def test_report_says_plainly_when_the_loop_never_revised_anything(self):
        """The smoke run that motivated this arm looked like a result and
        was not one: zero enforced flags, so the gated arm never revised
        and the deltas were pure variance. The report must say so instead
        of printing a table that invites the misreading."""
        clean = "The cache keeps results on disk for an hour."
        generator = ScriptedGenerator([clean, clean, clean])
        result = harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                              generator, max_iterations=3)
        rendered = report.render(result)
        self.assertIn("REVISED 0 OF 1", rendered)
        self.assertIn("measures nothing but", rendered)


class RecordingKeyTests(unittest.TestCase):
    """Regression: replay used to collapse the control arm into the
    ungated arm.

    Both send the identical message list, by design -- that is what makes
    the control a second independent sample. The recording key was the
    message hash alone, so the second call read back the first call's
    answer, a replayed run reported a noise floor of exactly 0.00, and
    every gate delta looked significant against it. Found by replaying a
    real recorded run rather than by reading the code.
    """

    def test_the_same_messages_asked_twice_get_two_recordings(self):
        import json as _json
        import tempfile
        from evalab.generators import RecordedGenerator, _key
        messages = [{"role": "user", "content": "write something"}]
        with tempfile.TemporaryDirectory() as tmp:
            for occurrence, text in enumerate(["first sample", "second sample"]):
                with open(os.path.join(tmp, _key(messages, occurrence) + ".json"),
                           "w") as f:
                    _json.dump({"messages": messages, "output": text}, f)
            generator = RecordedGenerator(tmp)
            self.assertEqual(generator(messages), "first sample")
            self.assertEqual(generator(messages), "second sample")

    def test_replaying_more_calls_than_were_recorded_raises(self):
        import json as _json
        import tempfile
        from evalab.generators import RecordedGenerator, _key
        messages = [{"role": "user", "content": "write something"}]
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, _key(messages, 0) + ".json"), "w") as f:
                _json.dump({"messages": messages, "output": "only sample"}, f)
            generator = RecordedGenerator(tmp)
            generator(messages)
            with self.assertRaises(GeneratorError):
                generator(messages)


if __name__ == "__main__":
    unittest.main()
