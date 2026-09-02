#!/usr/bin/env python3
"""Tests for core/history.py's shared gate-activity log."""
import json
import os
import tempfile
import unittest

from core import history


class DedupeDoubleFireTests(unittest.TestCase):
    def test_collapses_true_double_fire_on_same_file(self):
        events = [
            {"file": "a.md", "action": "deny", "ts": 100.0},
            {"file": "a.md", "action": "deny", "ts": 100.5},
        ]
        out = history.dedupe_double_fire(events)
        self.assertEqual(len(out), 1)

    def test_keeps_genuinely_separate_repeats_minutes_apart(self):
        events = [
            {"file": "a.md", "action": "deny", "ts": 100.0},
            {"file": "a.md", "action": "deny", "ts": 400.0},
        ]
        out = history.dedupe_double_fire(events)
        self.assertEqual(len(out), 2)

    def test_regression_fileless_events_never_collapse(self):
        # Live regression found while consolidating this function out of
        # pretool_hook.py/register_term.py: register_term/unregister_term
        # events carry no "file" key, so e.get("file") resolves to the same
        # None on every one of them. Without a real-file guard, a burst of
        # distinct registrations fired within DOUBLE_FIRE_WINDOW_SECONDS
        # (e.g. seeding a glossary from a word list) silently collapsed
        # into a single entry -- a real run of 40+ distinct register_term
        # events undercounted to 7 in stopslop.py status.
        events = [
            {"action": "register_term", "word": "repository", "ts": 100.0},
            {"action": "register_term", "word": "endpoint", "ts": 100.1},
            {"action": "register_term", "word": "session", "ts": 100.2},
        ]
        out = history.dedupe_double_fire(events)
        self.assertEqual(len(out), 3)


class ReadHistoryTests(unittest.TestCase):
    def _write(self, lines):
        f = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False)
        for line in lines:
            f.write(json.dumps(line) + "\n")
        f.close()
        return f.name

    def test_legacy_lines_default_to_ste100(self):
        path = self._write([{"action": "deny", "file": "a.md", "kinds": ["modal"]}])
        try:
            events = history.read_history(path)
            self.assertEqual(events[0]["ruleset"], "ste100")
        finally:
            os.unlink(path)

    def test_tagged_lines_keep_their_own_ruleset(self):
        path = self._write([{"action": "deny", "file": "a.md", "ruleset": "slopwatch"}])
        try:
            events = history.read_history(path)
            self.assertEqual(events[0]["ruleset"], "slopwatch")
        finally:
            os.unlink(path)

    def test_missing_file_returns_empty(self):
        self.assertEqual(history.read_history("/nonexistent/path.log"), [])


class LogEventTests(unittest.TestCase):
    def test_appends_ruleset_and_timestamp(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "history.log")
            history.log_event({"action": "clean", "file": "a.md"}, "ste100", path)
            events = history.read_history(path)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["ruleset"], "ste100")
            self.assertIn("ts", events[0])


class CheckHitCountTests(unittest.TestCase):
    """Which checks earn their keep, out of how many chances they had.

    The dashboard could show WHEN a check last fired and not how often,
    which is the number that reveals a decayed check set. This project
    measured five checks drawn from a 2023-24 catalogue of AI writing
    tells firing zero times against current model output, and noticed
    only by scoring corpora offline.
    """

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False)
        self._tmp.close()
        self.addCleanup(os.unlink, self._tmp.name)

    def _write(self, events):
        with open(self._tmp.name, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")

    def test_counts_hits_and_the_writes_they_came_from(self):
        self._write([
            {"action": "deny", "ruleset": "r", "kinds": ["a", "b"], "ts": 1},
            {"action": "clean", "ruleset": "r", "kinds": [], "ts": 2},
            {"action": "auto_fix", "ruleset": "r", "kinds": ["a"], "ts": 3},
        ])
        hits, events = history.check_hit_counts(self._tmp.name, "r")
        self.assertEqual(hits, {"a": 2, "b": 1})
        self.assertEqual(events, 3)

    def test_a_clean_write_counts_as_a_chance_to_fire(self):
        """The denominator is judged writes, not flagged ones. Counting
        only writes where something fired would make every check look
        like it fires constantly."""
        self._write([{"action": "clean", "ruleset": "r", "kinds": [], "ts": i}
                      for i in range(5)])
        hits, events = history.check_hit_counts(self._tmp.name, "r")
        self.assertEqual((hits, events), ({}, 5))

    def test_non_gate_events_are_not_chances_to_fire(self):
        """Registering a term is not the gate judging text. Counting it
        would dilute every rate with activity no check could respond to."""
        self._write([
            {"action": "deny", "ruleset": "r", "kinds": ["a"], "ts": 1},
            {"action": "register_term", "ruleset": "r", "word": "x", "ts": 2},
            {"action": "config_write", "ruleset": "r", "ts": 3},
        ])
        _hits, events = history.check_hit_counts(self._tmp.name, "r")
        self.assertEqual(events, 1)

    def test_counts_are_scoped_to_one_ruleset(self):
        """Two rulesets can name a check the same thing, so pooling them
        would attribute one ruleset's activity to another's check."""
        self._write([
            {"action": "deny", "ruleset": "r", "kinds": ["shared"], "ts": 1},
            {"action": "deny", "ruleset": "other", "kinds": ["shared"], "ts": 2},
        ])
        hits, events = history.check_hit_counts(self._tmp.name, "r")
        self.assertEqual((hits, events), ({"shared": 1}, 1))

    def test_a_missing_log_reports_nothing_rather_than_raising(self):
        hits, events = history.check_hit_counts("/nonexistent/history.log", "r")
        self.assertEqual((hits, events), ({}, 0))


if __name__ == "__main__":
    unittest.main()
