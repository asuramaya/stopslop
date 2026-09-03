#!/usr/bin/env python3
"""Direct-function tests for stopslop.py's ruleset-resolution and
capability-gating logic -- the CLI dispatcher itself still has no
end-to-end subprocess test coverage (see README's gap list), but the two
pieces of genuinely new logic the pluggable-ruleset refactor added
(_resolve's explicit-vs-config-driven resolution, _require_glossary's
capability gate) are exercised directly here against the real registered
rulesets (ste100 has "glossary", slopwatch doesn't -- a real fixture
already on hand, not a mock).

The subject under test is the one module outside src/: stopslop.py sits at
the repository root, because that file's own location is what
core/paths.py resolves the project root FROM. So this file puts the root
on sys.path the way its neighbours here put src/ on it (see
test_contract_doc.py), and lives with the rest of the suite instead of
alone at the root beside its subject.

Run with:
    python3 -m unittest discover -s src -p 'test_*.py'
"""
import io
import json
import glob
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stopslop
import rulesets
from core import config as core_config
from core import terms as _core_terms
from rulesets import slopwatch as _slopwatch


class ResolveTests(unittest.TestCase):
    def test_explicit_ruleset_wins_regardless_of_path(self):
        ruleset = stopslop._resolve("slopwatch", stopslop.REPO_ROOT + "/README.md")
        self.assertEqual(ruleset.RULESET_ID, "slopwatch")

    def test_no_explicit_ruleset_resolves_via_config(self):
        # Prose routes to slopwatch, at the root and at any depth. ste100
        # is opt-in for procedural text now -- in this repo that is
        # CONTRIBUTING.md and nothing else.
        ruleset = stopslop._resolve(None, stopslop.REPO_ROOT + "/notes.md")
        self.assertEqual(ruleset.RULESET_ID, "slopwatch")

    def test_root_readme_resolves_to_slopwatch_by_default(self):
        # Asserted against the built-in DEFAULT_RULES, not the live
        # stopslop.config.json -- the live file is the operator's working
        # state and may route README anywhere while they experiment. This
        # test used to read it and became a hostage of exactly such an
        # experiment (README.md -> codewatch, set from the dashboard).
        ruleset_id = core_config.resolve_ruleset_id(
            stopslop.REPO_ROOT + "/README.md", stopslop.REPO_ROOT,
            config_file=os.path.join(stopslop.REPO_ROOT, "no-such.config.json"))
        self.assertEqual(ruleset_id, "slopwatch")

    def test_py_resolves_to_codewatch(self):
        ruleset = stopslop._resolve(None, stopslop.REPO_ROOT + "/somefile.py")
        self.assertEqual(ruleset.RULESET_ID, "codewatch")

    def test_synthetic_stdin_path_resolves_like_a_real_md_file(self):
        ruleset = stopslop._resolve(None, stopslop._SYNTHETIC_STDIN_PATH)
        self.assertEqual(ruleset.RULESET_ID, "slopwatch")

    def test_unresolvable_path_exits_with_message(self):
        # Not .py -- that's a real codewatch default now; .json still has
        # no default rule at all.
        out_of_scope = stopslop.REPO_ROOT + "/somefile.json"
        with redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit):
                stopslop._resolve(None, out_of_scope)
        self.assertIn("doesn't resolve to any ruleset", err.getvalue())

    def test_unknown_explicit_ruleset_raises(self):
        with self.assertRaises(Exception):
            stopslop._resolve("__not_a_real_ruleset__", stopslop.REPO_ROOT + "/README.md")


class OwnDocsPassTheGateTests(unittest.TestCase):
    """The project's own root README, gated live through whatever ruleset
    it actually resolves to. Guards a regression that shipped and sat
    unnoticed: the README carried two colon-reveal constructions, a filler-
    verb false trigger, and a textbook "X. Not X. It is Y." binary-contrast
    opener -- four blocking flags against the project's own gate, on the
    file every new reader opens first. Nothing ran this check, so nobody
    noticed until someone actually fed the file through the linter."""

    def test_readme_is_clean_against_its_own_resolved_ruleset(self):
        ruleset = stopslop._resolve(None, stopslop.REPO_ROOT + "/README.md")
        with open(stopslop.REPO_ROOT + "/README.md") as f:
            text = f.read()
        result = ruleset.lint_and_gate(text)
        blocking = ruleset.blocking_semantic_flags(result["semantic_flags"])
        self.assertEqual(
            blocking, [],
            f"README.md fails its own {ruleset.RULESET_ID} gate: "
            + ", ".join(f"{f['kind']}({f.get('label')!r})" for f in blocking))


class RequireTermsTests(unittest.TestCase):
    """Every ruleset has term lists now -- "glossary" (ste100's allow list)
    and "wordlists" (slopwatch's/codewatch's deny lists) were one concept
    all along, so the capability gate that used to separate them applies
    uniformly. See src/core/terms.py."""

    def test_every_real_ruleset_passes_the_terms_gate(self):
        for ruleset_id in ("ste100", "slopwatch", "codewatch"):
            ruleset = stopslop._resolve(ruleset_id, stopslop._SYNTHETIC_STDIN_PATH)
            stopslop._require_terms(ruleset)  # must not raise/exit

    def test_ruleset_without_terms_exits_with_clear_message(self):
        ruleset = SimpleNamespace(RULESET_ID="fake", CAPABILITIES=frozenset({"checks"}))
        with redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit):
                stopslop._require_terms(ruleset)
        self.assertIn("no term lists", err.getvalue())


