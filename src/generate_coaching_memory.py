#!/usr/bin/env python3
"""Reads .claude/stopslop-history.log (written via core.history.log_event on
every deny/auto_fix event) and generates a per-ruleset coaching primer,
.claude/<ruleset_id>-memory.md: a short, principle-level summary of
recurring violation patterns for that ruleset (abstract patterns, not word
lists, kept small enough to be cheap to inject at session start).

Generalized during the pluggable-ruleset refactor from a single ste100-only
script: the history log is now shared across rulesets (see core/history.py),
so events are filtered by the "ruleset" field before counting, and each
ruleset's own CHECKS supplies the facts this file writes prose from. Kept as SEPARATE
files per ruleset rather than one merged memory, on purpose: two rulesets
with opposite writing philosophies (STE100 erases individual voice on
purpose; rulesets/slopwatch protects it) would produce contradictory-sounding
advice if concatenated into a single primer. ste100's own memory file keeps
its pre-refactor name (.claude/ste100-memory.md) -- no rename needed, it
already matches the new convention.
"""
import os
import sys
from collections import Counter

from core import history, paths
import rulesets


def _memory_path(project_root, ruleset_id):
    return os.path.join(project_root, ".claude", f"{ruleset_id}-memory.md")


def regenerate(ruleset_id, project_root=None):
    """Does the actual work, silently -- no stdout/stderr output. Returns a
    short status string ('no-log', 'no-violations', or 'wrote:<path>') for
    the caller to report however fits its own context. Split out from
    main() so pretool_hook.py can call this inline after every gate event
    (PostToolUse never fires after a PreToolUse denial, so this can't run
    as a separate hook without missing every deny -- exactly the event this
    coaching loop most needs to learn from). A print() here would corrupt
    pretool_hook.py's own stdout, which Claude Code parses as the hook's
    JSON response -- silence is required, not just tidy."""
    if project_root is None:
        project_root = paths.find_project_root(__file__)
    history_path = history.history_log_path(project_root)
    if not os.path.exists(history_path):
        return "no-log"

    events = [e for e in history.read_history_deduped(history_path)
              if e.get("ruleset", "ste100") == ruleset_id]

    kind_counts = Counter()
    for e in events:
        for k in e.get("kinds", []):
            kind_counts[k] += 1

    if not kind_counts:
        return "no-violations"

    ruleset = rulesets.get_ruleset(ruleset_id)
    checks = getattr(ruleset, "CHECKS", {})

    ranked = kind_counts.most_common(5)  # keep it small -- ~200 token budget

    lines = [
        f"# {ruleset.RULESET_NAME} Coaching Memory (auto-generated)",
        f"# Based on {len(events)} gate event(s) in .claude/stopslop-history.log",
        "",
        "## Recurring patterns (highest frequency first)",
        "",
    ]
    # This file is the one place the coaching voice belongs, and the "(12x)"
    # prefix is what earns it: a real count is the evidence that something
    # keeps recurring. The ruleset stores the two bare facts (what the check
    # catches, what to do instead) and each consumer writes its own sentence
    # -- the dashboard's Checks table is describing a setting, not scolding.
    for kind, count in ranked:
        catches, instead = checks.get(kind, (f"'{kind}' violations", ""))
        lines.append(f"- ({count}x) {catches}" + (f" -- {instead}." if instead else "."))

    content = "\n".join(lines) + "\n"
    memory_path = _memory_path(project_root, ruleset_id)
    os.makedirs(os.path.dirname(memory_path), exist_ok=True)
    with open(memory_path, "w") as f:
        f.write(content)
    return f"wrote:{memory_path}"


def main():
    if len(sys.argv) < 2:
        print("usage: generate_coaching_memory.py RULESET_ID", file=sys.stderr)
        return 1
    ruleset_id = sys.argv[1]
    status = regenerate(ruleset_id)
    if status == "no-log":
        print("No history log yet -- nothing to summarize.", file=sys.stderr)
    elif status == "no-violations":
        print(f"History log has no violation events yet for ruleset {ruleset_id!r}.", file=sys.stderr)
    else:
        path = status.split(":", 1)[1]
        with open(path) as f:
            content = f.read()
        print(f"Wrote {path} ({len(content.split())} words, ~{len(content)//4} tokens)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
