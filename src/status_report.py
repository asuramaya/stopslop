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
import os
from collections import Counter

from core import config as core_config
from core import history, paths
from core.version import VERSION
import rulesets


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

    return {
        "version": VERSION,
        "rulesets": ruleset_reports,
        "gate_event_count": len(events),
        "gate_event_counts_by_action": action_counts,
        "integrity_baseline_recorded": os.path.exists(integrity_path),
        "hook_configured": os.path.exists(settings_path),
        "config_file_present": os.path.exists(config_path),
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

    lines.append(f"Gate activity:   {report['gate_event_count']} event(s) logged")
    for action in ("deny", "auto_fix", "clean", "unscoped_write", "register_term", "unregister_term"):
        count = report["gate_event_counts_by_action"].get(action)
        if count:
            lines.append(f"  {action:16s} {count}")

    lines.append(f"\nConfig:          "
                  f"{'stopslop.config.json present' if report['config_file_present'] else 'not present -- using default rules (ste100 on .md/.txt/.rst)'}")
    lines.append(f"Integrity:       "
                  f"{'baseline recorded' if report['integrity_baseline_recorded'] else 'not established yet -- start a session to record one'}")
    lines.append(f"Hook wiring:     "
                  f"{'configured' if report['hook_configured'] else 'NOT SET UP -- run `stopslop.py init`'}")
    return "\n".join(lines)
