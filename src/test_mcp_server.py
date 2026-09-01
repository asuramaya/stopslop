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
    import rulesets
    from core import config as core_config
    from core import terms as core_terms
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


class _FakeChecks:
    """In-memory checks-capable ruleset -- mirrors rulesets/slopwatch's
    real list_checks/set_enabled_checks/list_check_config shape without
    ever touching a real stopslop.config.json, same isolation principle
    as _FakeGlossary above. foo_check declares one extra param, mirroring
    ste100's length and its word limits."""

    ALL_CHECKS = {"foo_check", "bar_check"}
    PARAMS = {"foo_check": {"word_limit"}}

    def __init__(self):
        self.RULESET_ID = "fake_checks"
        self.CAPABILITIES = frozenset()
        self._disabled = set()
        self._check_config = {c: {"threshold": 1, "action": "warn"} for c in self.ALL_CHECKS}
        self._check_config["foo_check"]["params"] = {"word_limit": {"value": 20, "default": 20}}

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

    def list_check_config(self):
        return {c: dict(spec) for c, spec in self._check_config.items()}

    def set_check_config(self, check_id, threshold=None, action=None, **params):
        if check_id not in self.ALL_CHECKS:
            raise ValueError(f"unknown check id {check_id!r}")
        if action is not None and action not in ("block", "warn"):
            raise ValueError(f"action must be 'block' or 'warn', got {action!r}")
        unknown = set(params) - self.PARAMS.get(check_id, set())
        if unknown:
            raise ValueError(f"unknown setting(s) for {check_id!r}: {sorted(unknown)}")
        spec = self._check_config.setdefault(check_id, {"threshold": 1, "action": "warn"})
        if threshold is not None:
            spec["threshold"] = threshold
        if action is not None:
            spec["action"] = action
        for name, value in params.items():
            spec["params"][name]["value"] = value


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class ChecksToolsTests(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeChecks()
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

    def test_set_check_config_param_then_list_reflects_it(self):
        result = mcp_server.set_check_config("foo_check", params={"word_limit": 9})
        self.assertTrue(result["ok"])
        config = mcp_server.list_check_config()["check_config"]
        self.assertEqual(config["foo_check"]["params"]["word_limit"]["value"], 9)

    def test_set_check_config_refuses_unknown_param(self):
        result = mcp_server.set_check_config("bar_check", params={"word_limit": 9})
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")

    def test_set_check_config_threshold_then_list_reflects_it(self):
        result = mcp_server.set_check_config("foo_check", threshold=3)
        self.assertTrue(result["ok"])
        self.assertEqual(mcp_server.list_check_config()["check_config"]["foo_check"]["threshold"], 3)

    def test_set_check_config_action_then_list_reflects_it(self):
        result = mcp_server.set_check_config("foo_check", action="block")
        self.assertTrue(result["ok"])
        self.assertEqual(mcp_server.list_check_config()["check_config"]["foo_check"]["action"], "block")

    def test_set_check_config_leaving_threshold_at_zero_does_not_change_it(self):
        # threshold=0 doubles as "not set" -- see set_check_config's own
        # docstring on why 0 is never a valid real threshold.
        mcp_server.set_check_config("foo_check", threshold=5)
        mcp_server.set_check_config("foo_check", action="block")
        self.assertEqual(mcp_server.list_check_config()["check_config"]["foo_check"]["threshold"], 5)

    def test_set_check_config_refuses_unknown_check(self):
        result = mcp_server.set_check_config("__not_real__", threshold=1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")

    def test_set_check_config_refuses_invalid_action(self):
        result = mcp_server.set_check_config("foo_check", action="deny")
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "refused")

    def test_capability_gate_refuses_a_ruleset_without_checks(self):
        mcp_server._resolve = lambda ruleset_id=None: types.SimpleNamespace(
            RULESET_ID="no_checks", CAPABILITIES=frozenset())
        self.assertEqual(mcp_server.list_checks()["status"], "unsupported")
        self.assertEqual(mcp_server.set_checks({})["status"], "unsupported")
        self.assertEqual(mcp_server.list_check_config()["status"], "unsupported")
        self.assertEqual(mcp_server.set_check_config("x", threshold=1)["status"], "unsupported")


class _FakeTermListRuleset:
    """A terms-capable fake for add_term_list/remove_term_list -- these
    two tools call core.config functions directly (RULESET_ID and
    TERM_LISTS are the only attributes they ever read off `active`), not
    a method on the ruleset itself, so this needs no in-memory term
    store the way _FakeTerms does."""

    def __init__(self, ruleset_id="fake_term_list_ruleset"):
        self.RULESET_ID = ruleset_id
        self.CAPABILITIES = frozenset({"terms"})
        self.TERM_LISTS = {}


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class TermListToolsTests(unittest.TestCase):
    """add_term_list/remove_term_list, isolated to a temp project root via
    mcp_server.REPO_ROOT -- core.config.add_custom_term_list/
    delete_custom_term_list both take project_root as a real parameter
    (no import-time-fixed path to work around), so this is genuinely
    isolated, unlike the pack/check/ruleset tools below."""

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_repo_root = mcp_server.REPO_ROOT
        mcp_server.REPO_ROOT = self._tmp.name
        self.fake = _FakeTermListRuleset()
        self._orig_resolve = mcp_server._resolve
        mcp_server._resolve = lambda ruleset_id=None: self.fake

    def tearDown(self):
        mcp_server.REPO_ROOT = self._orig_repo_root
        mcp_server._resolve = self._orig_resolve
        self._tmp.cleanup()

    def test_add_then_visible_in_custom_term_lists(self):
        from core import config as core_config
        result = mcp_server.add_term_list("jargon", label="Jargon")
        self.assertTrue(result["ok"])
        saved = core_config.custom_term_lists(self._tmp.name, self.fake.RULESET_ID)
        self.assertIn("jargon", saved)

    def test_remove_then_gone(self):
        mcp_server.add_term_list("jargon")
        result = mcp_server.remove_term_list("jargon")
        self.assertTrue(result["ok"])

    def test_remove_unknown_list_refuses(self):
        result = mcp_server.remove_term_list("__never_declared__")
        self.assertFalse(result["ok"])

    def test_add_refuses_a_malformed_id(self):
        result = mcp_server.add_term_list("Not-Valid")
        self.assertFalse(result["ok"])

    def test_capability_gate_refuses_a_ruleset_without_terms(self):
        mcp_server._resolve = lambda ruleset_id=None: types.SimpleNamespace(
            RULESET_ID="no_terms", CAPABILITIES=frozenset())
        self.assertEqual(mcp_server.add_term_list("x")["status"], "unsupported")


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class PackToolsTests(unittest.TestCase):
    """add_pack/remove_pack, isolated the same way
    core/test_glossary_packs_custom.py's own _TempCustomPacksDir is --
    glossary_packs._CUSTOM_PACKS_DIR is fixed at import time, so patching
    it directly is the correct seam (mcp_server.REPO_ROOT would do
    nothing for this particular write)."""

    def setUp(self):
        import tempfile
        from core import glossary_packs
        self._glossary_packs = glossary_packs
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_dir = glossary_packs._CUSTOM_PACKS_DIR
        glossary_packs._CUSTOM_PACKS_DIR = self._tmp.name

    def tearDown(self):
        self._glossary_packs._CUSTOM_PACKS_DIR = self._orig_dir
        self._tmp.cleanup()

    def test_add_then_visible_and_removable(self):
        result = mcp_server.add_pack("mcp-probe", "MCP Probe", source="https://example.com",
                                      license="MIT", terms_text="widget: a small mechanism")
        self.assertTrue(result["ok"])
        self.assertIn("mcp-probe", self._glossary_packs.list_packs())

        result = mcp_server.remove_pack("mcp-probe")
        self.assertTrue(result["ok"])
        self.assertNotIn("mcp-probe", self._glossary_packs.list_packs())

    def test_remove_refuses_a_built_in(self):
        result = mcp_server.remove_pack("mdn-glossary")
        self.assertFalse(result["ok"])


class _FakeCustomCheckRuleset:
    """A custom_checks-capable fake bound to a real tempdir via
    core.custom_checks directly -- genuine functional behavior (a real
    add/fire/remove round trip through core.checks.run_checks) with no
    touch of the real repo, the same isolation principle as
    core/test_custom_checks.py's own tests, wired through the MCP tool
    layer instead of called directly."""

    def __init__(self, project_root, ruleset_id="fake_custom_check_ruleset"):
        self.RULESET_ID = ruleset_id
        self.CAPABILITIES = frozenset({"custom_checks"})
        self._project_root = project_root
        self._built_in_ids = set()

    def custom_check_units(self):
        from core import custom_checks as core_custom_checks
        return sorted(u.value for u in core_custom_checks.DEFAULT_ALLOWED_UNITS)

    def custom_check_ids(self):
        from core import custom_checks as core_custom_checks
        return core_custom_checks.custom_check_ids(self._project_root, self.RULESET_ID)

    def add_custom_check(self, check_id, unit, catches, instead, threshold, action, fn_body,
                          terms_list=None):
        from core import custom_checks as core_custom_checks
        core_custom_checks.add_custom_check(
            self._project_root, self.RULESET_ID, self._built_in_ids, check_id, unit,
            catches, instead, threshold, action, fn_body, terms_list=terms_list)

    def update_custom_check(self, check_id, unit, catches, instead, threshold, action, fn_body,
                             terms_list=None):
        from core import custom_checks as core_custom_checks
        core_custom_checks.update_custom_check(
            self._project_root, self.RULESET_ID, self._built_in_ids, check_id, unit,
            catches, instead, threshold, action, fn_body, terms_list=terms_list)

    def remove_custom_check(self, check_id):
        from core import custom_checks as core_custom_checks
        core_custom_checks.remove_custom_check(self._project_root, self.RULESET_ID, check_id)

    def list_checks(self):
        from core import custom_checks as core_custom_checks
        table = core_custom_checks.effective_checks_table({}, self._project_root, self.RULESET_ID)
        return {check_id: {"catches": c.catches, "instead": c.instead, "enabled": True}
                for check_id, c in table.items()}


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class CheckToolsCustomCheckTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.fake = _FakeCustomCheckRuleset(self._tmp.name)
        self._orig_resolve = mcp_server._resolve
        mcp_server._resolve = lambda ruleset_id=None: self.fake
        # add_check/update_check's terms_list binding writes through
        # mcp_server.REPO_ROOT directly (core_config.*_terms_list_* take
        # a project_root, not a ruleset object) -- patch it too, or a
        # terms_list-bearing call here would touch the real repo's own
        # tracked stopslop.config.json instead of this tempdir.
        self._orig_repo_root = mcp_server.REPO_ROOT
        mcp_server.REPO_ROOT = self._tmp.name

    def tearDown(self):
        mcp_server._resolve = self._orig_resolve
        mcp_server.REPO_ROOT = self._orig_repo_root
        self._tmp.cleanup()

    def test_custom_check_units_reports_the_safe_default(self):
        result = mcp_server.custom_check_units()
        self.assertEqual(result["units"], ["document", "sentence"])

    def test_add_then_fires_through_list_checks(self):
        result = mcp_server.add_check(
            "no_todo", "sentence", "a TODO left in prose", "file it",
            'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        self.assertTrue(result["ok"])
        self.assertIn("no_todo", result["checks"])

    def test_update_then_remove_round_trips(self):
        mcp_server.add_check("no_todo", "sentence", "x", "y", "return []")
        updated = mcp_server.update_check(
            "no_todo", "sentence", "a TODO left in prose", "file it",
            'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        self.assertTrue(updated["ok"])
        self.assertIn("no_todo", updated["checks"])

        removed = mcp_server.remove_check("no_todo")
        self.assertTrue(removed["ok"])
        self.assertNotIn("no_todo", removed["checks"])

    def test_remove_unknown_check_refuses(self):
        result = mcp_server.remove_check("__never_added__")
        self.assertFalse(result["ok"])

    def test_add_with_terms_list_binds_it_and_reaches_the_gate(self):
        core_config.add_custom_term_list(self._tmp.name, self.fake.RULESET_ID, "jargon", {})
        core_terms.add_term(self.fake.RULESET_ID,
                             {"jargon": {"label": "jargon", "polarity": "deny",
                                         "accepts_additions": True}},
                             self._tmp.name, "jargon", "widget")
        result = mcp_server.add_check(
            "jargon_probe", "sentence", "project jargon", "use a plain word",
            'return [{"word": w} for w in extra if w in sentence.lower()]',
            terms_list="jargon")
        self.assertTrue(result["ok"])

        lists = core_config.custom_term_lists(self._tmp.name, self.fake.RULESET_ID)
        self.assertEqual(lists["jargon"]["feeds"], "jargon_probe")

        table = self.fake.list_checks()
        self.assertIn("jargon_probe", table)

    def test_add_with_a_terms_list_already_bound_elsewhere_is_refused(self):
        core_config.add_custom_term_list(self._tmp.name, self.fake.RULESET_ID, "jargon", {},
                                          feeds="other_check")
        result = mcp_server.add_check(
            "jargon_probe", "sentence", "x", "y", "return []", terms_list="jargon")
        self.assertFalse(result["ok"])
        self.assertIn("already feeds", result["message"])
        self.assertNotIn("jargon_probe", self.fake.custom_check_ids())

    def test_capability_gate_refuses_a_ruleset_without_custom_checks(self):
        mcp_server._resolve = lambda ruleset_id=None: types.SimpleNamespace(
            RULESET_ID="no_custom_checks", CAPABILITIES=frozenset())
        self.assertEqual(mcp_server.custom_check_units()["status"], "unsupported")
        self.assertEqual(
            mcp_server.add_check("x", "sentence", "c", "i", "return []")["status"],
            "unsupported")


@unittest.skipUnless(_MCP_AVAILABLE, "mcp package not installed -- see README's MCP setup section")
class RulesetToolsTests(unittest.TestCase):
    """add_ruleset/remove_ruleset touch the real repo's own
    .claude/stopslop/custom_rulesets/ and the process-global
    rulesets._REGISTRY -- there is no isolation seam around either (see
    rulesets/test_custom_rulesets_registry.py's own module docstring for
    why: rulesets/__init__.py resolves project root the same
    un-overridable way mcp_server.py's own REPO_ROOT does, and the
    registry is genuinely process-global). Same "touch the real thing,
    always clean up in tearDown" posture already established for this
    exact registry elsewhere in this project (webui's RulesetRouteTests,
    stopslop.py's CmdListRulesetsAddRemoveTests)."""

    RULESET_ID = "mcp_test_scratch_ruleset"

    def tearDown(self):
        from core import custom_rulesets as core_custom_rulesets
        if rulesets.is_custom_ruleset(self.RULESET_ID):
            rulesets.unregister_ruleset(self.RULESET_ID)
        core_custom_rulesets.remove_ruleset(mcp_server.REPO_ROOT, self.RULESET_ID)

    def test_add_then_visible_and_removable(self):
        result = mcp_server.add_ruleset(self.RULESET_ID, name="Scratch")
        self.assertTrue(result["ok"])
        self.assertIn(self.RULESET_ID,
                       [r["id"] for r in mcp_server.list_rulesets()["rulesets"]])

        result = mcp_server.remove_ruleset(self.RULESET_ID)
        self.assertTrue(result["ok"])
        self.assertNotIn(self.RULESET_ID,
                          [r["id"] for r in mcp_server.list_rulesets()["rulesets"]])

    def test_remove_refuses_a_built_in(self):
        result = mcp_server.remove_ruleset("codewatch")
        self.assertFalse(result["ok"])

    def test_add_refuses_a_duplicate_id(self):
        mcp_server.add_ruleset(self.RULESET_ID)
        result = mcp_server.add_ruleset(self.RULESET_ID)
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()
