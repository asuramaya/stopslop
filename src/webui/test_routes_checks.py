#!/usr/bin/env python3
"""Tests for the Checks page -- per-ruleset table, inline toggle/
threshold/action, params, the Try-it playground.

Read-only tests run freely against the real registered rulesets. The
handful of mutation tests snapshot stopslop.config.json in setUp and
restore it byte-for-byte in tearDown (always, even on failure) --
this project's own test_mcp_server.py deliberately never writes the
real config from an automated test; these do, briefly, but leave no
trace, the same "restore no matter what" discipline core/test_config.py's
own temp-directory tests get for free by not touching the real file at
all. Kept real (not faked) because routes_checks.py resolves its
project root the same way every ruleset's own set_check_config() does
(paths.find_project_root, no override parameter) -- there is no seam to
inject a fake project root through here without changing that contract.

Run with (needs the venv):
    cd src && ../.venv/bin/python3 -m unittest webui.test_routes_checks -v
"""
import os
import unittest

try:
    from fastapi.testclient import TestClient

    import rulesets
    from webui.app import app
    from webui.deps import REPO_ROOT
    client = TestClient(app)
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class CheckPageReadOnlyTests(unittest.TestCase):
    def test_defaults_to_the_first_checkable_ruleset(self):
        response = client.get("/checks")
        self.assertEqual(response.status_code, 200)
        self.assertIn('class="active"', response.text)

    def test_every_known_ruleset_renders_its_own_table(self):
        for ruleset_id in ("ste100", "slopwatch", "codewatch"):
            with self.subTest(ruleset_id=ruleset_id):
                response = client.get("/checks", params={"ruleset": ruleset_id})
                self.assertEqual(response.status_code, 200)
                self.assertIn(f'class="active">{ruleset_id}</a>', response.text)
                self.assertIn("checks-table-body", response.text)

    def test_unknown_ruleset_falls_back_to_the_first_known_one(self):
        known = client.get("/checks").text
        fallback = client.get("/checks", params={"ruleset": "not-a-real-ruleset"}).text
        self.assertEqual(known, fallback)

    def test_ste100_length_check_shows_its_params_panel(self):
        response = client.get("/checks", params={"ruleset": "ste100"})
        self.assertIn("procedure_word_limit", response.text)
        self.assertIn("description_word_limit", response.text)

    def test_a_vocabulary_bound_check_points_at_the_vocabulary_page(self):
        response = client.get("/checks", params={"ruleset": "slopwatch"})
        self.assertIn("curate on Vocabulary", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class PlaygroundTests(unittest.TestCase):
    """Read-only -- lint_and_gate never writes anything."""

    def test_blocking_text_reports_deny(self):
        response = client.post("/checks/ste100/playground",
                                data={"text": "The system should utilize this."})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Would DENY", response.text)

    def test_clean_text_reports_pass(self):
        response = client.post("/checks/ste100/playground",
                                data={"text": "The pump has two seals."})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Would DENY", response.text)

    def test_empty_text_is_handled_without_error(self):
        response = client.post("/checks/ste100/playground", data={"text": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Nothing to check", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class MutationTests(unittest.TestCase):
    """Touches the real stopslop.config.json briefly -- see module
    docstring for why, and why it's always restored."""

    def setUp(self):
        self._config_path = os.path.join(REPO_ROOT, "stopslop.config.json")
        self._before = None
        if os.path.exists(self._config_path):
            with open(self._config_path) as f:
                self._before = f.read()

    def tearDown(self):
        if self._before is None:
            if os.path.exists(self._config_path):
                os.unlink(self._config_path)
        else:
            with open(self._config_path, "w") as f:
                f.write(self._before)

    def test_toggle_off_then_on_round_trips(self):
        off = client.post("/checks/codewatch/todo_stub/toggle", data={})
        self.assertEqual(off.status_code, 200)
        self.assertNotIn("checked", off.text.split('name="enabled"')[1][:20])

        on = client.post("/checks/codewatch/todo_stub/toggle", data={"enabled": "on"})
        self.assertEqual(on.status_code, 200)
        self.assertIn("checked", on.text.split('name="enabled"')[1][:20])

    def test_set_threshold_and_action_merge_not_replace(self):
        response = client.post("/checks/codewatch/todo_stub/config", data={"threshold": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('value="3"', response.text)
        # action untouched by a threshold-only post -- still whatever the
        # default was, not reset to warn/block by side effect.
        response2 = client.post("/checks/codewatch/todo_stub/config", data={"action": "block"})
        self.assertIn('value="3"', response2.text)  # threshold=3 survived
        self.assertIn('value="block" selected', response2.text)

    def test_set_param_on_ste100_length(self):
        response = client.post("/checks/ste100/length/param",
                                data={"name": "procedure_word_limit", "value": "18"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('value="18"', response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class ChecksWithoutCheckConfigCapabilityTests(unittest.TestCase):
    """The registry (rulesets/__init__.py's CAPABILITY_ATTRS) allows a
    ruleset to declare "checks" without "check_config" -- no ruleset
    shipped today does, but the page must not assume every checkable
    ruleset looks like today's three. Patches a real registered module's
    CAPABILITIES for the duration of one test rather than a stub, since
    the registry keys off the actual module object identity."""

    def setUp(self):
        self.module = rulesets.get_ruleset("codewatch")
        self._original = self.module.CAPABILITIES
        self.module.CAPABILITIES = frozenset(self._original) - {"check_config"}
        self.addCleanup(setattr, self.module, "CAPABILITIES", self._original)

    def test_row_renders_without_live_threshold_action_controls(self):
        response = client.get("/checks", params={"ruleset": "codewatch"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("not configurable", response.text)
        self.assertNotIn('name="threshold"', response.text)
        self.assertNotIn('name="action"', response.text)

    def test_config_post_returns_error_banner_not_a_500(self):
        response = client.post("/checks/codewatch/todo_stub/config", data={"threshold": "3"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("no tunable threshold/action", response.text)

    def test_param_post_returns_error_banner_not_a_500(self):
        response = client.post("/checks/codewatch/todo_stub/param",
                                data={"name": "whatever", "value": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("no tunable settings", response.text)


if __name__ == "__main__":
    unittest.main()
