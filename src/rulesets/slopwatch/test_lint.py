#!/usr/bin/env python3
"""Automated tests for rulesets/slopwatch/lint.py -- same stdlib-unittest
structure as rulesets/ste100/test_lint.py, one TestCase per check plus
blocking-policy and integration tests. slopwatch is a demo ruleset built to
prove the plugin contract generalizes; these tests exist for the same
reason ste100's do, not because slopwatch is meant to be a finished product.

Run with:
    cd src && python3 -m unittest rulesets.slopwatch.test_lint -v
"""
import os
import tempfile
import unittest

from core import terms as _terms
from rulesets import slopwatch
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

    def test_markdown_bold_label_not_flagged(self):
        # Live regression: a spec/glossary-style bold lead ("**Manufacturing
        # processes**: a) Remove material...") was denying real writes to
        # docs/ASD-STE100-rules-extracted.md -- found via stopslop.py scan
        # against this project's own real reference doc, not a fixture.
        self.assertEqual(
            lint.check_colon_reveal("**Manufacturing processes**: a) Remove material."), [])

    def test_bullet_prefixed_bold_label_not_flagged(self):
        self.assertEqual(
            lint.check_colon_reveal("— **(c)**: same category-membership judgment."), [])

    def test_bold_span_containing_the_colon_not_flagged(self):
        self.assertEqual(
            lint.check_colon_reveal("**3.2 Use only these forms/tenses: infinitive, imperative.**"), [])

    def test_numbered_method_label_not_flagged(self):
        self.assertEqual(
            lint.check_colon_reveal("Method 2: hyphenate word groups that function as one unit."), [])

    def test_spelled_out_step_label_not_flagged(self):
        self.assertEqual(
            lint.check_colon_reveal("Step one: the team checked the file first."), [])

    def test_metadata_field_labels_not_flagged(self):
        for sentence in ("Source: PDF pages 43 to 147.",
                          "Date: 2026-08-01.",
                          "Incident: gate bypass during extraction.",
                          "Checkability legend: (a) deterministic, (b) heuristic."):
            with self.subTest(sentence=sentence):
                self.assertEqual(lint.check_colon_reveal(sentence), [])

    def test_dramatic_reveal_with_bold_word_inline_still_flags(self):
        # The bold-label exemption only applies when the bold span starts
        # (at most a bullet/dash away from) the beginning of the buildup --
        # a real reveal that merely bolds one word for emphasis must still
        # flag, or the exemption would swallow genuine hits too.
        hits = lint.check_colon_reveal("The **real** issue: nobody noticed.")
        self.assertEqual(len(hits), 1)


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
    """The check itself no longer gates on a threshold -- it reports the
    raw count unconditionally, and whether that's enough to actually
    TRIGGER (and whether triggering denies a write) is
    blocking_semantic_flags's job now, against this check's own
    configured {threshold, action}. See CheckToggleAndOptionsTests for
    the threshold/action behavior itself."""

    def test_reports_raw_count(self):
        hits = lint.check_em_dash_cluster("one — two — three — four — five")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["count"], 4)
        self.assertEqual(hits[0]["occurrences"], 4)

    def test_a_single_em_dash_still_reports(self):
        hits = lint.check_em_dash_cluster("one — two")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["count"], 1)

    def test_no_em_dash_reports_nothing(self):
        self.assertEqual(lint.check_em_dash_cluster("one two three"), [])


class EntityEncodedPunctuationTests(unittest.TestCase):
    def test_entity_em_dash_flags_and_autofixes(self):
        hits = lint.check_entity_encoded_punctuation("The system starts&mdash;then stops.")
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["auto_fix"])
        self.assertEqual(lint.fix_sentence("The system starts&mdash;then stops."),
                          "The system starts—then stops.")

    def test_numeric_entity_forms_also_flag(self):
        self.assertEqual(len(lint.check_entity_encoded_punctuation("a&#8212;b")), 1)
        self.assertEqual(len(lint.check_entity_encoded_punctuation("a&#x2014;b")), 1)

    def test_entity_middot_autofixes_to_comma(self):
        self.assertEqual(lint.fix_sentence("cats&middot;dogs&middot;birds"), "Cats,dogs,birds")

    def test_plain_dash_not_flagged(self):
        self.assertEqual(lint.check_entity_encoded_punctuation("The system—then stops."), [])