class CmdInitTests(unittest.TestCase):
    def test_force_preserves_unknown_top_level_keys(self):
        # Regression: found live while verifying the prototype->src rename.
        # cmd_init used to overwrite SETTINGS_REAL wholesale from the
        # template, silently dropping "enabledMcpjsonServers" -- a key
        # Claude Code itself writes there the first time a user approves
        # the MCP server, never present in the template at all.
        with tempfile.TemporaryDirectory() as tmp:
            real_path = os.path.join(tmp, "settings.local.json")
            with open(real_path, "w") as f:
                json.dump({"hooks": {"stale": True},
                           "enabledMcpjsonServers": ["stopslop"]}, f)
            original = stopslop.SETTINGS_REAL
            stopslop.SETTINGS_REAL = real_path
            try:
                # no_venv=True: this test only cares about the settings
                # merge -- it must never trigger a real venv bootstrap
                # (network/subprocess) as a side effect.
                stopslop.cmd_init(SimpleNamespace(force=True, no_venv=True))
                with open(real_path) as f:
                    written = json.load(f)
            finally:
                stopslop.SETTINGS_REAL = original
        self.assertEqual(written["enabledMcpjsonServers"], ["stopslop"])
        self.assertIn("PreToolUse", written["hooks"])

    def test_missing_settings_example_fails_clean_not_a_traceback(self):
        # Regression: a partial/corrupted clone missing the tracked
        # .claude/settings.local.json.example used to crash cmd_init with
        # a raw FileNotFoundError traceback -- confirmed live against a
        # fresh-clone simulation missing this file. Must fail with a
        # clear message and a non-zero return instead.
        with tempfile.TemporaryDirectory() as tmp:
            real_path = os.path.join(tmp, "settings.local.json")
            example_path = os.path.join(tmp, "settings.local.json.example")  # never written
            original_real, original_example = stopslop.SETTINGS_REAL, stopslop.SETTINGS_EXAMPLE
            stopslop.SETTINGS_REAL, stopslop.SETTINGS_EXAMPLE = real_path, example_path
            try:
                with redirect_stderr(io.StringIO()) as err:
                    result = stopslop.cmd_init(SimpleNamespace(force=True, no_venv=True))
            finally:
                stopslop.SETTINGS_REAL, stopslop.SETTINGS_EXAMPLE = original_real, original_example
        self.assertEqual(result, 1)
        self.assertIn("is missing", err.getvalue())
        self.assertFalse(os.path.exists(real_path))

    def test_malformed_settings_example_fails_clean_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            real_path = os.path.join(tmp, "settings.local.json")
            example_path = os.path.join(tmp, "settings.local.json.example")
            with open(example_path, "w") as f:
                f.write("{not valid json")
            original_real, original_example = stopslop.SETTINGS_REAL, stopslop.SETTINGS_EXAMPLE
            stopslop.SETTINGS_REAL, stopslop.SETTINGS_EXAMPLE = real_path, example_path
            try:
                with redirect_stderr(io.StringIO()) as err:
                    result = stopslop.cmd_init(SimpleNamespace(force=True, no_venv=True))
            finally:
                stopslop.SETTINGS_REAL, stopslop.SETTINGS_EXAMPLE = original_real, original_example
        self.assertEqual(result, 1)
        self.assertIn("not valid JSON", err.getvalue())
        self.assertFalse(os.path.exists(real_path))


class CmdInitVenvBootstrapTests(unittest.TestCase):
    """`cmd_init`'s venv step, in isolation from the settings-write logic
    above -- a fake `venv_python_path` and a stubbed `_bootstrap_venv`, so
    these never touch a real venv or the network."""

    def _patch(self, obj, name, value):
        original = getattr(obj, name)
        setattr(obj, name, value)
        self.addCleanup(setattr, obj, name, original)

    def _run_init(self, tmp, fake_venv_python, no_venv):
        real_path = os.path.join(tmp, "settings.local.json")
        self._patch(stopslop, "SETTINGS_REAL", real_path)
        self._patch(stopslop.dashboard_launch, "venv_python_path", lambda repo_root: fake_venv_python)
        calls = []
        self._patch(stopslop, "_bootstrap_venv", lambda *a, **k: calls.append(a))
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_init(SimpleNamespace(force=True, no_venv=no_venv))
        return calls, out.getvalue()

    def test_no_venv_flag_skips_bootstrap_and_prints_manual_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, ".venv", "bin", "python3")
            calls, out = self._run_init(tmp, missing, no_venv=True)
        self.assertEqual(calls, [])
        self.assertIn("Skipped venv setup (--no-venv)", out)
        self.assertIn("python3 -m venv", out)

    def test_default_bootstraps_when_venv_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, ".venv", "bin", "python3")
            calls, out = self._run_init(tmp, missing, no_venv=False)
        self.assertEqual(len(calls), 1)

    def test_does_not_bootstrap_when_venv_already_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = os.path.join(tmp, "python3")
            open(existing, "w").close()
            calls, out = self._run_init(tmp, existing, no_venv=False)
        self.assertEqual(calls, [])

    def test_start_instructions_mention_the_mcp_trust_prompt(self):
        # The undocumented-trust-prompt landmine (a stranger's session
        # silently never connects to MCP if they miss this) -- init's own
        # output is the one place that can warn about it before it bites.
        with tempfile.TemporaryDirectory() as tmp:
            existing = os.path.join(tmp, "python3")
            open(existing, "w").close()
            _, out = self._run_init(tmp, existing, no_venv=False)
        self.assertIn("allow this project's MCP servers", out)
        self.assertIn("stopslop.py status", out)


