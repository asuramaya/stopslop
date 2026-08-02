#!/usr/bin/env python3
"""MCP server exposing stopslop's convenience layer as model-callable
tools. This is deliberately NOT the enforcement mechanism -- see
pretool_hook.py for that. The distinction matters: a hook sits in front of
the built-in Write/Edit/Bash tools and can deny a call before it happens,
whether or not the model wants that to happen. An MCP tool is something the
model chooses to call; nothing here can stop a model from writing a file
directly instead of checking it first. That's not a gap to close -- it's
the same "priming reduces retries, it does not replace the gate"
distinction the SKILL.md priming skill already states about itself. These
tools exist to reduce retries against the live gate, not to duplicate or
substitute for it.

Every tool here is a thin wrapper around the SAME functions the CLI
(stopslop.py) and the hook (pretool_hook.py) use -- each ruleset's own
lint_and_gate/blocking_semantic_flags, register_term()/check_word() when it
declares those capabilities, status_report.build_status_report() -- never a
second copy of any of that logic. A duplicated copy is a copy that can
silently drift from the real gate's behavior, which is exactly the failure
mode that made stopslop.py's own `lint` command briefly report a false FAIL
on this project's own clean README (see project memory).

Generalized during the pluggable-ruleset refactor: every tool now takes an
optional `ruleset` id, resolved the same way stopslop.py's CLI does (an
explicit id always wins; otherwise resolve through core.config.resolve_ruleset
against a synthetic <repo_root>/__stdin__.md path, since MCP calls don't
carry a real file path). A ruleset that doesn't declare a capability a tool
needs (glossary, word_lookup) gets a structured {"ok": False, "status":
"unsupported", ...} response, not an exception.

Run directly for local testing:
    python3 mcp_server.py
Configured for Claude Code via .mcp.json at the repo root.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rulesets
import status_report
from core import config as core_config
from core import paths

from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    name="stopslop",
    description="Convenience tools for stopslop, a pluggable writing-enforcement gate. "
                 "Checking text here does not write it anywhere and carries no "
                 "enforcement guarantee -- the live PreToolUse hook is what "
                 "actually blocks a bad write, regardless of whether these tools "
                 "were used first.",
)

REPO_ROOT = paths.find_project_root(__file__)
_SYNTHETIC_STDIN_PATH = os.path.join(REPO_ROOT, "__stdin__.md")


def _resolve(ruleset_id):
    """Same resolution stopslop.py's CLI uses: an explicit id always wins;
    otherwise resolve through the config-driven default (no real file path
    exists for an MCP call, so this always uses the synthetic stdin path --
    unlike the CLI's --file, there's no --file equivalent here)."""
    if ruleset_id:
        return rulesets.get_ruleset(ruleset_id)
    resolved = core_config.resolve_ruleset(_SYNTHETIC_STDIN_PATH, REPO_ROOT, rulesets)
    if resolved is None:
        raise ValueError(
            "no ruleset resolves under the current config -- pass ruleset explicitly")
    return resolved


def _unsupported(ruleset, capability, verb):
    return {"ok": False, "status": "unsupported",
            "message": f"'{ruleset.RULESET_ID}' ruleset has no {capability} capability "
                       f"(capabilities: {sorted(ruleset.CAPABILITIES)}) -- nothing to {verb} here."}


def _flag_summary(flags):
    out = []
    for f in flags:
        d = f["detail"]
        label = f.get("label") or d.get("rule", "?")
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
def lint_text(text: str, context: str = "", ruleset: str = "") -> dict:
    """Check text against a ruleset's rules without writing it anywhere.
    Use this before a real Write/Edit to see what the live gate would do,
    and cut down on denied attempts -- it does NOT replace the gate; the
    actual write still goes through the hook regardless of this tool's
    result. `ruleset` picks which ruleset to check against (default:
    resolved from stopslop.config.json, or ste100 if there's no config
    file). `context` is passed through to the resolved ruleset -- for
    ste100: "procedure" (20-word limit, step-by-step instructions) or
    "description" (default, 25-word limit, whole documents).
    """
    active = _resolve(ruleset or None)
    result = active.lint_and_gate(text, context=context or None)
    blocking = active.blocking_semantic_flags(result["semantic_flags"])
    return {
        "ruleset": active.RULESET_ID,
        "would_pass_live_gate": len(blocking) == 0,
        "blocking_issues": _flag_summary(blocking),
        "mechanical_fixes_on_real_write": _flag_summary(result["mechanical_violations"]),
    }


@mcp.tool()
def check_word(word: str, ruleset: str = "") -> dict:
    """Look up a single word against a ruleset's dictionary and glossary,
    if it has one (see list_rulesets for which do). Returns whether it's
    approved, forbidden (with a replacement if the standard gives one), a
    registered project term, a modal needing resolution, or simply not
    covered by any of those. Cheaper than lint_text when all you need is
    one word's status, e.g. before choosing how to phrase a sentence.
    """
    active = _resolve(ruleset or None)
    if "word_lookup" not in active.CAPABILITIES:
        return _unsupported(active, "word_lookup", "look up a single word for")
    return active.check_word(word)


@mcp.tool()
def register_project_term(word: str, note: str = "", override_unapproved: str = "", ruleset: str = "") -> dict:
    """Add a word to a ruleset's glossary so the gate stops flagging it, if
    that ruleset has a glossary (see list_rulesets). For genuine domain
    vocabulary a closed-vocabulary ruleset was never going to cover (e.g.
    "repository", "API" for ste100). Registration is meant to be
    deliberate: confirm with the person you're working with before calling
    this, the same way the project's own workflow does it (ask, then
    register on approval), even though this tool itself doesn't enforce
    that step. Refuses a word the real dictionary already forbids unless
    override_unapproved gives an explicit reason -- that's overriding a
    real rule, not filling a coverage gap, and needs to be a deliberate,
    on-the-record choice.
    """
    active = _resolve(ruleset or None)
    if "glossary" not in active.CAPABILITIES:
        return _unsupported(active, "glossary", "register a term for")
    return active.register_term(word, note, override_unapproved or None)


@mcp.tool()
def unregister_project_term(word: str, ruleset: str = "") -> dict:
    """Remove a word from a ruleset's glossary, if it has one -- undoes a
    mistaken register_project_term call. The gate goes back to flagging
    the word normally.
    """
    active = _resolve(ruleset or None)
    if "glossary" not in active.CAPABILITIES:
        return _unsupported(active, "glossary", "unregister a term for")
    return active.unregister_term(word)


@mcp.tool()
def list_project_terms(ruleset: str = "") -> dict:
    """Every word currently registered in a ruleset's glossary, if it has
    one, with the note it was registered under and whether it overrides a
    real prohibition.
    """
    active = _resolve(ruleset or None)
    if "glossary" not in active.CAPABILITIES:
        return _unsupported(active, "glossary", "list terms for")
    return {"ruleset": active.RULESET_ID, "terms": active.list_terms()}


@mcp.tool()
def list_glossary_packs(ruleset: str = "") -> dict:
    """Every bulk vocabulary pack registered for a ruleset (name, source
    URL, license, real term count, and whether it's enabled for this
    project right now), if that ruleset supports packs at all. A pack
    starts disabled -- enabling one is a project-level choice, made with
    enable_glossary_packs, not automatic just because a pack exists in
    code.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "list_glossary_packs"):
        return _unsupported(active, "glossary-packs", "list vocabulary packs for")
    return {"ruleset": active.RULESET_ID, "packs": active.list_glossary_packs()}