class BoldBulletLeadTests(unittest.TestCase):
    def test_bold_word_tag_with_no_terminal_punctuation_flags(self):
        hits = lint.check_bold_bullet_lead("- **Fast** the service starts in under a second.")
        self.assertEqual(len(hits), 1)

    def test_bold_label_ending_in_colon_not_flagged(self):
        # Deslopper's own distinction: a bold run that CLOSES on the label
        # ("**Latency:**") names a real inline term, not a per-item tag.
        self.assertEqual(
            lint.check_bold_bullet_lead("- **Latency:** stays low under load."), [])

    def test_non_list_item_not_flagged(self):
        self.assertEqual(lint.check_bold_bullet_lead("**Fast** is not a list item."), [])


class IdLabelLeadTests(unittest.TestCase):
    def test_id_tag_followed_by_capitalized_text_flags(self):
        hits = lint.check_id_label_lead("- R-1. The system must start within five seconds.")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["phrase"], "R-1")

    def test_plain_numbered_item_not_flagged(self):
        self.assertEqual(lint.check_id_label_lead("1. The system starts."), [])


class NotJustXButYTests(unittest.TestCase):
    def test_pattern_flags(self):
        hits = lint.check_not_just_but("This is not just fast but also reliable.")
        self.assertEqual(len(hits), 1)

    def test_ordinary_sentence_not_flagged(self):
        self.assertEqual(lint.check_not_just_but("This is fast and reliable."), [])


class VagueIntensifierTests(unittest.TestCase):
    def test_known_word_flags(self):
        hits = lint.check_vague_intensifier("The system is very fast at startup.")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["word"], "very")

    def test_intensifier_with_a_number_still_flags(self):
        # The check targets the word itself, not whether a number is
        # present elsewhere -- "significantly, by 40%" still reads as
        # padding since "significantly" adds nothing the number doesn't.
        hits = lint.check_vague_intensifier("Latency dropped significantly, by 40%.")
        self.assertEqual(len(hits), 1)

    def test_ordinary_sentence_not_flagged(self):
        self.assertEqual(lint.check_vague_intensifier("The system is fast."), [])


class EmojiInProseTests(unittest.TestCase):
    def test_emoji_flags_and_autofixes(self):
        hits = lint.check_emoji("The system starts \U0001F680 and runs fine.")
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["auto_fix"])
        self.assertEqual(lint.fix_sentence("The system starts \U0001F680 and runs fine."),
                          "The system starts and runs fine.")

    def test_checkmark_flags(self):
        self.assertEqual(len(lint.check_emoji("Done ✅")), 1)

    def test_plain_text_not_flagged(self):
        self.assertEqual(lint.check_emoji("The system starts and runs fine."), [])


class MarketingAdjectiveTests(unittest.TestCase):
    def test_known_word_flags(self):
        hits = lint.check_marketing_adjective("Our seamless integration handles everything.")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["word"], "seamless")

    def test_ordinary_sentence_not_flagged(self):
        self.assertEqual(lint.check_marketing_adjective("The integration handles retries."), [])


class FillerVerbTests(unittest.TestCase):
    def test_known_verb_flags(self):
        hits = lint.check_filler_verb("This feature leverages the existing cache layer.")
        self.assertEqual(len(hits), 1)

    def test_delve_alone_not_flagged(self):
        # "delve" the plain approved verb, no "into"/"deeper" collocation.
        self.assertEqual(lint.check_filler_verb("The archivist chose to delve no further today."), [])

    def test_delve_into_flags(self):
        hits = lint.check_filler_verb("Let's delve into the configuration options available.")
        self.assertEqual(len(hits), 1)


