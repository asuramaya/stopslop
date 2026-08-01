#!/usr/bin/env python3
"""SessionStart hook: if .claude/ste100-memory.md exists, inject it as
additional context so the model starts the session already primed against
its own recent gate-denial patterns. Closes the loop: gate denies -> logged
-> aggregated into memory -> read back in at the next session start.

Also runs the integrity check (integrity_check.py) against the gate's own
trust anchors -- see that module's docstring for why -- and prepends any
drift warning to the same additionalContext block.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import integrity_check

PROJECT_ROOT = "/home/asuramaya/code/stopslop/"
MEMORY_FILE = os.path.join(PROJECT_ROOT, ".claude", "ste100-memory.md")


def main():
    sections = []

    warnings = integrity_check.check_and_update()
    if warnings:
        sections.append(
            "# STE100 Integrity Warning\n"
            "One or more gate trust-anchor files changed since the last "
            "session start, outside this hook's own knowledge of why:\n"
            + "\n".join(f"- {w}" for w in warnings)
        )

    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
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