class BootstrapVenvTests(unittest.TestCase):
    def test_success_prints_ready_and_returns_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            venv_dir = os.path.join(tmp, ".venv")
            with redirect_stdout(io.StringIO()) as out:
                result = stopslop._bootstrap_venv(
                    venv_dir, os.path.join(tmp, "requirements.txt"),
                    run=lambda *a, **k: None)
        self.assertTrue(result)
        self.assertIn("Virtual environment ready.", out.getvalue())

    def test_venv_creation_failure_prints_fallback_and_returns_false(self):
        def _fake_run(argv, **k):
            if "venv" in argv:
                raise subprocess.CalledProcessError(1, argv)
            return None

        with tempfile.TemporaryDirectory() as tmp:
            venv_dir = os.path.join(tmp, ".venv")
            with redirect_stdout(io.StringIO()) as out:
                result = stopslop._bootstrap_venv(
                    venv_dir, os.path.join(tmp, "requirements.txt"), run=_fake_run)
        self.assertFalse(result)
        self.assertIn("could not create the venv", out.getvalue())
        self.assertIn("python3 -m venv", out.getvalue())

    def test_pip_install_failure_prints_fallback_and_returns_false(self):
        def _fake_run(argv, **k):
            if "pip" in argv:
                raise subprocess.CalledProcessError(1, argv)
            return None

        with tempfile.TemporaryDirectory() as tmp:
            venv_dir = os.path.join(tmp, ".venv")
            with redirect_stdout(io.StringIO()) as out:
                result = stopslop._bootstrap_venv(
                    venv_dir, os.path.join(tmp, "requirements.txt"), run=_fake_run)
        self.assertFalse(result)
        self.assertIn("pip install failed", out.getvalue())
        self.assertIn("pip install -r", out.getvalue())