class MarketingClicheTests(unittest.TestCase):
    def test_known_phrase_flags(self):
        hits = lint.check_marketing_cliche("Without further ado, the system starts now.")
        self.assertEqual(len(hits), 1)

    def test_ordinary_sentence_not_flagged(self):
        self.assertEqual(lint.check_marketing_cliche("The system starts now."), [])


class SolicitCriticismTests(unittest.TestCase):
    def test_known_phrase_flags(self):
        hits = lint.check_solicit_criticism("Would love your feedback on this proposal.")
        self.assertEqual(len(hits), 1)

    def test_ordinary_sentence_not_flagged(self):
        self.assertEqual(lint.check_solicit_criticism("Send feedback to the team channel."), [])


class UnearnedProfundityTests(unittest.TestCase):
    def test_known_phrase_flags(self):
        hits = lint.check_unearned_profundity("Everything changed.")
        self.assertEqual(len(hits), 1)

    def test_concrete_sentence_not_flagged(self):
        self.assertEqual(
            lint.check_unearned_profundity("We switched from REST to gRPC."), [])


class DramaticFragmentationTests(unittest.TestCase):
    def test_known_fragment_flags(self):
        hits = lint.check_dramatic_fragmentation("That's it.")
        self.assertEqual(len(hits), 1)

    def test_ordinary_short_sentence_not_flagged(self):
        self.assertEqual(lint.check_dramatic_fragmentation("The cache cleared."), [])


class CannedQuestionAnswerTests(unittest.TestCase):
    def test_short_question_then_canned_answer_flags(self):
        hits = lint.check_canned_question_answer(
            ["The solution?", "It is simpler than you might think."])
        self.assertEqual(len(hits), 1)

    def test_long_question_not_flagged(self):
        hits = lint.check_canned_question_answer(
            ["What is the actual root cause of this particular failure?",
             "It is a race condition."])
        self.assertEqual(hits, [])

    def test_question_without_canned_answer_opener_not_flagged(self):
        hits = lint.check_canned_question_answer(
            ["Is it fast?", "Benchmarks show sub-millisecond latency."])
        self.assertEqual(hits, [])


class NegativeListingTests(unittest.TestCase):
    def test_two_consecutive_negatives_flag(self):
        hits = lint.check_negative_listing(
            ["Not a bug.", "Not a feature.", "A genuine surprise."])
        self.assertEqual(len(hits), 1)

    def test_single_negative_not_flagged(self):
        hits = lint.check_negative_listing(["Not a bug.", "A feature request."])
        self.assertEqual(hits, [])


class BlockingFlagsTests(unittest.TestCase):
    """slopwatch's blocking policy is a count/density threshold, a
    genuinely different shape from ste100's exclusion-list approach -- the
    concrete proof that the plugin contract needs no shared core mechanism
    to support a different deny policy per ruleset."""

    def test_single_flag_does_not_block(self):
        r = lint.lint_and_gate("Needless to say, this matters.")
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), [])

    def test_many_different_warn_checks_together_still_do_not_block(self):
        # The old shared aggregate ("N flags total, from ANY checks,
        # denies") is retired -- each check's own {threshold, action}
        # decides now, independently. A document full of different
        # one-off "warn" tics still passes, by design: see
        # CheckToggleAndOptionsTests for turning a specific check to
        # "block" instead.
        text = ("Needless to say, this matters. Studies show it works. "
                "The best part: it learns. This is not a bug. It's a feature.")
        r = lint.lint_and_gate(text)
        self.assertGreaterEqual(len(r["semantic_flags"]), 4)
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), [])

    def test_em_dash_cluster_is_reported_but_never_blocks_on_its_own(self):
        """slopwatch blocks nothing by default, and this check is why the
        rule is worth pinning: it used to be the one exception. Every check
        here detects a TELL, a surface correlate of empty writing. Text
        that dodges all of them and says nothing still passes, so blocking
        on one only teaches a writer to iterate until the checker goes
        quiet. The flag still fires -- a person reads it and judges."""
        r = lint.lint_and_gate("one — two — three — four — five plain sentence here.")
        self.assertTrue(any(f["kind"] == "em_dash_cluster" for f in r["semantic_flags"]))
        self.assertEqual(lint.blocking_semantic_flags(r["semantic_flags"]), [])


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

    def test_bold_bullet_lead_reachable_through_lint_and_gate(self):
        doc = "- **Fast** the service starts in under a second."
        r = lint.lint_and_gate(doc)
        self.assertTrue(any(f["kind"] == "bold_bullet_lead" for f in r["semantic_flags"]))

    def test_id_label_lead_reachable_through_lint_and_gate(self):
        doc = "- R-1. The system must start within five seconds."
        r = lint.lint_and_gate(doc)
        self.assertTrue(any(f["kind"] == "id_label_lead" for f in r["semantic_flags"]))


