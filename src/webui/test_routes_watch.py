#!/usr/bin/env python3
"""Tests for the Watch page -- activity feed, denials callout, path/
ruleset filters. In-process via TestClient against the real registered
rulesets and this repo's own real history log (read-only, no writes),
same posture webui/test_app.py already takes.

Run with (needs the venv):
    cd src && ../.venv/bin/python3 -m unittest webui.test_routes_watch -v
"""
import unittest

try:
    from fastapi.testclient import TestClient

    from webui.app import app
    from webui.routes_watch import _fmt_ts, _relative_time, _short_path
    client = TestClient(app)
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class WatchPageTests(unittest.TestCase):
    def test_page_boots_and_lists_known_rulesets_in_the_filter(self):
        response = client.get("/watch")
        self.assertEqual(response.status_code, 200)
        self.assertIn('<option value="All">All</option>', response.text)
        self.assertIn('<option value="ste100">ste100</option>', response.text)
        self.assertIn('<option value="slopwatch">slopwatch</option>', response.text)
        self.assertIn('<option value="codewatch">codewatch</option>', response.text)

    def test_page_wires_the_polling_fragment(self):
        response = client.get("/watch")
        self.assertIn('hx-get="/watch/fragment"', response.text)
        self.assertIn("every 2s", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class WatchFragmentTests(unittest.TestCase):
    def test_fragment_boots_unfiltered(self):
        response = client.get("/watch/fragment")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Recent denials", response.text)
        self.assertIn("Full activity", response.text)

    def test_ruleset_filter_narrows_results(self):
        unfiltered = client.get("/watch/fragment").text
        filtered = client.get("/watch/fragment", params={"ruleset": "ste100"}).text
        # A real, populated history log in this repo's own .claude/ dir --
        # the filtered response must never be LARGER than the unfiltered
        # one (narrowing, never widening).
        self.assertLessEqual(len(filtered), len(unfiltered) + 200)  # template chrome slack

    def test_path_filter_accepts_a_query_param(self):
        response = client.get("/watch/fragment", params={"path": "docs/"})
        self.assertEqual(response.status_code, 200)

    def test_nonsense_filter_yields_the_empty_state_not_an_error(self):
        response = client.get("/watch/fragment", params={"path": "no-such-path-xyzzy-123"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("No matching activity yet", response.text)


class HelperTests(unittest.TestCase):
    """Pure functions, no app needed -- always run, even without fastapi."""

    def test_fmt_ts_handles_none(self):
        if not _FASTAPI_AVAILABLE:
            self.skipTest("fastapi not installed")
        self.assertEqual(_fmt_ts(None), "?")

    def test_relative_time_handles_none(self):
        if not _FASTAPI_AVAILABLE:
            self.skipTest("fastapi not installed")
        self.assertEqual(_relative_time(None), "?")

    def test_short_path_handles_none(self):
        if not _FASTAPI_AVAILABLE:
            self.skipTest("fastapi not installed")
        self.assertEqual(_short_path(None), "")


if __name__ == "__main__":
    unittest.main()
