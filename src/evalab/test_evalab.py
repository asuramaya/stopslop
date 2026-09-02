#!/usr/bin/env python3
"""Tests for the A/B harness.

The harness is an instrument, so what needs pinning is the properties
that make its output mean anything: the gated arm never sees a held-out
check, the two sets partition the ruleset with nothing dropped, and the
metrics that detect a flattened register actually detect one.

No test here calls a model. ScriptedGenerator supplies the text.
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rulesets
from evalab import harness, metrics, prompts, report
from evalab.generators import (ClaudeCliGenerator, GeneratorError,
                                ResumingGenerator, ScriptedGenerator)


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

    def test_no_prompt_in_any_set_mentions_style_or_a_check_name(self):
        """A prompt that primed either arm would hide the effect being
        measured. Applies to BOTH sets: the padding set is meant to
        invite filler by asking for register rather than content, never
        by naming what the checks catch."""
        ruleset = rulesets.get_ruleset("slopwatch")
        banned = set(ruleset.list_checks()) | {
            "concise", "plain language", "avoid", "do not use"}
        for name, prompt_set in prompts.PROMPT_SETS.items():
            for prompt in prompt_set:
                lowered = prompt["text"].lower()
                for term in banned:
                    self.assertNotIn(term.replace("_", " "), lowered,
                                      f"{name}/{prompt['id']} primes a check")

    def test_ids_are_unique_within_and_across_sets(self):
        """A shared id between sets would make a saved run ambiguous
        about which prompt produced it."""
        seen = [p["id"] for s in prompts.PROMPT_SETS.values() for p in s]
        self.assertEqual(len(seen), len(set(seen)))

    def test_the_padding_set_is_reachable_and_distinct(self):
        technical = {p["id"] for p in prompts.get_set("technical")}
        padding = {p["id"] for p in prompts.get_set("padding")}
        self.assertTrue(padding)
        self.assertEqual(technical & padding, set())

    def test_by_ids_refuses_an_unknown_id(self):
        with self.assertRaises(ValueError):
            prompts.by_ids(["__no_such_prompt__"])

    def test_by_ids_refuses_an_unknown_set(self):
        with self.assertRaises(ValueError):
            prompts.by_ids(None, prompt_set="__no_such_set__")

    def test_an_id_from_the_other_set_is_refused_not_silently_dropped(self):
        with self.assertRaises(ValueError):
            prompts.by_ids(["readme-section"], prompt_set="padding")


class ReportTests(unittest.TestCase):
    def _result(self):
        ruleset = rulesets.get_ruleset("slopwatch")
        text = "The cache stores query results on disk."
        # Four arms: ungated, control, gated, blind. Neither the control
        # nor the blind arm is optional decoration -- see harness.run.
        generator = ScriptedGenerator([text] * 8)
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
        generator = ScriptedGenerator([a, b, a, a, a])
        result = harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                              generator, max_iterations=1)
        row = result["rows"][0]
        self.assertEqual(row["control"]["text"], b)
        # Byte-identical first prompt for the ungated, control and gated
        # arms, or the comparison is between different questions. The
        # instructed arm is the one deliberate exception: it carries the
        # rules the gate would otherwise have delivered as a denial, and
        # it still has to end in the same prompt.
        self.assertEqual(generator.seen[0], generator.seen[1])
        instructed = generator.seen[2][0]["content"]
        self.assertNotEqual(generator.seen[0], generator.seen[2])
        self.assertTrue(instructed.endswith(row["prompt"]))
        self.assertEqual(generator.seen[0], generator.seen[3])

    def test_report_prints_a_noise_floor_next_to_every_gate_delta(self):
        a = "The cache keeps results on disk for an hour."
        generator = ScriptedGenerator([a] * 8)
        result = harness.run(prompts.by_ids(["readme-section"]), self.ruleset,
                              generator, max_iterations=1)
        rendered = report.render(result)
        self.assertIn("noise floor", rendered)
        self.assertIn("rewrite alone", rendered)
        self.assertIn("A gate delta smaller than that is not a finding",
                       rendered)

    def test_report_says_plainly_when_the_loop_never_revised_anything(self):
        """The smoke run that motivated this arm looked like a result and
        was not one: zero enforced flags, so the gated arm never revised
        and the deltas were pure variance. The report must say so instead
        of printing a table that invites the misreading."""
        clean = "The cache keeps results on disk for an hour."
        generator = ScriptedGenerator([clean] * 8)
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


class ReportCountsTests(unittest.TestCase):
    """Run 1's lesson, pinned: a 41% held-out drop was two flags becoming
    one. The report prints absolute totals above every percentage so that
    cannot be read the wrong way twice."""

    def test_report_prints_absolute_totals_per_arm(self):
        ruleset = rulesets.get_ruleset("slopwatch")
        dirty = ("Needless to say, this is a seamless solution. "
                  "Studies show it is very fast.")
        generator = ScriptedGenerator([dirty] * 10)
        result = harness.run(prompts.by_ids(["readme-section"]), ruleset,
                              generator, max_iterations=2)
        rendered = report.render(result)
        self.assertIn("TOTAL FLAGS", rendered)
        self.assertIn("a percentage hides how few these are", rendered)

    def test_report_labels_which_prompt_set_produced_the_numbers(self):
        ruleset = rulesets.get_ruleset("slopwatch")
        text = "The cache stores query results on disk."
        generator = ScriptedGenerator([text] * 8)
        result = harness.run(prompts.by_ids(["launch-announcement"],
                                              prompt_set="padding"),
                              ruleset, generator, max_iterations=1)
        result["prompt_set"] = "padding"
        rendered = report.render(result)
        self.assertIn("not a base rate", rendered)


class BlindRevisionArmTests(unittest.TestCase):
    """Separates "the gate helped" from "the model tried again".

    Reading the 2026-09-01 runbook texts side by side showed the gated
    output was plainly better -- and it had also been generated twice. A
    second pass improves writing on its own, so without a matched-compute
    rewrite to compare against, a quality gain cannot be credited to the
    flags.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_the_blind_revision_prompt_names_no_check_and_no_flag(self):
        every_check = set(self.ruleset.list_checks())
        for check_id in every_check:
            self.assertNotIn(check_id, harness.BLIND_REVISION)
        self.assertNotIn("flag", harness.BLIND_REVISION.lower())

    def test_it_spends_the_same_generations_the_gated_arm_did(self):
        text = "Needless to say, this is a seamless solution."
        generator = ScriptedGenerator([text] * 5)
        arm = harness.run_arm_blind_revision(generator, "write something", 3)
        self.assertEqual(arm["iterations"], 3)
        self.assertEqual(len(generator.seen), 3)

    def test_one_iteration_means_no_rewrite_at_all(self):
        text = "The cache stores query results on disk."
        generator = ScriptedGenerator([text] * 3)
        harness.run_arm_blind_revision(generator, "write something", 1)
        self.assertEqual(len(generator.seen), 1)

    def test_run_matches_the_blind_arm_to_the_gated_arms_own_count(self):
        dirty = "Needless to say, this is a seamless and very robust tool."
        generator = ScriptedGenerator([dirty] * 12)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=3)
        row = result["rows"][0]
        self.assertEqual(row["blind"]["iterations"], row["gated"]["iterations"])


