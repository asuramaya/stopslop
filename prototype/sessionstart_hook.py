#!/usr/bin/env python3
"""SessionStart hook: for every registered ruleset, if its
.claude/<ruleset_id>-memory.md exists, inject it as additional context so
the model starts the session already primed against its own recent
gate-denial patterns for that ruleset. Closes the loop: gate denies ->
logged -> aggregated into memory -> read back in at the next session start.

Also runs the integrity check (integrity_check.py) against the gate's own
trust anchors -- see that module's docstring for why -- and prepends any
drift warning to the same additionalContext block.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity_check
import rulesets
from core import paths


def _memory_path(project_root, ruleset_id):
    return os.path.join(project_root, ".claude", f"{ruleset_id}-memory.md")


def main():
    project_root = paths.find_project_root(__file__)
    sections = []

    warnings = integrity_check.check_and_update()
    if warnings:
        sections.append(
            "# stopslop Integrity Warning\n"
            "One or more gate trust-anchor files changed since the last "
            "session start, outside this hook's own knowledge of why:\n"
            + "\n".join(f"- {w}" for w in warnings)
        )

    for ruleset in rulesets.list_rulesets():
        memory_file = _memory_path(project_root, ruleset.RULESET_ID)
        if os.path.exists(memory_file):
            with open(memory_file) as f:
                content = f.read().strip()
            if content:
                sections.append(content)

    if not sections:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(sections),
        }
    }))


if __name__ == "__main__":
    main()