class CheckToggleAndOptionsTests(unittest.TestCase):
    """Isolated against a temp project root (same technique
    rulesets/ste100/test_glossary_packs.py's PackEnableDisableTests uses)
    so this never touches the real repo's own stopslop.config.json."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = lint._paths.find_project_root
        lint._paths.find_project_root = lambda _file: self._tmp.name

    def tearDown(self):
        lint._paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_every_check_enabled_by_default(self):
        checks = slopwatch.list_checks()
        self.assertEqual(set(checks), lint.ALL_CHECK_IDS)
        self.assertTrue(all(c["enabled"] for c in checks.values()))

    def test_disabling_a_check_removes_its_flags_from_lint_and_gate(self):
        text = "Undoubtedly, this is great."
        self.assertTrue(any(f["kind"] == "stock_adverb"
                             for f in lint.lint_and_gate(text)["mechanical_violations"]))
        slopwatch.set_enabled_checks(lint.ALL_CHECK_IDS - {"stock_adverb"})
        self.assertFalse(any(f["kind"] == "stock_adverb"
                              for f in lint.lint_and_gate(text)["mechanical_violations"]))

    def test_disabling_a_mechanical_check_stops_its_own_autofix(self):
        # Regression guard: a disabled check's fix must not silently keep
        # rewriting text its own flag no longer appears for -- verified
        # live before this test existed, see the slopwatch modularity work.
        text = "Undoubtedly, this is great."
        self.assertEqual(lint.apply_mechanical_fixes(text), "This is great.")
        slopwatch.set_enabled_checks(lint.ALL_CHECK_IDS - {"stock_adverb"})
        self.assertEqual(lint.apply_mechanical_fixes(text), text)

    def test_unknown_check_id_raises_and_does_not_write(self):
        with self.assertRaises(ValueError):
            slopwatch.set_enabled_checks(["__not_a_real_check__"])
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_default_check_config_before_any_override(self):
        cfg = slopwatch.list_check_config()
        self.assertEqual(cfg["em_dash_cluster"],
                          {"threshold": 4, "action": "warn",
                           "default_threshold": 4, "default_action": "warn"})
        self.assertEqual(cfg["vague_intensifier"],
                          {"threshold": 1, "action": "warn",
                           "default_threshold": 1, "default_action": "warn"})

    def test_action_override_changes_blocking_semantic_flags(self):
        flags = [{"kind": "vague_intensifier", "label": f"w{i}", "detail": {}, "text": ""}
                  for i in range(3)]
        self.assertEqual(lint.blocking_semantic_flags(flags), [])  # default action=warn
        slopwatch.set_check_config("vague_intensifier", threshold=3, action="block")
        self.assertEqual(len(lint.blocking_semantic_flags(flags)), 3)

    def test_threshold_override_changes_when_a_check_fires(self):
        flags = [{"kind": "em_dash_cluster", "label": None,
                  "detail": {"occurrences": 2}, "text": None}]
        self.assertEqual(lint.blocking_semantic_flags(flags), [])  # 2 < default threshold 4
        # action too: this check warns by default now, so a threshold
        # change alone can never make it block.
        slopwatch.set_check_config("em_dash_cluster", threshold=2, action="block")
        self.assertEqual(len(lint.blocking_semantic_flags(flags)), 1)

    def test_unknown_check_id_in_set_check_config_raises_and_does_not_write(self):
        with self.assertRaises(ValueError):
            slopwatch.set_check_config("__not_a_real_check__", threshold=1)
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_invalid_threshold_raises(self):
        with self.assertRaises(ValueError):
            slopwatch.set_check_config("vague_intensifier", threshold=0)
        with self.assertRaises(ValueError):
            slopwatch.set_check_config("vague_intensifier", threshold="three")

    def test_invalid_action_raises(self):
        with self.assertRaises(ValueError):
            slopwatch.set_check_config("vague_intensifier", action="deny")

    def test_set_check_config_merges_rather_than_replaces(self):
        # Regression guard: a CLI/dashboard edit naturally sets one field
        # at a time -- a second set_check_config() call for the other
        # field must not silently reset the first back to its default.
        slopwatch.set_check_config("vague_intensifier", threshold=7)
        slopwatch.set_check_config("vague_intensifier", action="block")
        cfg = slopwatch.list_check_config()["vague_intensifier"]
        self.assertEqual(cfg["threshold"], 7)
        self.assertEqual(cfg["action"], "block")

    def test_setting_one_check_leaves_others_at_default(self):
        slopwatch.set_check_config("vague_intensifier", threshold=9)
        cfg = slopwatch.list_check_config()
        self.assertEqual(cfg["vague_intensifier"]["threshold"], 9)
        self.assertEqual(cfg["filler_opener"],
                          {"threshold": 1, "action": "warn",
                           "default_threshold": 1, "default_action": "warn"})


class WordlistExtensibilityDirectTests(unittest.TestCase):
    """Direct check-function tests -- extra=() default keeps every existing
    direct-call test above working unchanged; these confirm the extension
    mechanism itself, independent of project-config plumbing."""

    def test_extra_term_flags_alongside_built_ins(self):
        self.assertEqual(lint.check_weasel_attribution("Reportedly this works."), [])
        hits = lint.check_weasel_attribution("Reportedly this works.", extra=["reportedly"])
        self.assertEqual(len(hits), 1)

    def test_built_in_still_flags_with_extra_present(self):
        hits = lint.check_weasel_attribution("Studies show this works.", extra=["reportedly"])
        self.assertEqual(len(hits), 1)

    def test_extra_term_for_mechanical_stock_adverb_autofixes(self):
        hits = lint.check_stock_adverb("Frankly, this works.", extra=["frankly"])
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["auto_fix"])

    def test_extra_marketing_adjective_flags(self):
        self.assertEqual(
            len(lint.check_marketing_adjective("A bulletproof solution.", extra=["bulletproof"])), 1)

    def test_extra_filler_verb_is_escaped_not_treated_as_regex(self):
        # A custom term containing a regex metacharacter ("." here) must
        # match only the literal term, not "." as a wildcard.
        self.assertEqual(lint.check_filler_verb("This autoXmagic helps.", extra=["auto.magic"]), [])
        hits = lint.check_filler_verb("This auto.magic helps.", extra=["auto.magic"])
        self.assertEqual(len(hits), 1)

    def test_extra_marketing_cliche_flags(self):
        self.assertEqual(
            len(lint.check_marketing_cliche("An unparalleled offer.", extra=["unparalleled"])), 1)


class TermListExtensibilityEndToEndTests(unittest.TestCase):
    """Same temp-project-root isolation as CheckToggleAndOptionsTests --
    proves a real add_term() call actually changes lint_and_gate's
    real-world behavior, not just the direct check functions above."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = lint._paths.find_project_root
        lint._paths.find_project_root = lambda _file: self._tmp.name
        _terms._migration_checked.clear()

    def tearDown(self):
        lint._paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_registered_term_reaches_lint_and_gate(self):
        text = "Reportedly, this approach works better."
        self.assertNotIn("weasel_attribution",
                          [f["kind"] for f in lint.lint_and_gate(text)["semantic_flags"]])
        slopwatch.add_term("weasel_attribution", "reportedly", "flagged live, missing from v1")
        self.assertIn("weasel_attribution",
                       [f["kind"] for f in lint.lint_and_gate(text)["semantic_flags"]])

    def test_removed_term_stops_flagging(self):
        slopwatch.add_term("weasel_attribution", "reportedly")
        text = "Reportedly, this approach works better."
        self.assertIn("weasel_attribution",
                       [f["kind"] for f in lint.lint_and_gate(text)["semantic_flags"]])
        slopwatch.remove_term("weasel_attribution", "reportedly")
        self.assertNotIn("weasel_attribution",
                          [f["kind"] for f in lint.lint_and_gate(text)["semantic_flags"]])

    def test_registered_stock_adverb_gets_autofixed(self):
        slopwatch.add_term("stock_adverb", "frankly")
        self.assertEqual(lint.apply_mechanical_fixes("Frankly, this works."), "This works.")

    def test_list_term_lists_surfaces_project_terms(self):
        slopwatch.add_term("marketing_cliche", "unparalleled", "found in a real draft")
        lists = slopwatch.list_term_lists()
        self.assertEqual(lists["marketing_cliche"]["project_terms"],
                          {"unparalleled": {"note": "found in a real draft"}})
        self.assertEqual(lists["weasel_attribution"]["project_terms"], {})

    def test_every_list_reports_deny_polarity(self):
        # slopwatch flags what it matches. ste100's list is the opposite
        # polarity -- the distinction that used to be two whole APIs.
        for view in slopwatch.list_term_lists().values():
            self.assertEqual(view["polarity"], "deny")

    def test_built_in_counts_are_reported(self):
        lists = slopwatch.list_term_lists()
        self.assertEqual(lists["stock_adverb"]["built_in_count"],
                          len(lint.STOCK_ADVERBS))

    def test_unknown_list_id_raises_and_does_not_write(self):
        with self.assertRaises(_terms.UnknownTermListError):
            slopwatch.add_term("__not_real__", "x")
        self.assertFalse(os.path.exists(os.path.join(self._tmp.name, "stopslop.config.json")))

    def test_removing_a_never_registered_term_is_a_no_op(self):
        slopwatch.remove_term("weasel_attribution", "never-added")  # must not raise


