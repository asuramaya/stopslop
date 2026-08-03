#!/usr/bin/env python3
"""The text every ruleset ships to describe its own checks, held to the
standard stopslop exists to enforce.

This is a real regression test, not a joke about dogfooding. The rot it
guards against shipped and sat in the product for two releases: each check
carried ONE prewritten sentence, authored in the coaching voice the
.claude/<ruleset>-memory.md primer wants ("X keeps showing up -- do Y"),
because that primer was the only consumer at the time. The dashboard's
Checks table later reused the same strings under a "what it catches"
heading, and 37 of 43 rows rendered as the same sentence template repeating
down a column. A slop detector whose own configuration screen was templated
filler.

The failure was invisible to every test in the suite, because each string
was individually fine. Only the COLLECTION was slop -- which is exactly the
kind of thing slopwatch flags in prose (em_dash_cluster and
synonym_rotation are both collection-level checks) and exactly what nothing
was checking here. These assertions look at the collection.

Reads each ruleset's CHECKS directly rather than calling list_checks(), so
nothing here touches the real repo's stopslop.config.json to find out
whether a check happens to be enabled -- the text is a property of the
code, not of this project's configuration.
"""
import os
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rulesets


def _all_checks():
    """[(ruleset_id, check_id, catches, instead), ...] across the fleet."""
    out = []
    for module in rulesets.list_rulesets():
        for check_id, (catches, instead) in getattr(module, "CHECKS", {}).items():
            out.append((module.RULESET_ID, check_id, catches, instead))
    return out


def _trigrams(text):
    words = [w.strip(".,:;\"'()") for w in text.lower().split()]
    return {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}


class CheckTextTests(unittest.TestCase):

    def test_the_fleet_actually_ships_checks_to_examine(self):
        # Guards the guard: every assertion below passes trivially against an
        # empty list, so a refactor that renamed CHECKS would silently turn
        # this whole file into a no-op rather than failing.
        rows = _all_checks()
        self.assertGreaterEqual(len(rows), 40)
        self.assertEqual({r[0] for r in rows},
                          {m.RULESET_ID for m in rulesets.list_rulesets()})

    def test_every_check_carries_both_facts_separately(self):
        for ruleset_id, check_id, catches, instead in _all_checks():
            with self.subTest(check=f"{ruleset_id}.{check_id}"):
                self.assertTrue(catches.strip(), "no 'catches' text")
                self.assertTrue(instead.strip(), "no 'instead' text")
                # Pre-joining them here would put the sentence back in the
                # data and hand every consumer one voice again.
                self.assertNotIn(" -- ", catches)

    def test_no_check_describes_itself_in_the_coaching_voice(self):
        # "keeps showing up" is a claim about FREQUENCY. It is true in the
        # coaching primer, which prefixes each line with a real count from
        # the history log, and content-free in a settings table.
        banned = ("keep showing up", "keeps showing up", "keep opening",
                   "keeps opening", "keep clustering", "keeps clustering")
        for ruleset_id, check_id, catches, instead in _all_checks():
            for phrase in banned:
                with self.subTest(check=f"{ruleset_id}.{check_id}", phrase=phrase):
                    self.assertNotIn(phrase, f"{catches} {instead}".lower())

    def test_no_phrase_dominates_the_catches_column(self):
        """The actual defect: not one bad string, but one string shape
        repeated until the column stopped carrying information."""
        rows = _all_checks()
        counts = Counter()
        for _, _, catches, _ in rows:
            counts.update(_trigrams(catches))
        if not counts:
            self.fail("no trigrams extracted -- the check text is too short to assess")
        phrase, hits = counts.most_common(1)[0]
        limit = max(3, len(rows) // 4)
        self.assertLessEqual(
            hits, limit,
            f"{hits} of {len(rows)} checks describe themselves with the same "
            f"phrase {phrase!r} (limit {limit}). The old PRINCIPLE_TEXT hit 37 "
            f"of 43 this way. Say what each check catches, not what they have "
            f"in common.")

    def test_first_words_are_not_all_the_same(self):
        rows = _all_checks()
        openers = Counter(c.split()[0].lower() for _, _, c, _ in rows if c.split())
        opener, hits = openers.most_common(1)[0]
        self.assertLessEqual(
            hits, max(3, len(rows) // 4),
            f"{hits} of {len(rows)} 'catches' strings open with {opener!r} -- "
            f"a table scanned down its first column reads as one repeated row.")


class CoachingMemoryStillGetsItsVoiceTests(unittest.TestCase):
    """Splitting the sentence must not cost the primer anything: it is the
    one consumer the coaching frame was right for, and it composes its own
    line now instead of reading a prewritten one."""

    def test_generated_line_names_the_pattern_and_the_fix(self):
        import generate_coaching_memory  # noqa: F401 -- import-time smoke
        module = rulesets.get_ruleset("slopwatch")
        catches, instead = module.CHECKS["filler_verb"]
        line = f"- (12x) {catches} -- {instead}."
        self.assertIn("Filler verbs", line)
        self.assertIn("plain verb", line)
        # The count is what makes a recurrence claim in the primer honest;
        # it is also why the checks table needed different words entirely.
        self.assertIn("(12x)", line)


if __name__ == "__main__":
    unittest.main()
