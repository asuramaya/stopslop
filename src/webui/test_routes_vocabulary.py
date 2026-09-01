#!/usr/bin/env python3
"""Tests for the Vocabulary page -- cross-list search, per-list browser,
add/remove/restore, ste100's override-reason refusal flow.

Same discipline as test_routes_checks.py: read-only tests run freely;
mutation tests snapshot stopslop.config.json in setUp and restore it in
tearDown, always -- see that file's own module docstring for why there's
no seam to fake the project root here without changing the ruleset
contract itself.

Run with (needs the venv):
    cd src && ../.venv/bin/python3 -m unittest webui.test_routes_vocabulary -v
"""
import os
import tempfile
import unittest

try:
    from fastapi.testclient import TestClient

    from core import config as core_config
    from core import glossary_packs
    from core import terms as core_terms
    from webui.app import app
    from webui.deps import REPO_ROOT
    client = TestClient(app)
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class VocabularyPageReadOnlyTests(unittest.TestCase):
    def test_page_boots_with_a_default_list(self):
        response = client.get("/vocabulary")
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="vocab-list"', response.text)

    def test_switching_lists_returns_the_right_block(self):
        response = client.get("/vocabulary/list", params={"rl": "codewatch|generic_naming"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Generic name stems", response.text)

    def test_search_finds_a_known_word_across_rulesets(self):
        response = client.get("/vocabulary/search", params={"q": "leverage"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("leverage", response.text)
        self.assertIn("matching word", response.text)

    def test_empty_query_renders_nothing(self):
        response = client.get("/vocabulary/search", params={"q": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text.strip(), "")

    def test_nonsense_query_reports_no_matches(self):
        response = client.get("/vocabulary/search", params={"q": "xyzzy-nonexistent-term-123"})
        self.assertIn("No word in any list matches", response.text)

    def test_closed_list_offers_no_add_form(self):
        response = client.get("/vocabulary/list", params={"rl": "ste100|approved_words"})
        self.assertIn("takes no new words", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class MutationTests(unittest.TestCase):
    """Touches the real stopslop.config.json briefly -- always restored,
    same discipline test_routes_checks.py's own MutationTests takes."""

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

    def test_add_then_remove_round_trips(self):
        added = client.post("/vocabulary/codewatch/generic_naming/add",
                             data={"term": "zzz_webui_test_word", "note": "temp"})
        self.assertEqual(added.status_code, 200)
        self.assertIn("zzz_webui_test_word", added.text)

        removed = client.post("/vocabulary/codewatch/generic_naming/remove",
                               data={"term": "zzz_webui_test_word"})
        self.assertEqual(removed.status_code, 200)
        self.assertNotIn("zzz_webui_test_word", removed.text)

    def test_forbidden_ste100_word_is_refused_with_an_override_prompt(self):
        response = client.post("/vocabulary/ste100/project_terms/add",
                                data={"term": "utilize", "note": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Override reason", response.text)
        self.assertIn("forbidden", response.text)

    def test_override_with_a_reason_succeeds(self):
        response = client.post("/vocabulary/ste100/project_terms/add",
                                data={"term": "utilize", "note": "test", "force": "testing"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(">utilize<", response.text)
        self.assertNotIn("Override reason", response.text)

    def test_remove_a_built_in_suppresses_not_deletes(self):
        # A built-in codewatch stem can't be deleted (it lives in source),
        # only suppressed -- removing it must move it to the Suppressed
        # section, restorable, not make it vanish outright.
        response = client.post("/vocabulary/codewatch/generic_naming/remove",
                                data={"term": "helper"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Suppressed", response.text)
        self.assertIn("helper", response.text)

        restored = client.post("/vocabulary/codewatch/generic_naming/restore",
                                data={"term": "helper"})
        self.assertIn("built-in", restored.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class PackRoutesTests(unittest.TestCase):
    """Isolated against a temp _CUSTOM_PACKS_DIR (same pattern as
    core/test_glossary_packs_custom.py) -- never touches this repo's own
    real .claude/stopslop/custom_packs/."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig = glossary_packs._CUSTOM_PACKS_DIR
        glossary_packs._CUSTOM_PACKS_DIR = self._tmp.name
        self.addCleanup(setattr, glossary_packs, "_CUSTOM_PACKS_DIR", self._orig)
        self.addCleanup(self._tmp.cleanup)

    def test_page_lists_built_in_packs(self):
        response = client.get("/vocabulary")
        self.assertIn("MDN Web Docs Glossary", response.text)
        self.assertIn("built-in", response.text)

    def test_add_pack_then_it_appears(self):
        response = client.post("/vocabulary/packs/add", data={
            "pack_id": "my-pack", "name": "My Pack", "source": "https://example.com",
            "license": "MIT", "content_kind": "word", "terms": "widget\ngadget: a note",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("My Pack", response.text)
        self.assertIn("custom", response.text)

    def test_add_pack_rejects_a_dead_key_with_an_error_banner(self):
        response = client.post("/vocabulary/packs/add", data={
            "pack_id": "my-pack", "name": "My Pack", "source": "x",
            "license": "MIT", "content_kind": "word", "terms": "front-end",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)
        self.assertNotIn("My Pack", response.text)

    def test_remove_custom_pack_round_trips(self):
        client.post("/vocabulary/packs/add", data={
            "pack_id": "my-pack", "name": "My Pack", "source": "x",
            "license": "MIT", "content_kind": "word", "terms": "",
        })
        response = client.post("/vocabulary/packs/my-pack/remove")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("My Pack", response.text)

    def test_cannot_remove_a_built_in_pack(self):
        response = client.post("/vocabulary/packs/mdn-glossary/remove")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)
        self.assertIn("MDN Web Docs Glossary", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class ListRoutesTests(unittest.TestCase):
    """Touches the real stopslop.config.json briefly -- always restored,
    same discipline every other MutationTests class in this project's
    webui test suite takes."""

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

    def test_add_list_then_it_appears_in_the_picker(self):
        response = client.post("/vocabulary/lists/add", data={
            "ruleset_id": "codewatch", "list_id": "my_custom_list",
            "label": "My Custom List", "polarity": "deny",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("my_custom_list", response.text)
        self.assertIn("(custom)", response.text)

    def test_add_list_rejects_a_built_in_id(self):
        response = client.post("/vocabulary/lists/add", data={
            "ruleset_id": "codewatch", "list_id": "generic_naming", "polarity": "deny",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)

    def test_add_list_rejects_a_malformed_id(self):
        response = client.post("/vocabulary/lists/add", data={
            "ruleset_id": "codewatch", "list_id": "Not Valid!", "polarity": "deny",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)

    def test_add_then_add_a_term_to_the_new_list(self):
        client.post("/vocabulary/lists/add", data={
            "ruleset_id": "codewatch", "list_id": "my_custom_list",
            "polarity": "deny", "accepts_additions": "on",
        })
        response = client.post("/vocabulary/codewatch/my_custom_list/add",
                                data={"term": "widget", "note": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("widget", response.text)

    def test_remove_list_round_trips(self):
        client.post("/vocabulary/lists/add", data={
            "ruleset_id": "codewatch", "list_id": "my_custom_list", "polarity": "deny",
        })
        response = client.post("/vocabulary/lists/codewatch/my_custom_list/remove")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("my_custom_list", response.text)

    def test_remove_of_unknown_custom_list_returns_an_error_banner(self):
        response = client.post("/vocabulary/lists/codewatch/never-existed/remove")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi not installed -- see README's dashboard setup section")
class EditListSpecRouteTests(unittest.TestCase):
    """A custom list's own spec was write-once: declared at Add time and
    then unchangeable from the dashboard, so a typo'd label or a polarity
    picked wrong meant deleting the list and losing its words. Same
    real-config, always-restore posture as ListRoutesTests above.
    """

    LIST_ID = "webui_test_editable_list"

    def setUp(self):
        self._config_path = os.path.join(REPO_ROOT, "stopslop.config.json")
        self._before = None
        if os.path.exists(self._config_path):
            with open(self._config_path) as f:
                self._before = f.read()
        add = client.post("/vocabulary/lists/add", data={
            "ruleset_id": "codewatch", "list_id": self.LIST_ID,
            "label": "Before", "polarity": "deny", "accepts_additions": "on",
        })
        assert add.status_code == 200, add.text

    def tearDown(self):
        if self._before is None:
            if os.path.exists(self._config_path):
                os.unlink(self._config_path)
        else:
            with open(self._config_path, "w") as f:
                f.write(self._before)

    def _spec(self):
        return core_config.custom_term_lists(REPO_ROOT, "codewatch")[self.LIST_ID]

    def test_label_and_polarity_round_trip(self):
        response = client.post(
            f"/vocabulary/lists/codewatch/{self.LIST_ID}/update", data={
                "label": "After", "polarity": "allow", "content_kind": "phrase",
            })
        self.assertEqual(response.status_code, 200)
        spec = self._spec()
        self.assertEqual(spec["label"], "After")
        self.assertEqual(spec["polarity"], "allow")
        self.assertEqual(spec["content_kind"], "phrase")

    def test_an_unchecked_box_actually_turns_the_flag_off(self):
        """A checkbox absent from the form body means "off". Reading it as
        "leave alone" would make the setting one-way from the UI."""
        self.assertTrue(self._spec()["accepts_additions"])
        client.post(f"/vocabulary/lists/codewatch/{self.LIST_ID}/update",
                     data={"label": "Before", "polarity": "deny"})
        self.assertFalse(self._spec()["accepts_additions"])

    def test_editing_the_spec_keeps_the_words_already_in_the_list(self):
        client.post(f"/vocabulary/codewatch/{self.LIST_ID}/add",
                     data={"term": "widget", "note": "test"})
        client.post(f"/vocabulary/lists/codewatch/{self.LIST_ID}/update",
                     data={"label": "Renamed", "polarity": "allow",
                           "accepts_additions": "on"})
        terms = core_terms.project_terms(REPO_ROOT, "codewatch", self.LIST_ID)
        self.assertIn("widget", terms)

    def test_a_feeds_binding_survives_an_edit_untouched(self):
        """The check-to-list wiring is set on the Checks page and is not
        on this form. Rebuilding the spec from form fields alone would
        silently unbind the check."""
        core_config.set_custom_term_list_feeds(
            REPO_ROOT, "codewatch", self.LIST_ID, "some_check")
        client.post(f"/vocabulary/lists/codewatch/{self.LIST_ID}/update",
                     data={"label": "Edited", "polarity": "deny"})
        self.assertEqual(self._spec().get("feeds"), "some_check")

    def test_editing_a_built_in_list_is_refused(self):
        response = client.post(
            "/vocabulary/lists/codewatch/generic_naming/update",
            data={"label": "hijacked", "polarity": "allow"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)

    def test_editing_an_unknown_list_is_refused(self):
        response = client.post(
            "/vocabulary/lists/codewatch/never-existed/update",
            data={"label": "x", "polarity": "deny"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Couldn't save", response.text)


if __name__ == "__main__":
    unittest.main()