class TerminologyTests(unittest.TestCase):
    """The project lexicon: one word, one meaning, as a check. Pure-function
    tests against an explicit lexicon dict -- the config-layer plumbing
    (registering a banned word, packs) is the same core.terms machinery the
    other five list-shaped checks already exercise above."""

    LEXICON = {"shipped": {"note": 'use "built-in" instead'},
               "utilize": {"note": ""}}

    def test_no_lexicon_means_no_flags_at_all(self):
        self.assertEqual(lint.check_terminology("Shipped words go free."), [])
        self.assertEqual(lint.check_terminology("Shipped words go free.", {}), [])

    def test_a_banned_synonym_flags_case_insensitively(self):
        hits = lint.check_terminology("The Shipped default applies.", self.LEXICON)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["word"], "Shipped")
        self.assertEqual(hits[0]["rule"], "slopwatch.terminology")

    def test_the_flag_note_names_the_canonical_term(self):
        hits = lint.check_terminology("the shipped default", self.LEXICON)
        self.assertIn("built-in", hits[0]["note"])

    def test_a_term_with_no_note_gets_the_generic_principle(self):
        hits = lint.check_terminology("we utilize things", self.LEXICON)
        self.assertIn("one word, one meaning", hits[0]["note"])

    def test_word_boundaries_hold(self):
        # "reshipped" contains "shipped"; a substring match would flag it.
        self.assertEqual(
            lint.check_terminology("the reshipped carton", self.LEXICON), [])

    def test_a_word_no_lexicon_bans_is_never_flagged(self):
        # End to end through the real resolver. Deliberately NOT asserting
        # on a word this repo's own lexicon bans ("shipped") -- that made
        # the test a hostage of the project's live config, and it failed
        # the moment dogfooding registered the first real banned word.
        result = lint.lint_and_gate("The plain default applies here.")
        self.assertNotIn("terminology",
                          [f["kind"] for f in result["semantic_flags"]])