class RevisedOnlyScopeTests(unittest.TestCase):
    """Averaging in prompts the gate never touched can INVENT an effect.

    Run 2 showed an 11% drop in sentence-length variance across all eight
    prompts. It vanished when restricted to the four the loop actually
    revised: on those, the noise floor moved further than the gate did.
    The apparent flattening was variance from prompts where the gated arm
    generated once and was therefore just a third random sample.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_averages_cover_only_the_prompts_the_loop_revised(self):
        rendered = report.render(self._mixed_result())
        self.assertIn("AVERAGES over the 1 prompts the loop revised",
                       rendered)

    def test_totals_show_revised_only_beside_the_whole_corpus(self):
        rendered = report.render(self._mixed_result())
        self.assertIn("revised-only", rendered)

    def test_it_says_so_when_the_loop_revised_nothing(self):
        clean = "The cache stores query results on disk."
        generator = ScriptedGenerator([clean] * 8)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=3)
        rendered = report.render(result)
        self.assertIn("ALL prompts (the loop revised none)", rendered)

    def _mixed_result(self):
        """One prompt the loop revises, one it does not."""
        dirty = "Needless to say, this is a seamless and very robust tool."
        clean = "The cache stores query results on disk."
        # readme-section: ungated, control and instructed take a dirty
        # each, then the gated loop takes dirty -> clean, so it revises
        # once; the blind arm's matched two follow.
        # incident-report: clean throughout, so the loop never fires.
        generator = ScriptedGenerator(
            [dirty] * 4 + [clean] + [dirty, dirty] + [clean] * 8)
        return harness.run(prompts.by_ids(["readme-section",
                                             "incident-report"]),
                            self.ruleset, generator, max_iterations=2)


class WorkerParallelismTests(unittest.TestCase):
    """Running prompts in parallel must not change a single number.

    Thirty prompts serially is about two hours of subprocess latency, so
    the run that answers anything has to be parallel -- and a measurement
    instrument that gives a different answer at a different worker count
    is not one.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")
        self.ids = ["readme-section", "incident-report", "design-note"]

    def _run(self, workers):
        dirty = "Needless to say, this is a seamless and very robust tool."
        clean = "The cache stores query results on disk."
        # Deterministic per call so both runs see the same text; the point
        # is the plumbing, not the model.
        generator = ScriptedGenerator([dirty, clean] * 40)
        return harness.run(prompts.by_ids(self.ids), self.ruleset, generator,
                            max_iterations=2, workers=workers)

    def test_row_order_follows_submission_not_completion(self):
        """A saved result has to read the same however many workers made
        it, or two runs of one experiment are not comparable."""
        serial = [r["id"] for r in self._run(1)["rows"]]
        parallel = [r["id"] for r in self._run(3)["rows"]]
        self.assertEqual(serial, parallel)
        self.assertEqual(serial, self.ids)

    def test_every_prompt_still_gets_all_five_arms(self):
        for row in self._run(3)["rows"]:
            for arm in ("ungated", "control", "gated", "blind", "instructed"):
                self.assertIn(arm, row, f"{row['id']} lost its {arm} arm")

    def test_the_blind_arm_still_matches_its_own_prompts_gated_count(self):
        """The matched-compute guarantee is per prompt. Parallelism must
        not pair a prompt's blind arm with another prompt's iteration
        count."""
        for row in self._run(4)["rows"]:
            self.assertEqual(row["blind"]["iterations"],
                              row["gated"]["iterations"], row["id"])


