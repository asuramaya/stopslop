#!/usr/bin/env python3
"""Direct-function tests for stopslop.py's ruleset-resolution and
capability-gating logic -- the CLI dispatcher itself still has no
end-to-end subprocess test coverage (see README's gap list), but the two
pieces of genuinely new logic the pluggable-ruleset refactor added
(_resolve's explicit-vs-config-driven resolution, _require_glossary's
capability gate) are exercised directly here against the real registered
rulesets (ste100 has "glossary", slopwatch doesn't -- a real fixture
already on hand, not a mock).

Run with:
    python3 -m unittest test_stopslop -v
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace

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
        # Not README.md -- that's a real slopwatch default now (see
        # test_root_readme_resolves_to_slopwatch below); this checks
        # generic *.md -> ste100 resolution.
        ruleset = stopslop._resolve(None, stopslop.REPO_ROOT + "/notes.md")
        self.assertEqual(ruleset.RULESET_ID, "ste100")

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
        self.assertEqual(ruleset.RULESET_ID, "ste100")

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
                     remove=None, force=None)
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
        _core_terms._migration_checked.clear()

    def tearDown(self):
        _slopwatch.paths.find_project_root = self._orig_find_root
        _core_terms._migration_checked.clear()
        self._tmp.cleanup()

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
    defaults = dict(ruleset="slopwatch", enable=None, set_threshold=None, set_action=None)
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

    def tearDown(self):
        _slopwatch.paths.find_project_root = self._orig_find_root
        self._tmp.cleanup()

    def test_no_args_lists_every_check(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_checks(_checks_args())
        self.assertEqual(code, 0)
        self.assertIn("em_dash_cluster", out.getvalue())

    def test_listing_shows_threshold_and_action_for_check_config_rulesets(self):
        with redirect_stdout(io.StringIO()) as out:
            stopslop.cmd_checks(_checks_args())
        text = out.getvalue()
        self.assertIn("threshold=4, action=block", text)  # em_dash_cluster's default

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

    def test_set_threshold_on_a_ruleset_without_check_config_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_checks(_checks_args(
                ruleset="ste100", set_threshold=["length=3"]))
        self.assertEqual(code, 1)
        self.assertIn("no per-check threshold/action", err.getvalue())


class CmdPacksTests(unittest.TestCase):
    """Packs attach to a path glob, so the command reports per rule."""

    def test_listing_names_each_pack_without_naming_a_consumer(self):
        with redirect_stdout(io.StringIO()) as out:
            code = stopslop.cmd_packs(SimpleNamespace(glob=None, list=None, enable=None))
        self.assertEqual(code, 0)
        text = out.getvalue()
        self.assertIn("nist-security", text)
        self.assertIn("any of these can feed any term list", text)

    def test_enable_without_a_glob_is_rejected(self):
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_packs(SimpleNamespace(
                glob=None, list="project_terms", enable=["nist-security"]))
        self.assertEqual(code, 1)
        self.assertIn("--glob", err.getvalue())

    def test_enable_without_a_list_is_rejected(self):
        # A pack has no opinion about which list it feeds, so the command
        # cannot infer one.
        with redirect_stderr(io.StringIO()) as err:
            code = stopslop.cmd_packs(SimpleNamespace(
                glob="*.md", list=None, enable=["nist-security"]))
        self.assertEqual(code, 1)
        self.assertIn("--list", err.getvalue())


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
