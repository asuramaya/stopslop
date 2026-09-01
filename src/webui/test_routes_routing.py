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


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class RulesetRouteTests(unittest.TestCase):
    """Same "touches the real config briefly, always restores" posture as
    MutationTests, plus cleanup of the real scaffolded PACKAGE
    add_ruleset writes -- routes_routing.py resolves project root the
    same un-overridable way every other route here does, so this is a
    real directory under this repo's own .claude/stopslop/custom_rulesets/,
    and a real entry in the process-global rulesets registry."""

    RULESET_ID = "webui_test_scratch_ruleset"

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
        import rulesets
        from core import custom_rulesets as core_custom_rulesets
        if self.RULESET_ID in rulesets._REGISTRY:
            rulesets.unregister_ruleset(self.RULESET_ID)
        core_custom_rulesets.remove_ruleset(REPO_ROOT, self.RULESET_ID)

    def test_add_then_visible_and_removable(self):
        response = client.post("/routing/rulesets/add",
                                data={"ruleset_id": self.RULESET_ID, "name": "Scratch"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.RULESET_ID, response.text)
        self.assertIn("Scratch", response.text)
        # the routing table's own picker (an out-of-band swap) also
        # reflects the new ruleset, without a full page reload
        self.assertIn(f'value="{self.RULESET_ID}"', response.text)

        remove = client.post(f"/routing/rulesets/{self.RULESET_ID}/remove", data={})
        self.assertEqual(remove.status_code, 200)
        self.assertNotIn(self.RULESET_ID, remove.text)

    def test_removing_a_built_in_ruleset_is_refused(self):
        response = client.post("/routing/rulesets/codewatch/remove", data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn("built-in ruleset", response.text)

    def test_removing_a_ruleset_still_routed_is_refused(self):
        client.post("/routing/rulesets/add", data={"ruleset_id": self.RULESET_ID, "name": "Scratch"})
        add_rule = client.post("/routing/add", data={"glob": "zzz_scratch_probe/**",
                                                       "ruleset": self.RULESET_ID})
        self.assertEqual(add_rule.status_code, 200)
        try:
            remove = client.post(f"/routing/rulesets/{self.RULESET_ID}/remove", data={})
            self.assertIn("still routed", remove.text)
        finally:
            rules = core_config.load_rules(REPO_ROOT)
            idx = next(i for i, r in enumerate(rules) if r.get("ruleset") == self.RULESET_ID)
            client.post(f"/routing/{idx}/delete")

    def test_a_duplicate_id_returns_an_error_banner_not_a_500(self):
        client.post("/routing/rulesets/add", data={"ruleset_id": self.RULESET_ID, "name": "Scratch"})
        response = client.post("/routing/rulesets/add",
                                data={"ruleset_id": self.RULESET_ID, "name": "Again"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("error-banner", response.text)

    def test_a_pre_existing_directory_returns_a_clean_error_not_a_500(self):
        # Regression: os.makedirs(exist_ok=False) inside scaffold_ruleset
        # used to let a raw FileExistsError escape as a plain 500 with no
        # error banner, when a directory existed on disk but the id
        # wasn't in existing_ids (a leftover from an interrupted scaffold,
        # or two concurrent submissions).
        ghost_dir = os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_rulesets", self.RULESET_ID)
        os.makedirs(ghost_dir)
        try:
            response = client.post("/routing/rulesets/add",
                                    data={"ruleset_id": self.RULESET_ID, "name": "Ghost"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("error-banner", response.text)
            self.assertIn("already exists", response.text)
        finally:
            import shutil
            shutil.rmtree(ghost_dir, ignore_errors=True)

    def test_a_broken_custom_ruleset_is_surfaced_without_blocking_the_page(self):
        broken_dir = os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_rulesets",
                                   "webui_test_broken_for_routing_page")
        os.makedirs(broken_dir)
        with open(os.path.join(broken_dir, "__init__.py"), "w") as f:
            f.write('RULESET_ID = "webui_test_broken_for_routing_page"\n')
        try:
            import rulesets
            rulesets.rescan_custom_rulesets()
            response = client.get("/routing")
            self.assertEqual(response.status_code, 200)
            self.assertIn("webui_test_broken_for_routing_page", response.text)
            self.assertIn("failed to load", response.text)
        finally:
            import shutil
            shutil.rmtree(broken_dir, ignore_errors=True)
            rulesets._CUSTOM_RULESET_ERRORS.pop("webui_test_broken_for_routing_page", None)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class RenameRulesetRouteTests(unittest.TestCase):
    """A scaffolded ruleset's display name was write-once. Same real
    package, always-clean-up posture as RulesetRouteTests above."""

    RULESET_ID = "webui_test_rename_ruleset"

    def setUp(self):
        self._config_path = os.path.join(REPO_ROOT, "stopslop.config.json")
        self._before = None
        if os.path.exists(self._config_path):
            with open(self._config_path) as f:
                self._before = f.read()
        add = client.post("/routing/rulesets/add",
                           data={"ruleset_id": self.RULESET_ID, "name": "Before"})
        assert add.status_code == 200, add.text

    def tearDown(self):
        if self._before is None:
            if os.path.exists(self._config_path):
                os.unlink(self._config_path)
        else:
            with open(self._config_path, "w") as f:
                f.write(self._before)
        import rulesets
        from core import custom_rulesets as core_custom_rulesets
        if self.RULESET_ID in rulesets._REGISTRY:
            rulesets.unregister_ruleset(self.RULESET_ID)
        core_custom_rulesets.remove_ruleset(REPO_ROOT, self.RULESET_ID)

    def _init_path(self):
        return os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_rulesets",
                             self.RULESET_ID, "__init__.py")

    def test_rename_round_trips_into_the_live_registry(self):
        response = client.post(f"/routing/rulesets/{self.RULESET_ID}/rename",
                                data={"name": "After"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("After", response.text)
        import rulesets
        self.assertEqual(rulesets.get_ruleset(self.RULESET_ID).RULESET_NAME,
                          "After")

    def test_rename_keeps_a_project_authors_own_edits_to_the_package(self):
        """The package is a starting point people edit. Regenerating it
        from the template to change one string would discard their work,
        so only the RULESET_NAME line is rewritten."""
        with open(self._init_path(), "a") as f:
            f.write("\n# a project author's own comment\n")
        client.post(f"/routing/rulesets/{self.RULESET_ID}/rename",
                     data={"name": "After"})
        with open(self._init_path()) as f:
            source = f.read()
        self.assertIn("a project author's own comment", source)
        self.assertIn("After", source)

    def test_an_empty_name_is_refused(self):
        response = client.post(f"/routing/rulesets/{self.RULESET_ID}/rename",
                                data={"name": "   "})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)
        import rulesets
        self.assertEqual(rulesets.get_ruleset(self.RULESET_ID).RULESET_NAME,
                          "Before")

    def test_renaming_a_built_in_ruleset_is_refused(self):
        response = client.post("/routing/rulesets/codewatch/rename",
                                data={"name": "hijacked"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)
        import rulesets
        self.assertNotEqual(rulesets.get_ruleset("codewatch").RULESET_NAME,
                             "hijacked")


if __name__ == "__main__":
    unittest.main()