class DispatcherMigrationTests(unittest.TestCase):
    """lint_and_gate now dispatches through core.checks.run_checks instead
    of a hand-written per-check loop -- this proves the migration byte-
    identical against _lint_and_gate_legacy (the pre-migration
    implementation, kept only for this comparison) across every .py file
    in this repo, not just the small hand-picked snippets the rest of
    this file exercises. Read-only: lints real files, writes nothing.

    Scoped to the checks the legacy loop actually knows. It is frozen at
    the pre-migration check set by definition, so a check added to
    CHECKS_TABLE afterwards makes the dispatcher legitimately produce
    MORE flags. Comparing the intersection keeps what this test is for --
    the dispatcher reproduces the old behaviour exactly for every old
    check -- without turning it into a veto on ever adding one."""

    # Every check the legacy loop calls by name. Deliberately a literal
    # list rather than something derived from CHECKS_TABLE: the whole
    # point is to compare against a frozen implementation, so this has to
    # stay frozen with it.
    LEGACY_CHECK_IDS = frozenset({
        "filler_opener", "stock_adverb", "colon_reveal", "binary_contrast",
        "em_dash_cluster", "weasel_attribution", "entity_encoded_punctuation",
        "bold_bullet_lead", "id_label_lead", "not_just_x_but_y",
        "vague_intensifier", "emoji_in_prose", "marketing_adjective",
        "filler_verb", "marketing_cliche", "solicit_criticism",
        "unearned_profundity", "canned_question_answer", "negative_listing",
        "dramatic_fragmentation", "identifier_in_prose", "terminology",
    })

    @classmethod
    def _legacy_only(cls, flags):
        return [f for f in flags if f["kind"] in cls.LEGACY_CHECK_IDS]

    @staticmethod
    def _repo_python_files():
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        out = []
        for root, dirs, names in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in {"__pycache__", ".venv", ".git"}]
            out.extend(os.path.join(root, n) for n in names if n.endswith(".py"))
        return sorted(out)

    def test_the_legacy_check_set_still_covers_what_the_loop_calls(self):
        """Guards the frozen list above against the real legacy loop
        growing or losing a call, which would make the comparison below
        quietly weaker than it reads."""
        table_ids = set(lint.CHECKS_TABLE)
        self.assertTrue(self.LEGACY_CHECK_IDS <= table_ids,
                         self.LEGACY_CHECK_IDS - table_ids)

    def test_matches_the_legacy_implementation_across_every_real_py_file(self):
        files = self._repo_python_files()
        self.assertGreater(len(files), 50, "sanity check: corpus looks too small to be real")
        for path in files:
            with self.subTest(file=path):
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                old = lint._lint_and_gate_legacy(text, file_path=path)
                new = lint.lint_and_gate(text, file_path=path)
                self.assertEqual(self._legacy_only(old["semantic_flags"]),
                                  self._legacy_only(new["semantic_flags"]))
                self.assertEqual(old["mechanical_violations"], new["mechanical_violations"])
                self.assertEqual(old["sentence_count"], new["sentence_count"])


