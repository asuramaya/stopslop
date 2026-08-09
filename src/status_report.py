#!/usr/bin/env python3
"""Builds the status summary stopslop.py's `status` command and
mcp_server.py's status tool show -- one function, so the CLI and the MCP
server can't quietly start disagreeing about what "status" means, the same
reason blocking_semantic_flags exists as a shared function instead of two
independent copies.

Generalized during the pluggable-ruleset refactor: the dictionary/glossary-
specific numbers used to be read directly from ste100_lint here; now each
registered ruleset supplies its own via an optional stats() function, and
this module only owns what's genuinely generic (gate-activity counts,
integrity/hook-wiring/config booleans).

Also fixes a real inconsistency found during that refactor: this reader
never applied the same double-fire dedup pretool_hook.py's own
count_consecutive_denials() already did, silently inflating activity counts
whenever a near-simultaneous duplicate log entry occurred. Both now go
through core.history.read_history_deduped(), so they can't diverge again.
"""
import functools
import json
import os
import subprocess
from collections import Counter

import dashboard_launch
from core import config as core_config
from core import history, paths
from core import text as core_text
from core.version import VERSION
import rulesets

_PRECOMMIT_MARKER = "installed by stopslop.py init"


def _precommit_hook_installed(project_root):
    hook_path = os.path.join(project_root, ".git", "hooks", "pre-commit")
    if not os.path.exists(hook_path):
        return False
    try:
        with open(hook_path) as f:
            return _PRECOMMIT_MARKER in f.read()
    except OSError:
        return False


def _importable(venv_python, module_name, timeout=5):
    try:
        result = subprocess.run([venv_python, "-c", f"import {module_name}"],
                                 capture_output=True, timeout=timeout)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@functools.lru_cache(maxsize=8)
def _venv_status(project_root):
    """`(venv_present, mcp_installed, streamlit_installed)` -- checked by
    actually asking the venv's own interpreter to import each package,
    not by guessing from whether the directory exists, since a `pip
    install` interrupted partway through (no network, disk full) is a
    real state a directory-exists check alone would miss.

    Cached, unlike everything else this module reads -- `build_status_report`
    runs on every dashboard render (dashboard.py's status footer and
    first-run notice both call it, on every page interaction, not just on
    a timer), and this is the one fact here that a running process can't
    see change out from under it: nothing re-runs `pip install` mid-session.
    Two subprocess spawns per render would be a real, silent latency
    regression on a UI that renders on every interaction -- everything
    else in this report (config, gate activity, hook wiring) stays
    uncached on purpose, same reasoning core/config.py's own module
    docstring already gives for rereading fresh."""
    venv_python = dashboard_launch.venv_python_path(project_root)
    if not os.path.exists(venv_python):
        return False, False, False
    return True, _importable(venv_python, "mcp"), _importable(venv_python, "streamlit")


def _mcp_trust_status(project_root):
    settings_path = os.path.join(project_root, ".claude", "settings.local.json")
    if not os.path.exists(settings_path):
        return "hook not wired up yet -- run `stopslop.py init`"
    try:
        with open(settings_path) as f:
            settings = json.load(f)
    except (OSError, ValueError):
        return "unknown -- .claude/settings.local.json unreadable"
    if "stopslop" in settings.get("enabledMcpjsonServers", []):
        return "trusted"
    return ("not yet approved -- Claude Code asks whether to allow this project's "
            "MCP servers the first time you start a session here; say yes")


def build_status_report(project_root=None):
    if project_root is None:
        project_root = paths.find_project_root(__file__)

    history_path = history.history_log_path(project_root)
    events = history.read_history_deduped(history_path)
    action_counts = dict(Counter(e.get("action") for e in events))

    ruleset_reports = []
    for ruleset in rulesets.list_rulesets():
        memory_path = os.path.join(project_root, ".claude", f"{ruleset.RULESET_ID}-memory.md")
        pattern_count = 0
        if os.path.exists(memory_path):
            with open(memory_path) as f:
                pattern_count = f.read().count("\n- (")
        stats_fn = getattr(ruleset, "stats", None)
        ruleset_reports.append({
            "id": ruleset.RULESET_ID,
            "name": ruleset.RULESET_NAME,
            "capabilities": sorted(ruleset.CAPABILITIES),
            "stats": stats_fn() if stats_fn else {},
            "coaching_memory_pattern_count": pattern_count,
        })

    integrity_path = os.path.join(project_root, ".claude", "stopslop-integrity.json")
    settings_path = os.path.join(project_root, ".claude", "settings.local.json")
    config_path = core_config.config_path(project_root)
    venv_present, mcp_installed, streamlit_installed = _venv_status(project_root)

    return {
        "version": VERSION,
        "rulesets": ruleset_reports,
        "gate_event_count": len(events),
        "gate_event_counts_by_action": action_counts,
        "integrity_baseline_recorded": os.path.exists(integrity_path),
        "hook_configured": os.path.exists(settings_path),
        "config_file_present": os.path.exists(config_path),
        "stray_config_keys": core_config.stray_top_level_keys(project_root),
        "orphaned_rule_extras": core_config.orphaned_rule_extras(project_root, rulesets),
        "precommit_hook_installed": _precommit_hook_installed(project_root),
        "venv_present": venv_present,
        "mcp_package_installed": mcp_installed,
        "streamlit_installed": streamlit_installed,
        "mcp_trust": _mcp_trust_status(project_root),
        "dashboard_reachable": dashboard_launch.is_alive(),
    }


