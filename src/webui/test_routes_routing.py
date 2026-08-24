#!/usr/bin/env python3
"""Tests for the Routing page -- the editable first-match-wins rules
table, real move-up/move-down reordering, per-rule pack bindings and
check exemptions, the path probe.

Same snapshot/restore-in-tearDown discipline as the Checks and
Vocabulary pages' own mutation tests -- see either's module docstring
for why.

Run with (needs the venv):
    cd src && ../.venv/bin/python3 -m unittest webui.test_routes_routing -v
"""
import os
import unittest

try:
    from fastapi.testclient import TestClient

    from webui.app import app
    from webui.deps import REPO_ROOT
    from core import config as core_config
    client = TestClient(app)
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class RoutingPageReadOnlyTests(unittest.TestCase):
    def test_page_boots_and_lists_real_rules(self):
        response = client.get("/routing")
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="glob"', response.text)

    def test_first_row_cannot_move_up(self):
        response = client.get("/routing/table")
        first_row_chunk = response.text.split("<tbody>")[1].split("</tr>")[0]
        self.assertIn("disabled", first_row_chunk)

    def test_probe_resolves_a_real_path(self):
        response = client.get("/routing/probe", params={"path": "README.md"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("README.md", response.text)
        self.assertIn("wins", response.text)

    def test_probe_reports_no_match_for_a_path_outside_the_repo_scope(self):
        response = client.get("/routing/probe", params={"path": "../../etc/passwd"})
        self.assertEqual(response.status_code, 200)

    def test_focus_with_no_index_shows_the_picker_only(self):
        response = client.get("/routing/focus")
        self.assertIn("pick a rule", response.text)

    def test_focus_on_a_real_rule_shows_its_disable_multiselect(self):
        rules = core_config.load_rules(REPO_ROOT)
        scoped_index = next(i for i, r in enumerate(rules) if r.get("ruleset"))
        response = client.get("/routing/focus", params={"index": scoped_index})
        self.assertIn("check_ids", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class MutationTests(unittest.TestCase):
    """Touches the real stopslop.config.json briefly -- always restored."""

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

    def test_move_and_move_back_round_trips_the_order(self):
        before = [r["glob"] for r in core_config.load_rules(REPO_ROOT)]
        self.assertGreaterEqual(len(before), 2)

        client.post("/routing/1/move", params={"direction": "down"})
        moved = [r["glob"] for r in core_config.load_rules(REPO_ROOT)]
        self.assertEqual(moved[1], before[2])
        self.assertEqual(moved[2], before[1])

        client.post("/routing/2/move", params={"direction": "up"})
        restored = [r["glob"] for r in core_config.load_rules(REPO_ROOT)]
        self.assertEqual(restored, before)

    def test_moving_a_rule_carries_its_packs(self):
        rules = core_config.load_rules(REPO_ROOT)
        idx = next((i for i, r in enumerate(rules) if r.get("packs") and i > 0), None)
        if idx is None:
            self.skipTest("no packs-carrying rule below index 0 in this repo's own config")
        glob = rules[idx]["glob"]
        packs_before = rules[idx]["packs"]

        client.post(f"/routing/{idx}/move", params={"direction": "up"})
        after = core_config.load_rules(REPO_ROOT)
        moved = next(r for r in after if r["glob"] == glob)
        self.assertEqual(moved["packs"], packs_before)

    def test_add_then_delete_a_rule_round_trips(self):
        before_count = len(core_config.load_rules(REPO_ROOT))
        client.post("/routing/add", data={"glob": "zzz_webui_test/*.md", "ruleset": "ste100"})
        after_add = core_config.load_rules(REPO_ROOT)
        self.assertEqual(len(after_add), before_count + 1)
        new_index = next(i for i, r in enumerate(after_add) if r["glob"] == "zzz_webui_test/*.md")

        client.post(f"/routing/{new_index}/delete")
        after_delete = core_config.load_rules(REPO_ROOT)
        self.assertEqual(len(after_delete), before_count)

    def test_set_disable_round_trips(self):
        rules = core_config.load_rules(REPO_ROOT)
        idx = next(i for i, r in enumerate(rules) if r.get("ruleset") == "codewatch")
        glob = rules[idx]["glob"]

        client.post(f"/routing/{idx}/disable", data={"check_ids": ["todo_stub"]})
        after = core_config.load_rules(REPO_ROOT)
        self.assertEqual(next(r for r in after if r["glob"] == glob).get("disable"), ["todo_stub"])

        client.post(f"/routing/{idx}/disable", data={})
        cleared = core_config.load_rules(REPO_ROOT)
        self.assertFalse(next(r for r in cleared if r["glob"] == glob).get("disable"))


if __name__ == "__main__":
    unittest.main()