class InstructedArmTests(unittest.TestCase):
    """The free alternative the gate has to beat.

    Every other arm answers "does the gate beat trying again". This one
    answers the cheaper question three rounds of experiments routed
    around: does the gate beat simply telling the model the rules in the
    prompt, the way a line in CLAUDE.md would?
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_the_instruction_names_every_enforced_check_rule(self):
        """It has to be the STRONGEST form of the alternative. An
        instruction weaker than the denials the gate sends would rig the
        comparison in this project's own favour."""
        enforced, _ = harness.split_checks(self.ruleset)
        text = harness.build_instruction(self.ruleset, enforced)
        table = self.ruleset.list_checks()
        for check_id in enforced:
            instead = (table[check_id].get("instead") or "").strip()
            self.assertTrue(instead, f"{check_id} has no instead line")
            self.assertIn(instead, text, f"{check_id}'s rule went missing")

    def test_the_instruction_leaks_no_held_out_check(self):
        """Held-out checks measure transfer in this arm too. Naming one
        would turn a transfer measurement into instruction-following."""
        enforced, held_out = harness.split_checks(self.ruleset)
        text = harness.build_instruction(self.ruleset, enforced)
        table = self.ruleset.list_checks()
        for check_id in held_out:
            self.assertNotIn(check_id, text)
            instead = (table[check_id].get("instead") or "").strip()
            if instead and not any(
                    instead == (table[e].get("instead") or "").strip()
                    for e in enforced):
                self.assertNotIn(instead, text, f"{check_id}'s rule leaked")

    def test_it_spends_exactly_one_generation(self):
        """The whole point is that it is cheaper than the gate. If it
        ever costs a second call the comparison stops meaning anything."""
        generator = ScriptedGenerator(["some text"] * 4)
        arm = harness.run_arm_instructed(generator, "write something", "RULES\n")
        self.assertEqual(arm["iterations"], 1)
        self.assertEqual(len(generator.seen), 1)

    def test_the_instruction_reaches_the_model_ahead_of_the_prompt(self):
        generator = ScriptedGenerator(["some text"])
        harness.run_arm_instructed(generator, "write a README", "RULES:\n\n")
        sent = generator.seen[0][0]["content"]
        self.assertTrue(sent.startswith("RULES:"))
        self.assertIn("write a README", sent)

    def test_run_records_the_instruction_it_actually_used(self):
        """A result that cannot show its own instruction cannot be
        argued with -- the arm would be an unfalsifiable number."""
        generator = ScriptedGenerator(["The cache stores results."] * 12)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=2)
        self.assertIn("instruction", result)
        self.assertIn(harness.INSTRUCTION_HEADER, result["instruction"])

    def test_the_arm_is_scored_like_every_other(self):
        generator = ScriptedGenerator(["The cache stores results."] * 12)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=2)
        scores = result["rows"][0]["instructed"]["scores"]
        for key in ("enforced_per_1k", "held_out_per_1k", "words"):
            self.assertIn(key, scores)

    def test_the_report_prints_it_beside_the_gate(self):
        generator = ScriptedGenerator(
            ["Needless to say, this is a seamless and very robust tool.",
             "The cache stores query results on disk."] * 12)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=3)
        rendered = report.render(result)
        self.assertIn("TOLD THE RULES", rendered)
        self.assertIn("instructed", rendered)

    def test_an_older_result_without_the_arm_still_renders(self):
        """Four committed runs predate this arm. A report that crashed on
        them would erase the evidence this project already published."""
        generator = ScriptedGenerator(["The cache stores results."] * 12)
        result = harness.run(prompts.by_ids(["readme-section"]),
                              self.ruleset, generator, max_iterations=2)
        for row in result["rows"]:
            del row["instructed"]
        rendered = report.render(result)
        self.assertNotIn("TOLD THE RULES", rendered)


