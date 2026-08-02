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
    def test_list_rulesets_includes_every_shipped_ruleset(self):
        result = mcp_server.list_rulesets()
        ids = {r["id"] for r in result["rulesets"]}
        self.assertEqual(ids, {"ste100", "slopwatch", "codewatch"})

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


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class ListGlossaryPacksReadOnlyTests(unittest.TestCase):
    """Read-only, so this runs against the real ste100 ruleset -- no write
    ever reaches this project's own stopslop.config.json."""

    def test_ste100_reports_its_real_packs(self):
        result = mcp_server.list_glossary_packs(ruleset="ste100")
        self.assertEqual(set(result["packs"]),
                          {"microsoft-style-guide", "mdn-glossary", "nist-security"})

    def test_ruleset_without_packs_is_unsupported(self):
        result = mcp_server.list_glossary_packs(ruleset="slopwatch")
        self.assertEqual(result["status"], "unsupported")


class _FakeChecksAndOptions:
    """In-memory checks/options-capable ruleset -- mirrors
    rulesets/slopwatch's real list_checks/set_enabled_checks/list_options/
    set_options shape without ever touching a real stopslop.config.json,
    same isolation principle as _FakeGlossary above."""

    ALL_CHECKS = {"foo_check", "bar_check"}

    def __init__(self):
        self.RULESET_ID = "fake_checks"
        self.CAPABILITIES = frozenset()
        self._disabled = set()
        self._options = {"threshold": 4}

    def list_checks(self):
        return {c: {"description": f"{c} desc", "enabled": c not in self._disabled}
                for c in sorted(self.ALL_CHECKS)}

    def set_enabled_checks(self, check_ids):
        unknown = set(check_ids) - self.ALL_CHECKS
        if unknown:
            raise ValueError(f"unknown check id(s): {sorted(unknown)}")
        self._disabled = self.ALL_CHECKS - set(check_ids)

    def list_options(self):
        return {"threshold": {"value": self._options["threshold"], "default": 4}}

    def set_options(self, options):
        unknown = set(options) - {"threshold"}
        if unknown:
            raise ValueError(f"unknown option(s): {sorted(unknown)}")
        self._options.update(options)


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class ChecksAndOptionsToolsTests(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeChecksAndOptions()
        self._original_resolve = mcp_server._resolve
        mcp_server._resolve = lambda ruleset_id=None: self.fake

    def tearDown(self):
        mcp_server._resolve = self._original_resolve

    def test_every_check_enabled_by_default(self):
        result = mcp_server.list_checks()
        self.assertTrue(all(c["enabled"] for c in result["checks"].values()))

    def test_enable_checks_then_list_reflects_it(self):
        enable = mcp_server.enable_checks(["foo_check"])
        self.assertTrue(enable["ok"])
        checks = mcp_server.list_checks()["checks"]
        self.assertTrue(checks["foo_check"]["enabled"])
        self.assertFalse(checks["bar_check"]["enabled"])

    def test_enable_checks_refuses_unknown_id(self):
        result = mcp_server.enable_checks(["__not_real__"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")

    def test_set_options_then_list_reflects_it(self):
        result = mcp_server.set_ruleset_options({"threshold": 9})
        self.assertTrue(result["ok"])
        self.assertEqual(mcp_server.list_options()["options"]["threshold"]["value"], 9)

    def test_set_options_refuses_unknown_key(self):
        result = mcp_server.set_ruleset_options({"__not_real__": 1})
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")

    def test_capability_gate_refuses_a_ruleset_without_checks(self):
        mcp_server._resolve = lambda ruleset_id=None: types.SimpleNamespace(
            RULESET_ID="no_checks", CAPABILITIES=frozenset())
        self.assertEqual(mcp_server.list_checks()["status"], "unsupported")
        self.assertEqual(mcp_server.enable_checks([])["status"], "unsupported")
        self.assertEqual(mcp_server.list_options()["status"], "unsupported")
        self.assertEqual(mcp_server.set_ruleset_options({})["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