def _scan_args(**overrides):
    defaults = dict(paths=[], ruleset=None, glob="*", all=False, quiet=False, json=False)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CmdScanTests(unittest.TestCase):
    """cmd_scan against a real temp tree -- exercises the CLI wiring
    (argument handling, exit codes, --json/--quiet/--all) on top of
    core.scan.scan_tree, which already has its own direct unit coverage in
    core/test_scan.py."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        with open(os.path.join(self.tmp.name, "bad.py"), "w") as f:
            # A real bare `except: pass` (codewatch's swallowed_exception
            # check) plus enough leftover print()s to cross codewatch's own
            # block_flag_count_threshold (4) -- real checks, not synthetic
            # fixtures, so this also exercises would_block the same way the
            # live gate's blocking_semantic_flags() would.
            f.write(
                "try:\n    risky()\nexcept Exception:\n    pass\n"
                "print('debug1')\nprint('debug2')\nprint('debug3')\nprint('debug4')\n"
            )

    def test_glob_without_ruleset_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_scan(_scan_args(glob="*.py"))
        self.assertEqual(code, 1)
        self.assertIn("--glob only applies together with --ruleset", err.getvalue())

    def test_nonexistent_path_errors_cleanly(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_scan(_scan_args(paths=["/does/not/exist/anywhere"]))
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err.getvalue())

    def test_unknown_ruleset_id_raises_loudly(self):
        # Same "loud on a typo, not a silent no-op" contract _resolve()
        # already gives every other command.
        with self.assertRaises(rulesets.UnknownRulesetError):
            stopslop.cmd_scan(_scan_args(paths=[self.tmp.name], ruleset="__not_real__"))

    def test_forced_ruleset_finds_the_real_swallowed_exception_check(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_scan(_scan_args(paths=[self.tmp.name], ruleset="codewatch", glob="*.py"))
        self.assertEqual(code, 1)
        self.assertIn("bad.py", out.getvalue())
        self.assertIn("swallowed_exception", out.getvalue())

    def test_quiet_suppresses_per_file_lines(self):
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_scan(_scan_args(paths=[self.tmp.name], ruleset="codewatch",
                                          glob="*.py", quiet=True))
        self.assertNotIn("bad.py", out.getvalue())
        self.assertIn("Scanned", out.getvalue())

    def test_json_output_is_valid_and_matches_text_mode_verdict(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_scan(_scan_args(paths=[self.tmp.name], ruleset="codewatch",
                                                 glob="*.py", json=True))
        report = json.loads(out.getvalue())
        self.assertEqual(report["scanned"], 1)
        self.assertTrue(report["results"][0]["would_block"])
        self.assertEqual(code, 1)

    def test_clean_tree_exits_zero(self):
        with tempfile.TemporaryDirectory() as clean_dir:
            with open(os.path.join(clean_dir, "ok.py"), "w") as f:
                f.write("def add(a, b):\n    return a + b\n")
            with redirect_stdout(io.StringIO()):
                code = stopslop.cmd_scan(_scan_args(paths=[clean_dir], ruleset="codewatch", glob="*.py"))
        self.assertEqual(code, 0)


def _terms_args(**overrides):
    defaults = dict(ruleset="slopwatch", list=None, add=None, note=None,
                     remove=None, force=None, new_list=None, label=None,
                     polarity=None, no_additions=False, accepts_packs=False,
                     remove_list=None)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CmdTermsTests(unittest.TestCase):
    """cmd_terms against the real ruleset modules, isolated to a temp
    project root so this never touches the repo's own config file."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = _slopwatch.paths.find_project_root
        _slopwatch.paths.find_project_root = lambda _file: self._tmp.name
        self._orig_repo_root = stopslop.REPO_ROOT
        stopslop.REPO_ROOT = self._tmp.name
        _core_terms._migration_checked.clear()

    def tearDown(self):
        _slopwatch.paths.find_project_root = self._orig_find_root
        stopslop.REPO_ROOT = self._orig_repo_root
        _core_terms._migration_checked.clear()
        self._tmp.cleanup()

    def test_new_list_then_visible_and_removable(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_terms(_terms_args(new_list="jargon", label="Jargon"))
        self.assertEqual(code, 0)
        self.assertIn("Declared 'jargon'", out.getvalue())
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_terms(_terms_args(list="jargon"))
        self.assertIn("jargon", out.getvalue())

        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_terms(_terms_args(remove_list="jargon"))
        self.assertEqual(code, 0)
        self.assertIn("Removed", out.getvalue())

    def test_new_list_refuses_a_malformed_id(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_terms(_terms_args(new_list="Not-Valid"))
        self.assertEqual(code, 1)
        self.assertIn("Not saved", err.getvalue())

    def test_remove_list_of_unknown_list_errors_cleanly(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_terms(_terms_args(remove_list="__never_declared__"))
        self.assertEqual(code, 1)
        self.assertIn("Not found", err.getvalue())

    def test_no_args_lists_every_term_list(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_terms(_terms_args())
        self.assertEqual(code, 0)
        self.assertIn("weasel_attribution", out.getvalue())
        self.assertIn("marketing_cliche", out.getvalue())

    def test_output_states_the_polarity(self):
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_terms(_terms_args())
        self.assertIn("deny", out.getvalue())
        self.assertIn("flagged", out.getvalue())

    def test_output_shows_the_layer_breakdown(self):
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_terms(_terms_args(list="stock_adverb"))
        self.assertIn("built-in", out.getvalue())
        self.assertIn("yours", out.getvalue())

    def test_add_then_list_shows_the_term(self):
        with redirect_stdout(io.StringIO()):
            stopslop.cmd_terms(_terms_args(list="weasel_attribution", add="reportedly",
                                            note="cli smoke test"))
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_terms(_terms_args(list="weasel_attribution"))
        self.assertIn("reportedly", out.getvalue())
        self.assertIn("cli smoke test", out.getvalue())

    def test_remove_drops_the_term(self):
        with redirect_stdout(io.StringIO()):
            stopslop.cmd_terms(_terms_args(list="weasel_attribution", add="reportedly"))
            stopslop.cmd_terms(_terms_args(list="weasel_attribution", remove="reportedly"))
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_terms(_terms_args(list="weasel_attribution"))
        self.assertNotIn("reportedly", out.getvalue())

    def test_add_without_list_id_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_terms(_terms_args(add="reportedly"))
        self.assertEqual(code, 1)
        self.assertIn("`--add` needs `--list LIST_ID`", err.getvalue())

    def test_unknown_list_id_errors_cleanly(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_terms(_terms_args(list="__not_real__"))
        self.assertEqual(code, 1)
        self.assertIn("unknown list", err.getvalue())

    def test_ste100_is_reachable_through_the_same_command(self):
        # The point of the collapse: one command, every ruleset, whatever
        # the polarity of its lists.
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_terms(_terms_args(ruleset="ste100"))
        self.assertEqual(code, 0)
        self.assertIn("project_terms", out.getvalue())
        self.assertIn("allow", out.getvalue())


def _checks_args(**overrides):
    defaults = dict(ruleset="slopwatch", enable=None, set_threshold=None,
                     set_action=None, set_param=None, add_check=None,
                     update_check=None, remove_check=None, unit=None,
                     catches=None, instead=None, threshold=None, action=None,
                     fn_body_file=None, terms_list=None)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CmdChecksTests(unittest.TestCase):
    """Same isolation technique as CmdTermsTests above -- a temp project
    root so this never touches the repo's own config file."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        open(os.path.join(self._tmp.name, "stopslop.py"), "w").close()
        self._orig_find_root = _slopwatch.paths.find_project_root
        _slopwatch.paths.find_project_root = lambda _file: self._tmp.name
        self._orig_repo_root = stopslop.REPO_ROOT
        stopslop.REPO_ROOT = self._tmp.name

    def tearDown(self):
        _slopwatch.paths.find_project_root = self._orig_find_root
        stopslop.REPO_ROOT = self._orig_repo_root
        self._tmp.cleanup()

    def _fn_body_file(self, body):
        path = os.path.join(self._tmp.name, "fn_body.py")
        with open(path, "w") as f:
            f.write(body)
        return path

    def test_add_check_then_fires_and_is_removable(self):
        fn_path = self._fn_body_file(
            'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(
                add_check="cli_probe", unit="sentence", catches="x", instead="y",
                fn_body_file=fn_path))
        self.assertEqual(code, 0)
        self.assertIn("Added check 'cli_probe'", out.getvalue())

        result = _slopwatch.lint_and_gate("There is a TODO here.")
        self.assertIn("cli_probe", [f["kind"] for f in result["semantic_flags"]])

        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(remove_check="cli_probe"))
        self.assertEqual(code, 0)
        self.assertIn("Removed check 'cli_probe'", out.getvalue())
        result = _slopwatch.lint_and_gate("There is a TODO here.")
        self.assertNotIn("cli_probe", [f["kind"] for f in result["semantic_flags"]])

    def test_add_check_with_terms_list_binds_it_and_reaches_the_gate(self):
        core_config.add_custom_term_list(self._tmp.name, "slopwatch", "jargon", {})
        _core_terms.add_term("slopwatch", {"jargon": {"label": "jargon", "polarity": "deny",
                                                        "accepts_additions": True}},
                              self._tmp.name, "jargon", "widget")
        fn_path = self._fn_body_file(
            'return [{"word": w} for w in extra if w in sentence.lower()]')
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(
                add_check="cli_jargon_probe", unit="sentence", catches="x", instead="y",
                fn_body_file=fn_path, terms_list="jargon"))
        self.assertEqual(code, 0)
        self.assertIn("bound to vocabulary list 'jargon'", out.getvalue())

        lists = core_config.custom_term_lists(self._tmp.name, "slopwatch")
        self.assertEqual(lists["jargon"]["feeds"], "cli_jargon_probe")

        result = _slopwatch.lint_and_gate("The system has a widget installed.")
        self.assertIn("cli_jargon_probe", [f["kind"] for f in result["semantic_flags"]])

    def test_add_check_with_a_terms_list_already_bound_elsewhere_is_rejected(self):
        core_config.add_custom_term_list(self._tmp.name, "slopwatch", "jargon", {},
                                          feeds="other_check")
        fn_path = self._fn_body_file("return []")
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(
                add_check="cli_probe", unit="sentence", catches="x", instead="y",
                fn_body_file=fn_path, terms_list="jargon"))
        self.assertEqual(code, 1)
        self.assertIn("already feeds", err.getvalue())
        self.assertNotIn("cli_probe", _slopwatch.custom_check_ids())

    def test_add_check_without_fn_body_file_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(add_check="cli_probe", unit="sentence"))
        self.assertEqual(code, 1)
        self.assertIn("--fn-body-file", err.getvalue())

    def test_remove_check_refuses_a_built_in(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(remove_check="stock_adverb"))
        self.assertEqual(code, 1)
        self.assertIn("Not saved", err.getvalue())

    def test_update_check_replaces_the_matcher(self):
        fn_path = self._fn_body_file('return []')
        stopslop.cmd_checks(_checks_args(add_check="cli_probe", unit="sentence",
                                          fn_body_file=fn_path))
        fn_path2 = self._fn_body_file(
            'return [{"phrase": "TODO"}] if "TODO" in sentence else []')
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(update_check="cli_probe", unit="sentence",
                                                      fn_body_file=fn_path2))
        self.assertEqual(code, 0)
        self.assertIn("Updated check 'cli_probe'", out.getvalue())
        result = _slopwatch.lint_and_gate("There is a TODO here.")
        self.assertIn("cli_probe", [f["kind"] for f in result["semantic_flags"]])

    def test_no_args_lists_every_check(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args())
        self.assertEqual(code, 0)
        self.assertIn("em_dash_cluster", out.getvalue())

    def test_listing_shows_each_checks_own_unit(self):
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_checks(_checks_args())
        self.assertIn("(unit=document, threshold=4, action=warn)", out.getvalue())  # em_dash_cluster

    def test_listing_shows_threshold_and_action_for_check_config_rulesets(self):
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_checks(_checks_args())
        text = out.getvalue()
        self.assertIn("threshold=4, action=warn", text)  # em_dash_cluster's default

    def test_enable_disables_every_other_check(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(enable=["em_dash_cluster"]))
        self.assertEqual(code, 0)
        self.assertIn("Enabled: em_dash_cluster", out.getvalue())

    def test_set_threshold_then_listing_reflects_it(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(set_threshold=["vague_intensifier=3"]))
        self.assertEqual(code, 0)
        self.assertIn("Set vague_intensifier threshold=3", out.getvalue())
        with redirect_stdout(io.StringIO()) as out2:
            stopslop.cmd_checks(_checks_args())
        self.assertIn("threshold=3", out2.getvalue())

    def test_set_action_then_listing_reflects_it(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(set_action=["vague_intensifier=block"]))
        self.assertEqual(code, 0)
        self.assertIn("Set vague_intensifier action=block", out.getvalue())
        with redirect_stdout(io.StringIO()) as out2:
            stopslop.cmd_checks(_checks_args())
        self.assertIn("action=block", out2.getvalue())

    def test_set_threshold_malformed_item_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(set_threshold=["not-a-pair"]))
        self.assertEqual(code, 1)
        self.assertIn("CHECK_ID=VALUE", err.getvalue())

    def test_set_threshold_non_integer_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(set_threshold=["vague_intensifier=many"]))
        self.assertEqual(code, 1)
        self.assertIn("whole number", err.getvalue())

    def test_set_action_invalid_value_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(set_action=["vague_intensifier=deny"]))
        self.assertEqual(code, 1)
        self.assertIn("block", err.getvalue())
        self.assertIn("warn", err.getvalue())

    def test_unknown_check_id_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(set_threshold=["__not_real__=3"]))
        self.assertEqual(code, 1)
        self.assertIn("unknown check id", err.getvalue())

    def test_ste100_takes_per_check_settings_like_every_other_ruleset(self):
        """ste100 was the last ruleset without check_config -- the one
        this command used to reject with "no per-check threshold/action".
        That special case is gone; a fourth ruleset shipping without the
        capability still gets the rejection (cmd_checks gates on
        CAPABILITIES), but nothing shipped exercises it any more."""
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(
                ruleset="ste100", set_threshold=["length=3"]))
        self.assertEqual(code, 0)
        self.assertIn("Set length threshold=3", out.getvalue())

    def test_set_param_reaches_a_checks_own_extra_number(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args(
                ruleset="ste100", set_param=["length.procedure_word_limit=18"]))
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("Set length procedure_word_limit=18", text)
        self.assertIn("procedure_word_limit=18", text.split("\n", 1)[1])

    def test_set_param_on_a_check_without_that_param_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(
                ruleset="ste100", set_param=["modal.procedure_word_limit=18"]))
        self.assertEqual(code, 1)
        self.assertIn("unknown setting", err.getvalue())


def _packs_args(**overrides):
    defaults = dict(glob=None, list=None, enable=None, add_pack=None, name=None,
                     source=None, license=None, content_kind=None, terms_file=None,
                     remove_pack=None)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class CmdPacksAddRemoveTests(unittest.TestCase):
    """--add-pack/--remove-pack, isolated the same way
    core/test_glossary_packs_custom.py's own _TempCustomPacksDir is --
    glossary_packs._CUSTOM_PACKS_DIR is a module-level constant computed
    at import time, not parameterized by REPO_ROOT, so this is the
    correct seam rather than patching stopslop.REPO_ROOT (which would do
    nothing for this particular write)."""

    def setUp(self):
        from core import glossary_packs
        self._glossary_packs = glossary_packs
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_dir = glossary_packs._CUSTOM_PACKS_DIR
        glossary_packs._CUSTOM_PACKS_DIR = self._tmp.name

    def tearDown(self):
        self._glossary_packs._CUSTOM_PACKS_DIR = self._orig_dir
        self._tmp.cleanup()

    def _terms_file(self, text):
        path = os.path.join(self._tmp.name, "terms.txt")
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_add_pack_then_visible_and_removable(self):
        terms_path = self._terms_file("widget: a small mechanism\ngizmo\n")
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_packs(_packs_args(
                add_pack="cli-probe", name="CLI Probe", source="https://example.com",
                license="MIT", terms_file=terms_path))
        self.assertEqual(code, 0)
        self.assertIn("Added pack 'cli-probe'", out.getvalue())
        self.assertIn("cli-probe", self._glossary_packs.list_packs())

        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_packs(_packs_args(remove_pack="cli-probe"))
        self.assertEqual(code, 0)
        self.assertIn("Removed pack 'cli-probe'", out.getvalue())
        self.assertNotIn("cli-probe", self._glossary_packs.list_packs())

    def test_remove_pack_refuses_a_built_in(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_packs(_packs_args(remove_pack="mdn-glossary"))
        self.assertEqual(code, 1)
        self.assertIn("built-in", err.getvalue())


class CmdPacksTests(unittest.TestCase):
    """Packs attach to a path glob, so the command reports per rule."""

    def test_listing_names_each_pack_without_naming_a_consumer(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_packs(_packs_args())
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("nist-security", text)
        self.assertIn("any of these can feed any term list", text)

    def test_enable_without_a_glob_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_packs(_packs_args(list="project_terms", enable=["nist-security"]))
        self.assertEqual(code, 1)
        self.assertIn("--glob", err.getvalue())

    def test_enable_without_a_list_is_rejected(self):
        # A pack has no opinion about which list it feeds, so the command
        # cannot infer one.
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_packs(_packs_args(glob="*.md", enable=["nist-security"]))
        self.assertEqual(code, 1)
        self.assertIn("--list", err.getvalue())


class CmdListRulesetsAddRemoveTests(unittest.TestCase):
    """--add/--remove scaffold a whole ruleset package and register it
    LIVE in the process-global rulesets._REGISTRY -- there is no isolation
    seam around that registry (see rulesets/test_custom_rulesets_registry
    .py's own module docstring for why), so this touches the real repo's
    .claude/stopslop/custom_rulesets/ like those tests do, and cleans up
    the same way: always, in tearDown."""

    RULESET_ID = "cli_test_scratch_ruleset"

    def tearDown(self):
        from core import custom_rulesets as core_custom_rulesets
        if rulesets.is_custom_ruleset(self.RULESET_ID):
            rulesets.unregister_ruleset(self.RULESET_ID)
        core_custom_rulesets.remove_ruleset(stopslop.REPO_ROOT, self.RULESET_ID)

    def test_add_then_visible_and_removable(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_list_rulesets(SimpleNamespace(
                add=self.RULESET_ID, name="Scratch", remove=None))
        self.assertEqual(code, 0)
        self.assertIn(f"Added ruleset {self.RULESET_ID!r}", out.getvalue())
        self.assertIn(self.RULESET_ID, out.getvalue())
        self.assertIn("[custom]", out.getvalue())

        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_list_rulesets(SimpleNamespace(
                add=None, name=None, remove=self.RULESET_ID))
        self.assertEqual(code, 0)
        confirmation, _, listing = out.getvalue().partition("\n")
        self.assertIn(f"Removed ruleset {self.RULESET_ID!r}", confirmation)
        self.assertNotIn(self.RULESET_ID, listing)

    def test_remove_refuses_a_built_in(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_list_rulesets(SimpleNamespace(
                add=None, name=None, remove="codewatch"))
        self.assertEqual(code, 1)
        self.assertIn("built-in", err.getvalue())

    def test_add_refuses_a_duplicate_id(self):
        stopslop.cmd_list_rulesets(SimpleNamespace(add=self.RULESET_ID, name=None, remove=None))
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_list_rulesets(SimpleNamespace(
                add=self.RULESET_ID, name=None, remove=None))
        self.assertEqual(code, 1)
        self.assertIn("already exists", err.getvalue())


class VersionTests(unittest.TestCase):
    def test_version_string_is_importable(self):
        self.assertRegex(stopslop.VERSION, r"^\d+\.\d+\.\d+$")

    def test_version_flag_prints_it_and_exits_cleanly(self):
        proc = subprocess.run([sys.executable, stopslop.__file__, "--version"],
                               capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0)
        self.assertIn(stopslop.VERSION, proc.stdout)


if __name__ == "__main__":
    unittest.main()


class RulesCommandTests(unittest.TestCase):
    """`stopslop rules` prints this project's own free alternative to
    itself.

    The 2026-09-01 instructed run measured a stated rule at about half
    the gate's effect for one generation and no install. A project that
    hides that from its users is not being honest about its evidence, so
    the command is part of the contract, not a convenience.
    """

    def _run(self, *extra):
        proc = subprocess.run(
            [sys.executable, os.path.join(stopslop.REPO_ROOT, "stopslop.py"), "rules",
             *extra],
            capture_output=True, text=True, cwd=stopslop.REPO_ROOT)
        return proc

    def test_it_prints_a_rule_for_every_enabled_check(self):
        import rulesets as _rulesets
        ruleset = _rulesets.get_ruleset("slopwatch")
        enabled = [cid for cid, meta in ruleset.list_checks().items()
                    if meta.get("enabled", True)]
        proc = self._run("--ruleset", "slopwatch", "--quiet")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        bullets = [ln for ln in proc.stdout.splitlines() if ln.startswith("- ")]
        self.assertEqual(len(bullets), len(enabled))

    def test_a_disabled_check_is_not_asked_for(self):
        """An instruction naming a check this project switched off asks
        for something nothing here enforces."""
        import rulesets as _rulesets
        ruleset = _rulesets.get_ruleset("slopwatch")
        table = ruleset.list_checks()
        off = [cid for cid, meta in table.items() if not meta.get("enabled", True)]
        if not off:
            self.skipTest("no disabled check in slopwatch right now")
        proc = self._run("--ruleset", "slopwatch", "--quiet")
        for check_id in off:
            instead = (table[check_id].get("instead") or "").strip()
            if instead:
                self.assertNotIn(instead, proc.stdout)

    def test_quiet_prints_only_the_block(self):
        proc = self._run("--ruleset", "slopwatch", "--quiet")
        self.assertEqual(proc.stderr.strip(), "")
        self.assertIn("## Writing rules", proc.stdout)

    def test_it_says_where_the_block_came_from(self):
        """Pasted into a CLAUDE.md, the block outlives the memory of how
        it was produced. It has to carry its own regeneration command."""
        proc = self._run("--ruleset", "slopwatch", "--quiet")
        self.assertIn("stopslop.py rules --ruleset slopwatch", proc.stdout)


class RulesComplementTests(unittest.TestCase):
    """`rules --complement` prints what the gate will NOT deny on.

    Six rounds found that held-out checks never improve under a gate.
    They do, the moment something tells the model about them: an
    instruction aimed at the gate's blind spot took held-out flags from
    25 to 11 (14-2, p = 0.004) and total tells from 30 to 13 (17-2,
    p = 0.0007). An instruction that repeats what the gate enforces adds
    almost nothing.
    """

    def _run(self, *extra):
        return subprocess.run(
            [sys.executable, os.path.join(stopslop.REPO_ROOT, "stopslop.py"),
             "rules", *extra],
            capture_output=True, text=True, cwd=stopslop.REPO_ROOT)

    def _bullets(self, text):
        return [line for line in text.splitlines() if line.startswith("- ")]

    def test_it_omits_every_blocking_check(self):
        import rulesets as _rulesets
        ruleset = _rulesets.get_ruleset("codewatch")
        config = ruleset.list_check_config()
        blocking = [cid for cid, spec in config.items()
                     if spec.get("action") == "block"]
        self.assertTrue(blocking, "codewatch should block at least one check")
        table = ruleset.list_checks()
        out = self._run("--ruleset", "codewatch", "--complement", "--quiet")
        self.assertEqual(out.returncode, 0, out.stderr)
        for check_id in blocking:
            instead = (table[check_id].get("instead") or "").strip()
            if instead:
                self.assertNotIn(instead, out.stdout)

    def test_it_keeps_every_non_blocking_check(self):
        import rulesets as _rulesets
        ruleset = _rulesets.get_ruleset("codewatch")
        config = ruleset.list_check_config()
        warning = [cid for cid, spec in ruleset.list_checks().items()
                    if spec.get("enabled", True)
                    and config.get(cid, {}).get("action") != "block"]
        out = self._run("--ruleset", "codewatch", "--complement", "--quiet")
        self.assertEqual(len(self._bullets(out.stdout)), len(warning))

    def test_it_is_strictly_smaller_than_the_full_block(self):
        full = self._run("--ruleset", "codewatch", "--quiet").stdout
        part = self._run("--ruleset", "codewatch", "--complement", "--quiet").stdout
        self.assertLess(len(self._bullets(part)), len(self._bullets(full)))

    def test_the_regeneration_command_records_the_flag(self):
        """A pasted block outlives the memory of how it was made, and
        regenerating it WITHOUT --complement would silently swap it for
        the arm that barely stacks."""
        out = self._run("--ruleset", "codewatch", "--complement", "--quiet")
        self.assertIn("--complement", out.stdout)

    def test_a_ruleset_that_blocks_nothing_says_so(self):
        """slopwatch warns on everything, so its complement is every
        check -- true, and useless unless the reason is stated."""
        out = self._run("--ruleset", "slopwatch", "--complement")
        self.assertIn("denies nothing", out.stderr)


class InitRecommendsTheComplementTests(unittest.TestCase):
    """`init` used to hand out the dominated configuration.

    A gate alone costs more than a gate plus an instruction and delivers
    less than half as much (30 total tells against 13, p = 0.0007). A
    user who runs init and reads no further gets the worse one, from the
    command whose whole job is setting them up correctly.
    """

    def _init_source(self):
        with open(os.path.join(stopslop.REPO_ROOT, "stopslop.py")) as f:
            text = f.read()
        start = text.index("def cmd_init(")
        end = text.index("\ndef ", start + 1)
        return text[start:end]

    def test_init_points_at_the_complement_not_plain_rules(self):
        source = self._init_source()
        self.assertIn("rules --complement", source)

    def test_it_says_why_rather_than_just_issuing_an_order(self):
        """A step with no reason attached is the first thing a reader
        skips."""
        source = self._init_source()
        self.assertIn("0.0007", source)

    def test_it_cites_a_findings_file_that_exists(self):
        source = self._init_source()
        cited = re.findall(r"evalab-runs/[\w.-]+/FINDINGS\.md", source)
        self.assertTrue(cited)
        for rel in cited:
            self.assertTrue(
                os.path.exists(os.path.join(stopslop.REPO_ROOT, rel)), rel)


class NoStrayModulesTests(unittest.TestCase):
    """The repository root holds one Python file.

    An agentic generator writes files where it was started. Two codewatch
    runs left twenty modules in the root, and `git add -A` committed them
    -- once in 422ced2, and again in the commit that was supposed to fix
    it. Runs are sandboxed now; this is the check that says so.
    """

    def test_the_root_holds_only_stopslop(self):
        root = stopslop.REPO_ROOT
        found = sorted(name for name in os.listdir(root)
                        if name.endswith(".py")
                        and os.path.isfile(os.path.join(root, name)))
        self.assertEqual(found, ["stopslop.py"],
                          "stray modules in the repository root -- an "
                          "agentic run wrote them and they are not this "
                          "project's code")

    def test_gitignore_guards_the_root(self):
        """A test catches them after the fact. The ignore rule keeps them
        out of a commit in the first place, which is where the damage
        actually happened."""
        with open(os.path.join(stopslop.REPO_ROOT, ".gitignore")) as f:
            text = f.read()
        self.assertIn("/*.py", text)
        self.assertIn("!/stopslop.py", text)


class ReadmeRunCountTests(unittest.TestCase):
    """The README's run count has drifted three times.

    It is the first number a reader checks against the directory listing,
    and every time a run is added or an invalid one is deleted it goes
    stale silently. Prose cannot be trusted to track a directory.
    """

    WORDS = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
             13: "thirteen", 14: "fourteen", 15: "fifteen",
             16: "sixteen", 17: "seventeen", 18: "eighteen"}

    def _actual(self):
        runs = os.path.join(stopslop.REPO_ROOT, "evalab-runs")
        return len(glob.glob(os.path.join(runs, "*", "result.json"))) + \
            len(glob.glob(os.path.join(runs, "*", "*", "result.json")))

    def test_the_readme_names_the_number_of_runs_on_disk(self):
        count = self._actual()
        word = self.WORDS.get(count)
        self.assertIsNotNone(word, f"extend WORDS for {count} runs")
        with open(os.path.join(stopslop.REPO_ROOT, "README.md")) as f:
            text = f.read().lower()
        self.assertIn(f"{word} committed runs", text,
                       f"{count} runs on disk; the README says otherwise")

    def test_it_names_no_other_count(self):
        """A stale second mention is how the first one stayed wrong."""
        count = self._actual()
        with open(os.path.join(stopslop.REPO_ROOT, "README.md")) as f:
            text = f.read().lower()
        for other, word in self.WORDS.items():
            if other != count:
                self.assertNotIn(f"{word} committed runs", text,
                                  f"README also claims {word} runs")


class DocumentedCommandsTests(unittest.TestCase):
    """The README's command list drifts in both directions.

    It documented `options` for weeks after that command was removed --
    a reader following it gets an argparse error -- and omitted
    `rule-checks` from the day it was added. Neither is visible without
    comparing the two by hand.
    """

    def _registered(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(stopslop.REPO_ROOT, "stopslop.py"),
             "--help"], capture_output=True, text=True,
            cwd=stopslop.REPO_ROOT)
        match = re.search(r"\{([a-z,\-]+)\}", proc.stdout)
        self.assertIsNotNone(match, "could not read the subcommand list")
        return sorted(match.group(1).split(","))

    def _readme(self):
        with open(os.path.join(stopslop.REPO_ROOT, "README.md")) as f:
            return f.read()

    def test_every_command_is_documented(self):
        readme = self._readme()
        for command in self._registered():
            self.assertIn(f"stopslop.py {command}", readme,
                           f"{command} is registered but the README never "
                           "mentions it")

    def test_the_readme_documents_no_command_that_does_not_exist(self):
        """Worse than an omission: a reader who follows it gets an
        error from the tool that told them to."""
        registered = set(self._registered())
        documented = set(re.findall(r"stopslop\.py ([a-z][a-z-]+)",
                                     self._readme()))
        # `--version` and prose like "stopslop.py init" inside sentences
        # both land here; only real-looking subcommands matter.
        stale = {c for c in documented - registered if "-" in c or c.isalpha()}
        stale -= {"py"}
        self.assertEqual(stale, set(),
                          "README documents commands that do not exist")
