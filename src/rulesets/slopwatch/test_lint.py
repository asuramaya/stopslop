#!/usr/bin/env python3
"""Automated tests for rulesets/slopwatch/lint.py -- same stdlib-unittest
structure as rulesets/ste100/test_lint.py, one TestCase per check plus
blocking-policy and integration tests. slopwatch is a demo ruleset built to
prove the plugin contract generalizes; these tests exist for the same
reason ste100's do, not because slopwatch is meant to be a finished product.

Run with:
    cd src && python3 -m unittest rulesets.slopwatch.test_lint -v
"""
import unittest

from rulesets.slopwatch import lint


class FillerOpenerTests(unittest.TestCase):
    def test_known_opener_flags(self):
        hits = lint.check_filler_opener("Needless to say, the migration failed.")
        self.assertEqual(len(hits), 1)
        self.assertFalse(hits[0]["auto_fix"])

    def test_ordinary_sentence_passes(self):
        self.assertEqual(lint.check_filler_opener("The migration failed."), [])

    def test_opener_only_matches_at_sentence_start(self):
        # "needless to say" appearing mid-sentence isn't the throat-clearing
        # opener pattern this check targets.
        hits = lint.check_filler_opener("He said, needless to say, that it failed.")
        self.assertEqual(hits, [])


class StockAdverbTests(unittest.TestCase):
    def test_sentence_initial_adverb_flags_and_autofixes(self):
        hits = lint.check_stock_adverb("Notably, the system failed.")
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["auto_fix"])
        self.assertEqual(hits[0]["word"], "Notably")

    def test_mid_sentence_parenthetical_adverb_flags(self):
        hits = lint.check_stock_adverb("The system, notably, failed.")
        self.assertEqual(len(hits), 1)

    def test_clean_sentence_passes(self):
        self.assertEqual(lint.check_stock_adverb("The system failed."), [])

    def test_autofix_removes_sentence_initial_adverb_and_recapitalizes(self):
        self.assertEqual(lint.fix_sentence("Notably, the system failed."),
                          "The system failed.")

    def test_autofix_removes_mid_sentence_parenthetical_adverb(self):
        self.assertEqual(lint.fix_sentence("The system, notably, failed."),
                          "The system failed.")

    def test_autofix_removes_adverb_before_the(self):
        self.assertEqual(lint.fix_sentence("This is ultimately the best approach."),
                          "This is the best approach.")


class ColonRevealTests(unittest.TestCase):
    def test_short_buildup_reveal_flags(self):
        hits = lint.check_colon_reveal("The best part: it learns on its own.")
        self.assertEqual(len(hits), 1)
        self.assertFalse(hits[0]["auto_fix"])

    def test_regression_genuine_list_label_not_flagged(self):
        # Live regression: "Files needed:" is a genuine label/list intro,
        # not a dramatic reveal -- the original label-word exclusion list
        # didn't cover "needed" and flagged it anyway.
        self.assertEqual(
            lint.check_colon_reveal("Files needed: config.json and settings.yaml."), [])

    def test_recognized_label_word_not_flagged(self):
        self.assertEqual(
            lint.check_colon_reveal("Note: this feature is experimental."), [])

    def test_long_buildup_not_flagged(self):
        # More than 6 words before the colon isn't the short-buildup shape
        # this check targets.
        hits = lint.check_colon_reveal(
            "After a long review of every option the team could think of: nothing changed.")
        self.assertEqual(hits, [])


class WeaselAttributionTests(unittest.TestCase):
    def test_known_phrase_flags(self):
        hits = lint.check_weasel_attribution("Studies show that this approach works better.")
        self.assertEqual(len(hits), 1)

    def test_named_source_not_flagged(self):
        self.assertEqual(
            lint.check_weasel_attribution("A 2023 Stanford study found this approach works better."),
            [])


class BinaryContrastTests(unittest.TestCase):
    def test_classic_pattern_flags(self):
        hits = lint.check_binary_contrast(["This is not a bug.", "It's a feature."])
        self.assertEqual(len(hits), 1)

    def test_regression_still_negative_second_sentence_not_flagged(self):
        # Live regression: "It is also not fixed yet." doesn't match the
        # exact "it is not" prefix regex (there's "also" in between), so it
        # fell through to "affirmative" and was wrongly flagged even though
        # it's still negative in spirit.
        hits = lint.check_binary_contrast(
            ["This is not a bug.", "It is also not fixed yet."])
        self.assertEqual(hits, [])

    def test_unrelated_adjacent_sentences_not_flagged(self):
        hits = lint.check_binary_contrast(
            ["The system started.", "It processed the queue."])
        self.assertEqual(hits, [])


class EmDashClusterTests(unittest.TestCase):
    def test_above_threshold_flags_once(self):
        hits = lint.check_em_dash_cluster("one — two — three — four — five")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["count"], 4)

    def test_at_or_below_threshold_not_flagged(self):
        self.assertEqual(lint.check_em_dash_cluster("one — two — three"), [])
        self.assertEqual(lint.check_em_dash_cluster("one — two"), [])


class BlockingFlagsTests(unittest.TestCase):
    """slopwatch's blocking policy is a count/density threshold, a
    genuinely different shape from ste100's exclusion-list approach -- the
    concrete proof that the plugin contract needs no shared core mechanism
    to support a different deny policy per ruleset."""

    def test_single_flag_does_not_block(self):
        r = lint.lint_and_gate("Needless to say, this matters.")
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), [])

    def test_four_or_more_flags_block(self):
        text = ("Needless to say, this matters. Studies show it works. "
                "The best part: it learns. This is not a bug. It's a feature.")
        r = lint.lint_and_gate(text)
        self.assertGreaterEqual(len(r["semantic_flags"]), 4)
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), r["semantic_flags"])

    def test_em_dash_cluster_alone_blocks(self):
        r = lint.lint_and_gate("one — two — three — four — five plain sentence here.")
        blocking = lint.blocking_semantic_flags(r["semantic_flags"])
        self.assertTrue(any(f["kind"] == "em_dash_cluster" for f in blocking))


class LintAndGateIntegrationTests(unittest.TestCase):
    def test_clean_text_status_clean(self):
        r = lint.lint_and_gate("The system started and processed the queue.")
        self.assertEqual(r["status"], "clean")

    def test_mechanical_only_status(self):
        r = lint.lint_and_gate("Notably, the system started.")
        self.assertEqual(r["status"], "mechanical_violations")

    def test_semantic_flags_status(self):
        r = lint.lint_and_gate("Needless to say, the system started.")
        self.assertEqual(r["status"], "semantic_flags")

    def test_code_fence_not_linted(self):
        doc = "Clean text.\n\n```\nNeedless to say this should not be linted.\n```\n"
        r = lint.lint_and_gate(doc)
        self.assertEqual(r["status"], "clean")

    def test_inline_code_span_not_linted(self):
        doc = "See the note that says `needless to say this is fine`."
        r = lint.lint_and_gate(doc)
        opener_flags = [f for f in r["semantic_flags"] if f["kind"] == "filler_opener"]
        self.assertEqual(opener_flags, [])


if __name__ == "__main__":
    unittest.main()
