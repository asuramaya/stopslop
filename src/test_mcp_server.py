#!/usr/bin/env python3
"""Direct-function tests for mcp_server.py's tool bodies -- previously
hand-verified only (see README's gap list). mcp_server.py imports the
`mcp` package at module level, so this whole file is skipped (not failed)
when it's not installed -- the stdlib-only core suite must stay runnable
without the venv (see requirements.txt).

Read-only tools (lint_text, check_word, list_rulesets, get_status) run
against the REAL registered rulesets -- safe, no writes. register_project_term
and unregister_project_term run against a small fake glossary-capable
ruleset instead of the real ste100 module, the same "small fake modules"
pattern core/test_config.py already uses -- this project's own real
project-terms.json and gate history must never be written by an automated
test that CI could run on every push.

Run with (needs the venv -- see README's MCP setup section):
    cd src && ../.venv/bin/python3 -m unittest test_mcp_server -v
"""
import types
import unittest

try:
    import mcp_server
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class LintTextTests(unittest.TestCase):
    def test_clean_text_against_ste100(self):
        result = mcp_server.lint_text("The system starts the service.", ruleset="ste100")
        self.assertEqual(result["ruleset"], "ste100")
        self.assertTrue(result["would_pass_live_gate"])
        self.assertEqual(result["blocking_issues"], [])

    def test_modal_blocks_against_ste100(self):
        result = mcp_server.lint_text("The system should start the service.", ruleset="ste100")
        self.assertFalse(result["would_pass_live_gate"])
        self.assertTrue(any(i["text"] == "should" for i in result["blocking_issues"]))

    def test_against_slopwatch(self):
        result = mcp_server.lint_text("Needless to say, it works.", ruleset="slopwatch")
        self.assertEqual(result["ruleset"], "slopwatch")

    def test_unknown_ruleset_raises(self):
        with self.assertRaises(Exception):
            mcp_server.lint_text("text", ruleset="__not_real__")


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class CheckWordTests(unittest.TestCase):
    def test_word_lookup_capable_ruleset(self):
        result = mcp_server.check_word("should", ruleset="ste100")
        self.assertIn("status", result)

    def test_ruleset_without_word_lookup_is_unsupported(self):
        result = mcp_server.check_word("anything", ruleset="slopwatch")
        self.assertEqual(result["status"], "unsupported")
        self.assertFalse(result["ok"])


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class ListRulesetsAndStatusTests(unittest.TestCase):
    def test_list_rulesets_includes_both_shipped_rulesets(self):
        result = mcp_server.list_rulesets()
        ids = {r["id"] for r in result["rulesets"]}
        self.assertEqual(ids, {"ste100", "slopwatch"})

    def test_get_status_returns_a_dict_with_rulesets_key(self):
        result = mcp_server.get_status()
        self.assertIn("rulesets", result)


class _FakeGlossary:
    """In-memory glossary capable ruleset -- mirrors rulesets/ste100's real
    shape (register_term/unregister_term/list_terms) without touching any
    real file on disk."""

    def __init__(self):
        self.RULESET_ID = "fake_glossary"
        self.CAPABILITIES = frozenset({"glossary"})
        self._terms = {}

    def register_term(self, word, note="", override_unapproved=None):
        self._terms[word] = {"note": note, "override": override_unapproved}
        return {"ok": True, "status": "registered", "message": f"registered {word!r}"}

    def unregister_term(self, word):
        existed = self._terms.pop(word, None) is not None
        return {"ok": existed, "status": "unregistered" if existed else "not_found",
                "message": f"unregistered {word!r}" if existed else f"{word!r} not registered"}

    def list_terms(self):
        return dict(self._terms)


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class RegisterProjectTermTests(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeGlossary()
        self._original_resolve = mcp_server._resolve
        mcp_server._resolve = lambda ruleset_id=None: self.fake

    def tearDown(self):
        mcp_server._resolve = self._original_resolve

    def test_register_then_list_then_unregister_round_trips(self):
        reg = mcp_server.register_project_term("widget", note="domain noun")
        self.assertTrue(reg["ok"])

        listed = mcp_server.list_project_terms()
        self.assertIn("widget", listed["terms"])

        unreg = mcp_server.unregister_project_term("widget")
        self.assertTrue(unreg["ok"])
        self.assertNotIn("widget", mcp_server.list_project_terms()["terms"])

    def test_capability_gate_refuses_a_ruleset_without_glossary(self):
        mcp_server._resolve = lambda ruleset_id=None: types.SimpleNamespace(
            RULESET_ID="no_glossary", CAPABILITIES=frozenset())
        result = mcp_server.register_project_term("widget")
        self.assertEqual(result["status"], "unsupported")
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
