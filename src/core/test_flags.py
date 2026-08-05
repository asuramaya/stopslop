#!/usr/bin/env python3
"""Tests for core/flags.py's display_label and display_options.

The display_label bug this guards: two call sites (pretool_hook's deny
summary, mcp_server's flag summary) each carried their own `label or
detail["rule"]` fallback, so any flag with no per-occurrence label -- a
sentence-length count, a whole-document synonym-rotation scan, a safety
block whose own severity word never reached the top-level "label" key --
surfaced to a human or agent as a bare internal id like "7.2" or "1.11"
instead of anything that was actually found.
"""
import unittest
from types import SimpleNamespace

from core.flags import (dedup_flags, display_label, display_options,
                          flag_weight)


class DisplayLabelTests(unittest.TestCase):

    def test_prefers_the_flags_own_label(self):
        flag = {"kind": "vocabulary", "label": "leverage",
                "detail": {"rule": "1.5"}, "text": "You should leverage this."}
        self.assertEqual(display_label(flag), "leverage")

    def test_falls_back_to_matched_text_when_no_label(self):
        flag = {"kind": "length", "label": None,
                "detail": {"rule": "1.9"}, "text": "A very long sentence."}
        self.assertEqual(display_label(flag), "A very long sentence.")

    def test_truncates_long_matched_text(self):
        flag = {"kind": "length", "label": None,
                "detail": {"rule": "1.9"}, "text": "x" * 200}
        result = display_label(flag)
        self.assertEqual(len(result), 80)
        self.assertTrue(result.endswith("..."))

    def test_falls_back_to_terms_used_for_document_level_checks(self):
        # synonym_rotation has no per-occurrence text at all -- it flags
        # the whole document, so "text" is None by construction.
        flag = {"kind": "synonym_rotation", "label": None,
                "detail": {"rule": "1.11", "terms_used": ["check", "verify"]},
                "text": None}
        self.assertEqual(display_label(flag), "check, verify")

    def test_falls_back_to_note_when_nothing_else_is_available(self):
        flag = {"kind": "em_dash_cluster", "label": None,
                "detail": {"rule": "slopwatch.em_dash_cluster",
                            "note": "5 em dashes in this document"},
                "text": None}
        self.assertEqual(display_label(flag), "5 em dashes in this document")

    def test_never_falls_back_to_the_raw_rule_id(self):
        # The bug, reproduced directly: a flag with nothing but a rule id
        # must never surface that id as if it were a match.
        flag = {"kind": "length", "label": None,
                "detail": {"rule": "1.9"}, "text": None}
        self.assertNotEqual(display_label(flag), "1.9")
        self.assertEqual(display_label(flag), "length")


class DisplayOptionsTests(unittest.TestCase):
    """Feeds DENY_POLICY's text.format(). The bug: a list-valued option
    (ste100's excluded_vocab_types, the first one this project ever had)
    rendered as its raw Python repr ("['a', 'b']") wherever the dashboard
    and mcp_server's explain() each built this dict by hand -- correct,
    but not fit for a sentence a human reads."""

    def _module(self, capabilities, options):
        return SimpleNamespace(
            CAPABILITIES=frozenset(capabilities),
            list_options=lambda: options)

    def test_scalar_options_pass_through_unchanged(self):
        module = self._module({"options"}, {"word_limit": {"value": 20, "default": 20}})
        self.assertEqual(display_options(module), {"word_limit": 20})

    def test_list_valued_options_are_joined_into_a_readable_string(self):
        module = self._module({"options"}, {
            "excluded_vocab_types": {"value": ["a", "b"], "default": ["a", "b", "c"]}})
        self.assertEqual(display_options(module), {"excluded_vocab_types": "a, b"})

    def test_ruleset_without_options_capability_returns_empty(self):
        module = self._module({"checks"}, {})
        self.assertEqual(display_options(module), {})


class FlagWeightTests(unittest.TestCase):
    """Occurrences, not deduped length -- the policy-side counterpart of
    dedup_flags. A policy that measured the collapsed list read fifty
    repeats of one banned word as a single flag."""

    def test_a_flag_without_occurrences_weighs_one(self):
        self.assertEqual(flag_weight([{"kind": "x", "detail": {}}]), 1)

    def test_occurrences_sum_across_the_list(self):
        collapsed = [{"kind": "x", "detail": {"occurrences": 5}},
                     {"kind": "y", "detail": {}}]
        self.assertEqual(flag_weight(collapsed), 6)

    def test_dedup_then_weight_round_trips_the_original_count(self):
        raw = [{"kind": "x", "label": "slop", "detail": {}} for _ in range(4)]
        self.assertEqual(flag_weight(dedup_flags(raw)), 4)


if __name__ == "__main__":
    unittest.main()