class ResumingGeneratorTests(unittest.TestCase):
    """A transient failure must not cost a whole run.

    The first live structural+instructed run died at call ~258 of 264 --
    `claude` exited 1 with an empty stderr -- and finishing it meant
    paying for the other 257 generations again.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)

    def _messages(self, text):
        return [{"role": "user", "content": text}]

    def test_it_replays_what_is_there_and_generates_what_is_not(self):
        live = ScriptedGenerator(["fresh"])
        recorder = ClaudeCliGenerator(record_to=self.dir)
        recorder._record(self._messages("asked before"), "recorded")
        gen = ResumingGenerator(self.dir, live)
        self.assertEqual(gen(self._messages("asked before")), "recorded")
        self.assertEqual(gen(self._messages("never asked")), "fresh")
        self.assertEqual((gen.replayed, gen.generated), (1, 1))

    def test_what_it_generates_it_records_so_a_second_resume_finds_it(self):
        gen = ResumingGenerator(self.dir, ScriptedGenerator(["fresh"]))
        gen(self._messages("new"))
        again = ResumingGenerator(self.dir, ScriptedGenerator([]))
        self.assertEqual(again(self._messages("new")), "fresh")

    def test_the_same_question_twice_resumes_as_two_separate_answers(self):
        """The control arm asks the ungated arm's exact question again.
        A resume that collapsed them would restore the recording-key bug
        that once reported a noise floor of exactly zero."""
        recorder = ClaudeCliGenerator(record_to=self.dir)
        recorder._record(self._messages("same"), "first")
        recorder._record(self._messages("same"), "second")
        gen = ResumingGenerator(self.dir, ScriptedGenerator([]))
        self.assertEqual(gen(self._messages("same")), "first")
        self.assertEqual(gen(self._messages("same")), "second")

    def test_it_refuses_an_inner_generator_that_also_records(self):
        """Two occurrence counters over one directory disagree, and the
        disagreement would be silent."""
        with self.assertRaises(ValueError):
            ResumingGenerator(self.dir, ClaudeCliGenerator(record_to=self.dir))


class CliRetryTests(unittest.TestCase):
    def test_a_transient_failure_is_retried_before_it_kills_a_run(self):
        gen = ClaudeCliGenerator(attempts=3, backoff=0)
        calls = []

        def flaky(messages):
            calls.append(messages)
            if len(calls) < 3:
                raise GeneratorError("claude exited 1: ")
            return "eventually"

        gen._once = flaky
        self.assertEqual(gen(self._m()), "eventually")
        self.assertEqual(len(calls), 3)

    def test_a_failure_that_never_clears_still_raises(self):
        """Retrying widens the window. It must not hide a broken
        executable behind a run that silently produces nothing."""
        gen = ClaudeCliGenerator(attempts=2, backoff=0)

        def broken(messages):
            raise GeneratorError("could not run 'claude'")

        gen._once = broken
        with self.assertRaises(GeneratorError):
            gen(self._m())

    def _m(self):
        return [{"role": "user", "content": "write something"}]


if __name__ == "__main__":
    unittest.main()


class PromptDeliveryTests(unittest.TestCase):
    """How the prompt reaches the executable.

    The first leaderboard run died on every competitor at once: a skill
    file opens with YAML front matter, and `claude -p ---\\nname: ...`
    reads that as an unknown command-line option. Nothing about the
    prompt's CONTENT should be able to change how it is delivered.
    """

    def test_the_prompt_goes_on_stdin_not_argv(self):
        seen = {}

        class FakeProc:
            returncode = 0
            stdout = "some text"
            stderr = ""

        def fake_run(argv, **kwargs):
            seen["argv"] = argv
            seen["input"] = kwargs.get("input")
            return FakeProc()

        import evalab.generators as gens
        real = gens.subprocess.run
        gens.subprocess.run = fake_run
        try:
            gen = ClaudeCliGenerator(attempts=1, backoff=0)
            gen([{"role": "user", "content": "---\nname: skill\n---\n\nwrite"}])
        finally:
            gens.subprocess.run = real
        self.assertEqual(seen["argv"], ["claude", "-p"])
        self.assertIn("name: skill", seen["input"])
        for arg in seen["argv"]:
            self.assertFalse(arg.startswith("---"))

    def test_a_prompt_opening_with_front_matter_is_delivered_intact(self):
        seen = {}

        class FakeProc:
            returncode = 0
            stdout = "some text"
            stderr = ""

        import evalab.generators as gens
        real = gens.subprocess.run
        gens.subprocess.run = lambda argv, **kw: (
            seen.update(input=kw.get("input")) or FakeProc())
        try:
            gen = ClaudeCliGenerator(attempts=1, backoff=0)
            gen([{"role": "user", "content": "---\nfront: matter\n---"},
                  {"role": "user", "content": "the task"}])
        finally:
            gens.subprocess.run = real
        self.assertTrue(seen["input"].startswith("---"))
        self.assertTrue(seen["input"].endswith("the task"))


class RetractedCalibratedPresetTests(unittest.TestCase):
    """The `calibrated` preset was withdrawn, and this holds it withdrawn.

    It dropped four checks for firing more on human prose than on
    generated prose "across every control". They do not: that verdict
    came from a human control that was mostly CPython docstrings, which
    carry no markdown. Against human MARKDOWN documentation and pre-2022
    encyclopedia prose the same four read no signal, disputed, disputed
    and disputed -- not one condemned.

    Shipping a preset whose membership did not survive its own
    re-measurement would be worse than shipping none.
    """

    def setUp(self):
        self.ruleset = rulesets.get_ruleset("slopwatch")

    def test_the_preset_is_gone(self):
        self.assertNotIn("calibrated", harness.PRESETS)

    def test_no_check_list_claims_they_are_condemned(self):
        self.assertFalse(hasattr(harness, "BACKWARDS_ON_EVERY_CONTROL"))

    def test_the_checks_it_dropped_are_still_enforced(self):
        enforced, _ = harness.split_checks(self.ruleset, "structural")
        for check_id in ("vague_intensifier", "marketing_adjective"):
            self.assertIn(check_id, enforced)

    def test_asking_for_it_fails_loudly_rather_than_silently_falling_back(self):
        """A preset name that quietly resolved to something else would
        make an old command line produce a different experiment without
        saying so."""
        with self.assertRaises(KeyError):
            harness.split_checks(self.ruleset, "calibrated")


class Ste100MeasurabilityTests(unittest.TestCase):
    """The ruleset that does the most work in production, unmeasured
    until now because the harness failed silently.

    ste100 shares no check id with slopwatch, so every slopwatch preset
    intersected it to nothing: the gated arm never revised, and the
    report said "the loop revised 0 of 30 prompts" -- which reads like a
    null result about the gate rather than a broken experiment.
    """

    def setUp(self):
        self.ste100 = rulesets.get_ruleset("ste100")
        self.slopwatch = rulesets.get_ruleset("slopwatch")

    def test_a_preset_naming_none_of_a_rulesets_checks_raises(self):
        with self.assertRaises(harness.EmptyEnforcedSet):
            harness.split_checks(self.ste100, "structural")

    def test_the_refusal_names_what_the_ruleset_actually_has(self):
        """An error that only says 'empty' sends the reader back to the
        source to find out what they could have enforced."""
        with self.assertRaises(harness.EmptyEnforcedSet) as caught:
            harness.split_checks(self.ste100, "lexical")
        self.assertIn("ing_form", str(caught.exception))

    def test_the_ste100_preset_enforces_real_ste100_checks(self):
        enforced, held_out = harness.split_checks(self.ste100, "ste100")
        self.assertTrue(enforced)
        self.assertTrue(held_out)
        self.assertTrue(enforced <= set(self.ste100.list_checks()))

    def test_the_split_still_partitions_the_ruleset(self):
        enforced, held_out = harness.split_checks(self.ste100, "ste100")
        self.assertEqual(enforced | held_out, set(self.ste100.list_checks()))
        self.assertFalse(enforced & held_out)

    def test_the_ste100_preset_is_refused_for_slopwatch(self):
        """Symmetry: pointing ste100's preset at the wrong ruleset must
        fail the same way rather than enforcing a lucky overlap."""
        with self.assertRaises(harness.EmptyEnforcedSet):
            harness.split_checks(self.slopwatch, "ste100")

    def test_an_explicit_empty_set_is_refused_too(self):
        with self.assertRaises(harness.EmptyEnforcedSet):
            harness.split_checks(self.ste100, {"not_a_real_check"})