@mcp.tool()
def enable_glossary_packs(pack_ids: list[str], ruleset: str = "") -> dict:
    """Set exactly this list of vocabulary packs as enabled for a ruleset
    -- disables every other known pack for that ruleset. Pass an empty
    list to disable all packs. Validated against the real pack registry
    first: an unknown pack id refuses instead of silently doing nothing.
    Takes effect on the next gate call immediately, no session restart.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "set_enabled_glossary_packs"):
        return _unsupported(active, "glossary-packs", "enable vocabulary packs for")
    try:
        active.set_enabled_glossary_packs(pack_ids)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}
    return {"ok": True, "status": "enabled", "message": f"enabled: {', '.join(pack_ids) or '(none)'}"}


@mcp.tool()
def list_rulesets() -> dict:
    """Every ruleset registered with this stopslop install: id, display
    name, and which capabilities it declares (glossary, word_lookup --
    absent means the other tools here will report "unsupported" for it).
    """
    return {
        "rulesets": [
            {"id": m.RULESET_ID, "name": m.RULESET_NAME,
             "capabilities": sorted(m.CAPABILITIES)}
            for m in rulesets.list_rulesets()
        ]
    }


@mcp.tool()
def get_status() -> dict:
    """Current state of the gate: per-ruleset stats (dictionary/glossary
    size where applicable), how many gate events have been logged and what
    kind, whether an integrity baseline exists, and whether the hook is
    even wired up in this clone yet.
    """
    return status_report.build_status_report()


if __name__ == "__main__":
    mcp.run(transport="stdio")
