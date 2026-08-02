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


if __name__ == "__main__":
    unittest.main()
