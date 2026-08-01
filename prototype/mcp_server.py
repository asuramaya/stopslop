#!/usr/bin/env python3
"""MCP server exposing stopslop's convenience layer as model-callable
tools. This is deliberately NOT the enforcement mechanism -- see
prototype/pretool_hook.py for that. The distinction matters: a hook sits
in front of the built-in Write/Edit/Bash tools and can deny a call before
it happens, whether or not the model wants that to happen. An MCP tool is
something the model chooses to call; nothing here can stop a model from
writing a file directly instead of checking it first. That's not a gap to
close -- it's the same "priming reduces retries, it does not replace the
gate" distinction the SKILL.md priming skill already states about itself.
These tools exist to reduce retries against the live gate, not to
duplicate or substitute for it.

Every tool here is a thin wrapper around the SAME functions the CLI
(stopslop.py) and the hook (pretool_hook.py) use -- ste100_lint's
lint_and_gate/blocking_semantic_flags, register_term.register(),
status_report.build_status_report() -- never a second copy of any of that
logic. A duplicated copy is a copy that can silently drift from the real
gate's behavior, which is exactly the failure mode that made
stopslop.py's own `lint` command briefly report a false FAIL on this
project's own clean README (see project memory).

Run directly for local testing:
    python3 mcp_server.py
Configured for Claude Code via .mcp.json at the repo root.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ste100_lint as lint
import register_term
import status_report

from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="stopslop",
    description="Convenience tools for the STE100 Gatekeeper System prototype. "
                 "Checking text here does not write it anywhere and carries no "
                 "enforcement guarantee -- the live PreToolUse hook is what "
                 "actually blocks a bad write, regardless of whether these tools "
                 "were used first.",
)


def _flag_summary(flags):
    out = []
    for f in flags:
        d = f["detail"]
        label = d.get("word") or d.get("phrase") or d.get("modal") or d.get("rule", "?")
        entry = {"kind": f["kind"], "rule": d.get("rule"), "text": label}
        note = d.get("note") or d.get("basis")
        if note:
            entry["note"] = note
        replacement = d.get("replacement")
        if replacement:
            entry["replacement"] = replacement
        out.append(entry)
    return out


@mcp.tool()
def lint_text(text: str, context: str = "description") -> dict:
    """Check text against the real ASD-STE100 rules without writing it
    anywhere. Use this before a real Write/Edit to see what the live gate
    would do, and cut down on denied attempts -- it does NOT replace the
    gate; the actual write still goes through the hook regardless of this
    tool's result. context="procedure" applies the stricter 20-word
    sentence limit real ASD-STE100 step-by-step instructions use;
    "description" (default) is the 25-word limit the live gate applies to
    whole documents.
    """
    if context not in ("procedure", "description"):
        context = "description"
    result = lint.lint_and_gate(text, context=context)
    blocking = lint.blocking_semantic_flags(result["semantic_flags"])
    return {
        "would_pass_live_gate": len(blocking) == 0,
        "blocking_issues": _flag_summary(blocking),
        "mechanical_fixes_on_real_write": _flag_summary(result["mechanical_violations"]),
    }


@mcp.tool()
def check_word(word: str) -> dict:
    """Look up a single word against the real ASD-STE100 dictionary and
    this project's own glossary. Returns whether it's approved, forbidden
    (with a replacement if the standard gives one), a registered project
    term, or simply not covered by either. Cheaper than lint_text when all
    you need is one word's status, e.g. before choosing how to phrase a
    sentence.
    """
    violations = lint.check_vocabulary(word)
    lw = word.strip().lower()
    if not violations:
        if lw in lint.PROJECT_TERMS:
            return {"word": word, "status": "project_term",
                    "note": lint.PROJECT_TERMS[lw].get("note", "")}
        return {"word": word, "status": "approved"}
    v = violations[0]
    return {
        "word": word,
        "status": v["type"],
        "replacement": v.get("replacement"),
        "rule": v.get("rule"),
    }


@mcp.tool()
def register_project_term(word: str, note: str = "", override_unapproved: str = "") -> dict:
    """Add a word to this project's Tier 2 glossary so the gate stops
    flagging it -- for genuine domain vocabulary the aviation-scoped
    ASD-STE100 standard was never going to cover (e.g. "repository",
    "API"). Registration is meant to be deliberate: confirm with the
    person you're working with before calling this, the same way the
    project's own workflow does it (ask, then register on approval), even
    though this tool itself doesn't enforce that step. Refuses a word the
    real dictionary already forbids unless override_unapproved gives an
    explicit reason -- that's overriding a real rule, not filling a
    coverage gap, and needs to be a deliberate, on-the-record choice.
    """
    return register_term.register(word, note, override_unapproved or None)


@mcp.tool()
def unregister_project_term(word: str) -> dict:
    """Remove a word from this project's Tier 2 glossary -- undoes a
    mistaken register_project_term call. The gate goes back to flagging
    the word normally.
    """
    return register_term.unregister(word)


@mcp.tool()
def list_project_terms() -> dict:
    """Every word currently registered in this project's Tier 2 glossary,
    with the note it was registered under and whether it overrides a real
    ASD-STE100 prohibition.
    """
    return {"terms": register_term.list_terms()}


@mcp.tool()
def get_status() -> dict:
    """Current state of the gate: dictionary size, project glossary size,
    how many gate events have been logged and what kind, whether an
    integrity baseline exists, and whether the hook is even wired up in
    this clone yet.
    """
    return status_report.build_status_report()


if __name__ == "__main__":
    mcp.run(transport="stdio")
