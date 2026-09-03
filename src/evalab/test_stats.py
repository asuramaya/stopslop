#!/usr/bin/env python3
"""The arithmetic behind every p-value this project publishes.

These numbers were computed by hand once and quoted in FINDINGS.md with
no way to recheck them. That is how a wrong number survives: nobody can
falsify what nobody can rerun.
"""
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evalab import stats

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
STRUCTURAL = os.path.join(REPO_ROOT, "evalab-runs", "2026-09-01-structural",
                           "result.json")


def _row(prompt_id, **arms):
    row = {"id": prompt_id}
    for arm, (enforced, held, words) in arms.items():
        row[arm] = {"scores": {"enforced_flags": enforced,
                                "held_out_flags": held,
                                "enforced_per_1k": float(enforced),
                                "held_out_per_1k": float(held),
                                "words": words}}
    return row


class SignTestTests(unittest.TestCase):
    def test_a_clean_sweep_is_significant(self):
        result = stats.sign_test([(0, 5)] * 10)
        self.assertEqual((result["wins"], result["losses"]), (10, 0))
        self.assertLess(result["p"], 0.01)

    def test_an_even_split_is_not(self):
        result = stats.sign_test([(0, 5)] * 5 + [(5, 0)] * 5)
        self.assertAlmostEqual(result["p"], 1.0)

    def test_ties_are_dropped_not_counted_as_wins(self):
        """A tie is not evidence for either arm. Counting it as a win is
        how a null result gets published as a finding."""
        result = stats.sign_test([(3, 3)] * 8 + [(0, 5)] * 2)
        self.assertEqual(result["ties"], 8)
        self.assertEqual((result["wins"], result["losses"]), (2, 0))

    def test_all_ties_cannot_be_significant(self):
        self.assertEqual(stats.sign_test([(1, 1)] * 20)["p"], 1.0)

    def test_it_is_two_sided(self):
        """Same magnitude, opposite direction, same p -- or the test is
        quietly rooting for one arm."""
        a = stats.sign_test([(0, 5)] * 7 + [(5, 0)] * 1)["p"]
        b = stats.sign_test([(5, 0)] * 7 + [(0, 5)] * 1)["p"]
        self.assertAlmostEqual(a, b)


class BootstrapTests(unittest.TestCase):
    def test_the_interval_brackets_the_mean(self):
        pairs = [(1, 4), (2, 5), (0, 3), (1, 6), (2, 4)]
        out = stats.bootstrap(pairs)
        self.assertLessEqual(out["lo"], out["mean"])
        self.assertLessEqual(out["mean"], out["hi"])

    def test_no_difference_leaves_the_interval_straddling_zero(self):
        out = stats.bootstrap([(3, 3)] * 20)
        self.assertEqual(out["mean"], 0.0)
        self.assertLessEqual(out["lo"], 0.0)
        self.assertGreaterEqual(out["hi"], 0.0)

    def test_it_is_deterministic_for_a_seed(self):
        """A CI that moves between two runs of the same data cannot be
        quoted in a findings file."""
        pairs = [(1, 4), (2, 5), (0, 3), (1, 6), (2, 4)]
        self.assertEqual(stats.bootstrap(pairs, seed=7),
                          stats.bootstrap(pairs, seed=7))

    def test_an_empty_comparison_does_not_divide_by_zero(self):
        self.assertEqual(stats.bootstrap([])["mean"], 0.0)


class CompareTests(unittest.TestCase):
    def test_it_pairs_by_prompt_and_totals_both_arms(self):
        rows = [_row("a", gated=(0, 1, 100), blind=(4, 2, 100)),
                 _row("b", gated=(1, 0, 100), blind=(3, 3, 100))]
        out = stats.compare({"rows": rows}, "gated", "blind")
        self.assertEqual(out["n"], 2)
        self.assertEqual(out["total_a"], 2)
        self.assertEqual(out["total_b"], 12)

    def test_a_prompt_missing_an_arm_is_skipped_not_scored_as_zero(self):
        """An older run has no instructed arm. Treating its absence as
        zero flags would hand that arm a perfect score it never earned."""
        rows = [_row("a", gated=(0, 1, 100), blind=(4, 2, 100)),
                 _row("b", gated=(1, 0, 100))]
        out = stats.compare({"rows": rows}, "gated", "blind")
        self.assertEqual(out["n"], 1)

    def test_total_tells_counts_held_out_too(self):
        """The reader does not know which checks the loop was pointed
        at, so the headline metric cannot be enforced-only."""
        row = _row("a", gated=(2, 3, 100))
        self.assertEqual(stats.total_tells(row, "gated"), 5)


class PublishedNumbersTests(unittest.TestCase):
    """The structural run's headline claim, rechecked against its own
    saved result rather than against a transcript."""

    def setUp(self):
        if not os.path.exists(STRUCTURAL):
            self.skipTest("structural run not present")
        with open(STRUCTURAL) as f:
            self.result = json.load(f)

    def test_the_gate_beat_a_blind_rewrite_on_26_of_30_with_none_lost(self):
        out = stats.compare(self.result, "gated", "blind")
        self.assertEqual(out["n"], 30)
        self.assertEqual(out["sign"]["wins"], 26)
        self.assertEqual(out["sign"]["losses"], 0)
        self.assertLess(out["sign"]["p"], 1e-6)

    def test_the_published_totals_are_what_the_saved_run_holds(self):
        out = stats.compare(self.result, "gated", "blind")
        self.assertEqual((out["total_a"], out["total_b"]), (29, 93))


if __name__ == "__main__":
    unittest.main()


class PublishedRunsTests(unittest.TestCase):
    """Every committed run must be usable by a stranger.

    A run directory that cannot be replayed, or whose numbers have no
    findings file behind them, is a directory of JSON rather than
    evidence. This project's whole claim is that its results can be
    checked, so the check is a test.
    """

    def _runs(self):
        base = os.path.join(REPO_ROOT, "evalab-runs")
        return [os.path.join(base, name) for name in sorted(os.listdir(base))
                 if name.startswith("2026-")
                 and os.path.isdir(os.path.join(base, name))]

    def test_every_run_with_results_can_be_replayed_or_says_why(self):
        for path in self._runs():
            if not os.path.exists(os.path.join(path, "result.json")):
                continue
            if os.path.isdir(os.path.join(path, "recordings")):
                continue
            findings = os.path.join(path, "FINDINGS.md")
            self.assertTrue(os.path.exists(findings),
                             f"{os.path.basename(path)} has results, no "
                             "recordings, and no findings explaining why")
            with open(findings) as f:
                text = f.read().lower()
            self.assertIn("recording", text,
                           f"{os.path.basename(path)} cannot be replayed and "
                           "does not say so")

    def test_every_run_directory_leads_a_reader_somewhere(self):
        """A per-model leg has no findings of its own -- the analysis
        pools across legs. Without a pointer it is a dead end."""
        for path in self._runs():
            has = any(os.path.exists(os.path.join(path, name))
                       for name in ("FINDINGS.md", "README.md"))
            self.assertTrue(has, f"{os.path.basename(path)} has neither "
                                  "FINDINGS.md nor a README pointing at one")

    def test_the_index_lists_every_run(self):
        with open(os.path.join(REPO_ROOT, "evalab-runs", "README.md")) as f:
            index = f.read()
        for path in self._runs():
            name = os.path.basename(path)
            listed = name in index or any(
                name.startswith(stem) for stem in
                re.findall(r"`(2026-[0-9a-z-]+)\*/`", index))
            self.assertTrue(listed, f"{name} is not in the runs index")
