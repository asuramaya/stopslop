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
import unittest

try:
    from fastapi.testclient import TestClient

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


if __name__ == "__main__":
    unittest.main()