class StructuralTellTests(unittest.TestCase):
    """The nine checks added from Wikipedia's "Signs of AI writing".

    They exist because of a measurement, not a hunch. A gated arm in this
    project's own evaluation reached ZERO flags on 11 enforced checks and
    still carried structural tells at the same rate as untouched output:
    5.99 per 1000 words before the gate, 6.12 after. Every check the tool
    had was looking at word choice and sentence shape, and the thing that
    survives a lexical scrub is the SHAPE of the document.
    """

    def test_rule_of_three_catches_a_parallel_ing_triad(self):
        self.assertTrue(lint.check_rule_of_three(
            "The release lands, highlighting, underscoring and emphasizing our focus."))

    def test_rule_of_three_leaves_an_ordinary_pair_alone(self):
        self.assertEqual(lint.check_rule_of_three(
            "The service starts and stops cleanly."), [])

    def test_copula_avoidance_catches_serves_as(self):
        self.assertTrue(lint.check_copula_avoidance(
            "The cache serves as a buffer between the API and the database."))

    def test_participial_tail_catches_a_significance_clause(self):
        self.assertTrue(lint.check_participial_tail(
            "We shipped the feature, underscoring the importance of iteration."))

    def test_participial_tail_leaves_a_real_clause_alone(self):
        self.assertEqual(lint.check_participial_tail(
            "We shipped the feature, then removed the old endpoint."), [])

    def test_section_template_catches_the_stock_skeleton(self):
        self.assertTrue(lint.check_section_template("Despite its success, the team faces challenges."))

    def test_bold_density_counts_spans(self):
        flags = lint.check_bold_density("**one** plain **two** plain **three**")
        self.assertEqual(flags[0]["occurrences"], 3)

    def test_bold_density_is_silent_on_unbolded_text(self):
        self.assertEqual(lint.check_bold_density("plain prose with no emphasis"), [])

    def test_thematic_break_counts_horizontal_rules(self):
        flags = lint.check_thematic_break("a\n\n---\n\nb\n\n---\n\nc")
        self.assertEqual(flags[0]["occurrences"], 2)

    def test_thematic_break_ignores_yaml_front_matter(self):
        """A front-matter fence is structure, not decoration. Counting it
        would flag every skill file and changelog with a header block."""
        self.assertEqual(lint.check_thematic_break(
            "---\ntitle: x\n---\n\nbody text here\n"), [])

    def test_title_case_heading_catches_capitalised_headings(self):
        self.assertTrue(lint.check_title_case_heading("## Getting Started With The Tool\n"))

    def test_title_case_heading_allows_sentence_case(self):
        self.assertEqual(lint.check_title_case_heading("## Getting started with the tool\n"), [])

    def test_title_case_heading_allows_proper_nouns_in_a_short_heading(self):
        self.assertEqual(lint.check_title_case_heading("## Claude Code\n"), [])

    def test_ai_markup_remnant_catches_generator_scaffolding(self):
        for leak in ("see oaicite:0", "as reported [cite: 3]",
                      "As an AI language model, I cannot", "[INSERT NAME HERE]"):
            with self.subTest(leak=leak):
                self.assertTrue(lint.check_ai_markup_remnant(f"Text. {leak}. More."))

    def test_ai_markup_remnant_is_silent_on_ordinary_prose(self):
        self.assertEqual(lint.check_ai_markup_remnant(
            "The parser reads the file and returns a list of records."), [])

    def test_paragraph_uniformity_catches_evenly_sized_blocks(self):
        para = " ".join(["word"] * 40)
        self.assertTrue(lint.check_paragraph_uniformity("\n\n".join([para] * 5)))

    def test_paragraph_uniformity_leaves_varied_prose_alone(self):
        paras = [" ".join(["word"] * n) for n in (22, 70, 30, 110, 25)]
        self.assertEqual(lint.check_paragraph_uniformity("\n\n".join(paras)), [])

    def test_paragraph_uniformity_needs_enough_paragraphs_to_mean_anything(self):
        """Two same-sized paragraphs are a coincidence, not a
        fingerprint."""
        para = " ".join(["word"] * 40)
        self.assertEqual(lint.check_paragraph_uniformity("\n\n".join([para] * 2)), [])

    def test_every_new_check_warns_rather_than_blocks(self):
        """These are tells, not defects, and slopwatch blocks nothing --
        see em_dash_cluster's own note for the reasoning."""
        cfg = slopwatch.list_check_config()
        for check_id in ("rule_of_three", "copula_avoidance", "participial_tail",
                          "section_template", "bold_density", "thematic_break",
                          "title_case_heading", "ai_markup_remnant",
                          "paragraph_uniformity"):
            with self.subTest(check=check_id):
                self.assertEqual(cfg[check_id]["action"], "warn")


if __name__ == "__main__":
    unittest.main()
