#!/usr/bin/env python3
"""Builds the status summary both stopslop.py's `status` command and
mcp_server.py's status tool show -- one function, so the CLI and the MCP
server can't quietly start disagreeing about what "status" means, the same
reason blocking_semantic_flags exists as a shared function in ste100_lint.py
instead of two independent copies.
"""
import json
import os
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_LOG = os.path.join(REPO_ROOT, ".claude", "ste100-history.log")
MEMORY_PATH = os.path.join(REPO_ROOT, ".claude", "ste100-memory.md")
INTEGRITY_PATH = os.path.join(REPO_ROOT, ".claude", "ste100-integrity.json")
SETTINGS_REAL = os.path.join(REPO_ROOT, ".claude", "settings.local.json")


def _read_history():
    if not os.path.exists(HISTORY_LOG):
        return []
    events = []
    with open(HISTORY_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def build_status_report():
    import ste100_lint as lint

    events = _read_history()
    action_counts = dict(Counter(e.get("action") for e in events))

    pattern_count = 0
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH) as f:
            pattern_count = f.read().count("\n- (")

    return {
        "approved_word_count": len(lint.APPROVED_WORDS),
        "forbidden_word_count": len(lint.UNAPPROVED_MAP) + len(lint.UNAPPROVED_NO_REPLACEMENT),
        "project_term_count": len(lint.PROJECT_TERMS),
        "gate_event_count": len(events),
        "gate_event_counts_by_action": action_counts,
        "coaching_memory_pattern_count": pattern_count,
        "integrity_baseline_recorded": os.path.exists(INTEGRITY_PATH),
        "hook_configured": os.path.exists(SETTINGS_REAL),
    }


def format_status_report(report):
    lines = ["stopslop status", ""]
    lines.append(f"Dictionary:      {report['approved_word_count']} approved words, "
                  f"{report['forbidden_word_count']} forbidden words")
    lines.append(f"Project terms:   {report['project_term_count']} registered "
                  f"(prototype/ste100-project-terms.json)")
    lines.append(f"\nGate activity:   {report['gate_event_count']} event(s) logged")
    for action in ("deny", "auto_fix", "clean", "unscoped_write", "register_term"):
        count = report["gate_event_counts_by_action"].get(action)
        if count:
            lines.append(f"  {action:16s} {count}")
    if report["coaching_memory_pattern_count"]:
        lines.append(f"\nCoaching memory: {report['coaching_memory_pattern_count']} recurring "
                      f"pattern(s) tracked (.claude/ste100-memory.md)")
    else:
        lines.append("\nCoaching memory: none yet -- no gate activity logged so far")
    lines.append(f"\nIntegrity:       "
                  f"{'baseline recorded' if report['integrity_baseline_recorded'] else 'not established yet -- start a session to record one'}")
    lines.append(f"Hook wiring:     "
                  f"{'configured' if report['hook_configured'] else 'NOT SET UP -- run `stopslop.py init`'}")
    return "\n".join(lines)
