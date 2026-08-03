#!/usr/bin/env python3
"""Direct-function tests for mcp_server.py's tool bodies -- previously
hand-verified only (see README's gap list). mcp_server.py imports the
`mcp` package at module level, so this whole file is skipped (not failed)
when it's not installed -- the stdlib-only core suite must stay runnable
without the venv (see requirements.txt).

Read-only tools (lint_text, check_word, list_rulesets, get_status,
list_path_packs) run against the REAL registered rulesets -- safe, no
writes. add_term and remove_term run against a small fake terms-capable
ruleset instead of the real ste100 module, the same "small fake modules"
pattern core/test_config.py already uses -- this project's own real
stopslop.config.json (project terms live there now) and gate history must
never be written by an automated test that CI could run on every push.

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


class _FakeTerms:
    """In-memory terms-capable ruleset -- mirrors the real shape every
    ruleset now shares (list_term_lists/add_term/remove_term) without
    touching any file on disk."""

    def __init__(self):
        self.RULESET_ID = "fake_terms"
        self.CAPABILITIES = frozenset({"terms"})
        self._terms = {}

    def list_term_lists(self, file_path=None):
        return {"l": {"label": "L", "polarity": "allow", "accepts_packs": False,
                       "built_in_count": 0, "pack_count": 0,
                       "project_count": len(self._terms),
                       "effective_count": len(self._terms),
                       "project_terms": dict(self._terms),
                       "pack_terms": [], "rejected": {}}}

    def add_term(self, list_id, term, note="", force=False):
        self._terms[term] = {"note": note}
        return {"ok": True, "status": "registered", "message": f"registered {term!r}"}

    def remove_term(self, list_id, term):
        existed = self._terms.pop(term, None) is not None
        return {"ok": True, "status": "removed" if existed else "no-op",
                "message": f"removed {term!r}" if existed else f"{term!r} not registered"}


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class TermToolsTests(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeTerms()
        self._original_resolve = mcp_server._resolve
        mcp_server._resolve = lambda ruleset_id=None: self.fake

    def tearDown(self):
        mcp_server._resolve = self._original_resolve

    def test_add_then_list_then_remove_round_trips(self):
        self.assertTrue(mcp_server.add_term("l", "widget", note="domain noun")["ok"])
        listed = mcp_server.list_term_lists()
        self.assertIn("widget", listed["lists"]["l"]["project_terms"])

        self.assertTrue(mcp_server.remove_term("l", "widget")["ok"])
        self.assertNotIn("widget",
                          mcp_server.list_term_lists()["lists"]["l"]["project_terms"])

    def test_list_reports_polarity(self):
        self.assertEqual(
            mcp_server.list_term_lists()["lists"]["l"]["polarity"], "allow")

    def test_capability_gate_refuses_a_ruleset_without_terms(self):
        mcp_server._resolve = lambda ruleset_id=None: types.SimpleNamespace(
            RULESET_ID="no_terms", CAPABILITIES=frozenset())
        result = mcp_server.add_term("l", "widget")
        self.assertEqual(result["status"], "unsupported")
        self.assertFalse(result["ok"])


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class TermToolsAgainstRealRulesetsTests(unittest.TestCase):
    """Read-only against the real registry -- no write ever reaches this
    project's own stopslop.config.json."""

    def test_every_real_ruleset_reports_its_lists(self):
        for ruleset_id, expected in (("ste100", "project_terms"),
                                      ("slopwatch", "marketing_cliche"),
                                      ("codewatch", "generic_naming")):
            result = mcp_server.list_term_lists(ruleset=ruleset_id)
            self.assertIn(expected, result["lists"],
                           f"{ruleset_id} did not report {expected}")

    def test_ste100_list_is_allow_polarity_and_others_are_deny(self):
        ste = mcp_server.list_term_lists(ruleset="ste100")["lists"]["project_terms"]
        slop = mcp_server.list_term_lists(ruleset="slopwatch")["lists"]["marketing_cliche"]
        self.assertEqual(ste["polarity"], "allow")
        self.assertEqual(slop["polarity"], "deny")


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class ListPathPacksTests(unittest.TestCase):
    """Pure read -- safe to run against the real config. See
    SetPathPacksRefusalTests for the write half, split into its own tool
    (set_path_packs) so an agent isn't guessing list-vs-write from which
    arguments happen to be present."""

    def test_lists_every_available_pack_as_inert_content(self):
        result = mcp_server.list_path_packs()
        self.assertTrue(result["ok"])
        self.assertEqual(set(result["available"]),
                          {"microsoft-style-guide", "mdn-glossary", "nist-security"})
        # No pack names its own consumer -- that binding is in config.
        self.assertNotIn("target", result["available"]["nist-security"])

    def test_reports_which_rule_and_list_each_pack_feeds(self):
        result = mcp_server.list_path_packs()
        self.assertIsInstance(result["enabled_by_rule"], list)
        for entry in result["enabled_by_rule"]:
            self.assertEqual(set(entry), {"glob", "ruleset", "packs_by_list"})
            self.assertIsInstance(entry["packs_by_list"], dict)


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class SetPathPacksRefusalTests(unittest.TestCase):
    """Only the refusal paths, which never reach a real write -- still safe
    against the real config. glob and list_id are required arguments now
    (the old "called with no glob, only reports" dual-mode moved to
    list_path_packs), so there is no more list-mode call to test here."""

    def test_a_glob_without_a_list_id_refuses(self):
        result = mcp_server.set_path_packs(glob="*.md", list_id="",
                                            pack_ids=["nist-security"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")
        self.assertIn("list_id", result["message"])

    def test_unknown_glob_refuses_without_writing(self):
        result = mcp_server.set_path_packs(glob="__not_a_real_glob__",
                                            list_id="project_terms",
                                            pack_ids=["nist-security"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")


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
        return {c: {"catches": f"{c} catches", "instead": f"{c} instead",
                     "enabled": c not in self._disabled}
                for c in sorted(self.ALL_CHECKS)}

    def set_enabled_checks(self, check_ids):
        unknown = set(check_ids) - self.ALL_CHECKS
        if unknown:
            raise ValueError(f"unknown check id(s): {sorted(unknown)}")
        self._disabled = self.ALL_CHECKS - set(check_ids)

    def set_checks_enabled(self, states):
        unknown = set(states) - self.ALL_CHECKS
        if unknown:
            raise ValueError(f"unknown check id(s): {sorted(unknown)}")
        for check_id, on in states.items():
            self._disabled.discard(check_id) if on else self._disabled.add(check_id)

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

    def test_set_checks_turns_one_off_and_leaves_the_rest(self):
        """The whole reason this tool replaced enable_checks. Naming one
        check must not be read as "and disable everything else" -- the
        caller almost never holds the full list, and the old shape turned
        'quieten this one check' into a silent mass disable."""
        result = mcp_server.set_checks({"foo_check": False})
        self.assertTrue(result["ok"])
        checks = mcp_server.list_checks()["checks"]
        self.assertFalse(checks["foo_check"]["enabled"])
        self.assertTrue(checks["bar_check"]["enabled"])

    def test_set_checks_turns_one_back_on(self):
        mcp_server.set_checks({"foo_check": False})
        mcp_server.set_checks({"foo_check": True})
        self.assertTrue(mcp_server.list_checks()["checks"]["foo_check"]["enabled"])

    def test_set_checks_refuses_unknown_id(self):
        result = mcp_server.set_checks({"__not_real__": False})
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
        self.assertEqual(mcp_server.set_checks({})["status"], "unsupported")
        self.assertEqual(mcp_server.list_options()["status"], "unsupported")
        self.assertEqual(mcp_server.set_ruleset_options({})["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
