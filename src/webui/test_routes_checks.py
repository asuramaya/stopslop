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
import html
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

    def test_unit_column_shows_each_checks_own_unit(self):
        response = client.get("/checks", params={"ruleset": "codewatch"})
        self.assertIn("<th>Unit</th>", response.text)
        row = response.text.split('id="row-todo_stub"')[1].split("</tr>")[0]
        self.assertIn(">line<", row)


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
class CustomCheckRouteTests(unittest.TestCase):
    """Same "touches the real config briefly, always restores" posture as
    MutationTests above, plus cleanup of the real custom-check FILE
    add_custom_check writes -- routes_checks.py resolves project root the
    same un-overridable way every other route here does, so this is a
    real file under this repo's own .claude/stopslop/custom_checks/."""

    CHECK_ID = "webui_test_no_todo"

    def setUp(self):
        self._config_path = os.path.join(REPO_ROOT, "stopslop.config.json")
        self._before = None
        if os.path.exists(self._config_path):
            with open(self._config_path) as f:
                self._before = f.read()
        self._check_path = os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_checks",
                                         "codewatch", f"{self.CHECK_ID}.py")

    def tearDown(self):
        if self._before is None:
            if os.path.exists(self._config_path):
                os.unlink(self._config_path)
        else:
            with open(self._config_path, "w") as f:
                f.write(self._before)
        if os.path.exists(self._check_path):
            os.unlink(self._check_path)

    def test_add_then_visible_and_removable(self):
        response = client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "a TODO left in code",
            "instead": "file a real issue", "threshold": "1", "action": "warn",
            "fn_body": 'return [{"phrase": "TODO"}] if "TODO" in line else []',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.CHECK_ID, response.text)
        self.assertIn("custom", response.text)
        self.assertTrue(os.path.exists(self._check_path))

        remove = client.post(f"/checks/codewatch/{self.CHECK_ID}/remove", data={})
        self.assertEqual(remove.status_code, 200)
        self.assertNotIn(self.CHECK_ID, remove.text)
        self.assertFalse(os.path.exists(self._check_path))

    def test_a_disallowed_unit_returns_an_error_banner_not_a_500(self):
        response = client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "sentence", "catches": "x",
            "instead": "y", "threshold": "1", "action": "warn", "fn_body": "return []",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("error-banner", response.text)
        self.assertFalse(os.path.exists(self._check_path))

    def test_removing_a_built_in_check_is_refused(self):
        response = client.post("/checks/codewatch/todo_stub/remove", data={})
        self.assertEqual(response.status_code, 200)
        self.assertIn("built-in check", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class EditCustomCheckRouteTests(unittest.TestCase):
    """Same real-file, always-restore posture as CustomCheckRouteTests --
    /edit and /update round-trip a real check under codewatch's own
    .claude/stopslop/custom_checks/, cleaned up in tearDown regardless of
    outcome."""

    CHECK_ID = "webui_test_edit_check"

    def setUp(self):
        self._config_path = os.path.join(REPO_ROOT, "stopslop.config.json")
        self._before = None
        if os.path.exists(self._config_path):
            with open(self._config_path) as f:
                self._before = f.read()
        self._check_path = os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_checks",
                                         "codewatch", f"{self.CHECK_ID}.py")
        add = client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "a TODO left in code",
            "instead": "file a real issue", "threshold": "1", "action": "warn",
            "fn_body": 'return [{"phrase": "TODO"}] if "TODO" in line else []',
        })
        assert add.status_code == 200 and os.path.exists(self._check_path), add.text

    def tearDown(self):
        if self._before is None:
            if os.path.exists(self._config_path):
                os.unlink(self._config_path)
        else:
            with open(self._config_path, "w") as f:
                f.write(self._before)
        if os.path.exists(self._check_path):
            os.unlink(self._check_path)

    def test_edit_prefills_the_current_matcher_body(self):
        response = client.get(f"/checks/codewatch/{self.CHECK_ID}/edit")
        self.assertEqual(response.status_code, 200)
        # the textarea's content is HTML-escaped by Jinja2 (correct,
        # browser-valid output) -- unescape before comparing so the
        # assertion checks the actual matcher text, not its markup.
        self.assertIn('return [{"phrase": "TODO"}] if "TODO" in line else []',
                       html.unescape(response.text))
        self.assertIn('value="a TODO left in code"', response.text)
        self.assertIn('value="file a real issue"', response.text)

    def test_edit_on_a_built_in_check_is_refused(self):
        response = client.get("/checks/codewatch/todo_stub/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn("error-banner", response.text)
        self.assertIn("built-in check", response.text)

    def test_update_changes_the_matcher_and_metadata(self):
        response = client.post(f"/checks/codewatch/{self.CHECK_ID}/update", data={
            "unit": "line", "catches": "a FIXME left in code", "instead": "file it",
            "threshold": "3", "action": "block",
            "fn_body": 'return [{"phrase": "FIXME"}] if "FIXME" in line else []',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("a FIXME left in code", response.text)
        self.assertIn('value="3"', response.text)
        self.assertIn('value="block" selected', response.text)

        # persisted, not just echoed in the response -- confirm via a
        # fresh /edit read rather than trusting the update's own response.
        reread = client.get(f"/checks/codewatch/{self.CHECK_ID}/edit")
        self.assertIn('return [{"phrase": "FIXME"}] if "FIXME" in line else []',
                       html.unescape(reread.text))

    def test_a_failed_update_keeps_the_submitted_values_not_the_old_ones(self):
        response = client.post(f"/checks/codewatch/{self.CHECK_ID}/update", data={
            "unit": "line", "catches": "still catches this", "instead": "still do this",
            "threshold": "1", "action": "warn", "fn_body": "this is not python (",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("error-banner", response.text)
        self.assertIn('value="still catches this"', response.text)
        self.assertIn("this is not python (", response.text)

        # the old saved version is untouched by the failed attempt
        reread = client.get(f"/checks/codewatch/{self.CHECK_ID}/edit")
        self.assertIn('return [{"phrase": "TODO"}] if "TODO" in line else []',
                       html.unescape(reread.text))

    def test_update_on_a_built_in_check_is_refused(self):
        response = client.post("/checks/codewatch/todo_stub/update", data={
            "unit": "line", "catches": "x", "instead": "y", "threshold": "1",
            "action": "warn", "fn_body": "return []",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("error-banner", response.text)
        self.assertIn("built-in check", response.text)

    def test_row_fragment_renders_the_plain_row(self):
        response = client.get(f"/checks/codewatch/{self.CHECK_ID}/row")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.CHECK_ID, response.text)
        self.assertIn("Edit", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class TermsListBindingRouteTests(unittest.TestCase):
    """A custom check binding to a custom vocabulary list -- add/edit's
    new "Vocabulary list" select, wired through core.config's own
    feeds/set_custom_term_list_feeds/clear_feeds_for_check. Same real-
    file, always-restore posture as CustomCheckRouteTests; the single
    config-file snapshot/restore also covers the custom term list's own
    declaration (custom_term_lists lives in the same file)."""

    CHECK_ID = "webui_test_terms_binding_check"
    LIST_ID = "webui_test_terms_binding_list"

    def setUp(self):
        from core import config as core_config
        self._core_config = core_config
        self._config_path = os.path.join(REPO_ROOT, "stopslop.config.json")
        self._before = None
        if os.path.exists(self._config_path):
            with open(self._config_path) as f:
                self._before = f.read()
        self._check_path = os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_checks",
                                         "codewatch", f"{self.CHECK_ID}.py")
        core_config.add_custom_term_list(REPO_ROOT, "codewatch", self.LIST_ID, {})

    def tearDown(self):
        if self._before is None:
            if os.path.exists(self._config_path):
                os.unlink(self._config_path)
        else:
            with open(self._config_path, "w") as f:
                f.write(self._before)
        if os.path.exists(self._check_path):
            os.unlink(self._check_path)

    def test_add_with_a_list_chosen_binds_it(self):
        response = client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn",
            "fn_body": 'return [{"word": w} for w in extra if w in line]',
            "terms_list": self.LIST_ID,
        })
        self.assertEqual(response.status_code, 200)
        lists = self._core_config.custom_term_lists(REPO_ROOT, "codewatch")
        self.assertEqual(lists[self.LIST_ID]["feeds"], self.CHECK_ID)

    def test_add_with_no_list_chosen_leaves_it_unbound(self):
        response = client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn", "fn_body": "return []",
        })
        self.assertEqual(response.status_code, 200)
        lists = self._core_config.custom_term_lists(REPO_ROOT, "codewatch")
        self.assertNotIn("feeds", lists[self.LIST_ID])

    def test_edit_prefills_the_current_binding(self):
        client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn", "fn_body": "return []",
            "terms_list": self.LIST_ID,
        })
        response = client.get(f"/checks/codewatch/{self.CHECK_ID}/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'value="{self.LIST_ID}" selected', response.text)

    def test_update_can_unbind_a_list(self):
        client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn", "fn_body": "return []",
            "terms_list": self.LIST_ID,
        })
        response = client.post(f"/checks/codewatch/{self.CHECK_ID}/update", data={
            "unit": "line", "catches": "x", "instead": "y", "threshold": "1",
            "action": "warn", "fn_body": "return []",
        })
        self.assertEqual(response.status_code, 200)
        lists = self._core_config.custom_term_lists(REPO_ROOT, "codewatch")
        self.assertNotIn("feeds", lists[self.LIST_ID])

    def test_remove_unbinds_the_list_it_was_feeding(self):
        client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn", "fn_body": "return []",
            "terms_list": self.LIST_ID,
        })
        response = client.post(f"/checks/codewatch/{self.CHECK_ID}/remove", data={})
        self.assertEqual(response.status_code, 200)
        lists = self._core_config.custom_term_lists(REPO_ROOT, "codewatch")
        self.assertNotIn("feeds", lists[self.LIST_ID])

    def test_binding_a_list_already_feeding_another_check_is_refused(self):
        other_check_path = os.path.join(REPO_ROOT, ".claude", "stopslop", "custom_checks",
                                         "codewatch", "webui_test_other_check.py")
        self.addCleanup(lambda: os.path.exists(other_check_path) and os.unlink(other_check_path))
        client.post("/checks/codewatch/custom/add", data={
            "check_id": "webui_test_other_check", "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn", "fn_body": "return []",
            "terms_list": self.LIST_ID,
        })
        response = client.post("/checks/codewatch/custom/add", data={
            "check_id": self.CHECK_ID, "unit": "line", "catches": "x", "instead": "y",
            "threshold": "1", "action": "warn", "fn_body": "return []",
            "terms_list": self.LIST_ID,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("error-banner", response.text)
        self.assertIn("already feeds", response.text)
        # the second check was never created -- refused before any write
        self.assertFalse(os.path.exists(self._check_path))
        lists = self._core_config.custom_term_lists(REPO_ROOT, "codewatch")
        self.assertEqual(lists[self.LIST_ID]["feeds"], "webui_test_other_check")


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
        # Scoped to the table body -- the "Add a check" form below it
        # (custom_checks capability, independent of check_config) has its
        # own unrelated name="threshold"/name="action" fields for a NEW
        # check's defaults, not a per-row live control.
        table_body = response.text.split('id="checks-table-body"')[1].split("</table>")[0]
        self.assertNotIn('name="threshold"', table_body)
        self.assertNotIn('name="action"', table_body)

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