def format_status_report(report):
    lines = [f"stopslop status (v{report['version']})", ""]

    for rs in report["rulesets"]:
        lines.append(f"Ruleset: {rs['name']} ({rs['id']}) -- capabilities: "
                      f"{', '.join(rs['capabilities']) or 'none'}")
        for key, value in rs["stats"].items():
            lines.append(f"  {key.replace('_', ' '):24s} {value}")
        if rs["coaching_memory_pattern_count"]:
            lines.append(f"  {'coaching memory patterns':24s} "
                          f"{rs['coaching_memory_pattern_count']} (.claude/{rs['id']}-memory.md)")
        lines.append("")

    lines.append(f"Gate activity:   {core_text.n(report['gate_event_count'], 'event')} logged")
    for action in ("deny", "auto_fix", "clean", "unscoped_write", "register_term", "unregister_term"):
        count = report["gate_event_counts_by_action"].get(action)
        if count:
            lines.append(f"  {action:16s} {count}")

    lines.append(f"\nConfig:          "
                  f"{'stopslop.config.json present' if report['config_file_present'] else 'not present -- using default rules (ste100 on .md/.txt/.rst)'}")
    if report["stray_config_keys"]:
        lines.append(f"  WARNING: no reader consumes: {', '.join(report['stray_config_keys'])} "
                      f"-- left over from a removed feature, tuning nothing. "
                      f"Run `stopslop.py status --clean-config` to drop them.")
    for entry in report["orphaned_rule_extras"]:
        bits = []
        if "packs" in entry:
            bits.append(f"packs on {core_text.n(len(entry['packs']), 'list')}: "
                        f"{', '.join(entry['packs'])}")
        if "disable" in entry:
            bits.append(f"disable {', '.join(entry['disable'])}")
        lines.append(f"  WARNING: {entry['glob']} carries {'; '.join(bits)} that no ruleset "
                      f"it invokes recognizes -- left over from an earlier ruleset/"
                      f"embedded_prose on this rule. Run `stopslop.py status "
                      f"--clean-config` to drop them.")
    lines.append(f"Integrity:       "
                  f"{'baseline recorded' if report['integrity_baseline_recorded'] else 'not established yet -- start a session to record one'}")
    lines.append(f"Hook wiring:     "
                  f"{'configured' if report['hook_configured'] else 'NOT SET UP -- run `stopslop.py init`'}")

    lines.append("\nInstallation (optional pieces -- the gate above works without any of this):")
    lines.append(f"  Pre-commit gate:  "
                  f"{'installed' if report['precommit_hook_installed'] else 'NOT INSTALLED -- run `stopslop.py init`'}")
    if not report["venv_present"]:
        lines.append("  Virtualenv:       NOT SET UP -- needed for MCP tools and the dashboard. "
                      "Run `stopslop.py init` (or by hand: python3 -m venv .venv && "
                      ".venv/bin/pip install -r requirements.txt)")
    elif not (report["mcp_package_installed"] and report["streamlit_installed"]):
        missing = [name for name, ok in (("mcp", report["mcp_package_installed"]),
                                          ("streamlit", report["streamlit_installed"])) if not ok]
        lines.append(f"  Virtualenv:       present, but missing: {', '.join(missing)} -- "
                      f"run .venv/bin/pip install -r requirements.txt")
    else:
        lines.append("  Virtualenv:       ready (mcp, streamlit both installed)")
    lines.append(f"  MCP trust:        {report['mcp_trust']}")
    lines.append(f"  Dashboard:        "
                  f"{'reachable at http://localhost:8501' if report['dashboard_reachable'] else 'not running -- starts automatically from an MCP session, or run `stopslop.py dashboard`'}")
    return "\n".join(lines)
