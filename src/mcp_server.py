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
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashboard_launch
import rulesets
import status_report
from core import config as core_config
from core import flags as core_flags
from core import paths
from core import scan as core_scan
from core import terms as core_terms

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
_SYNTHETIC_STDIN_PATH = os.path.join(REPO_ROOT, core_config.SYNTHETIC_TEXT_NAME)


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
        entry = {"kind": f["kind"], "rule": d.get("rule"), "text": core_flags.display_label(f)}
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
def list_term_lists(ruleset: str = "", file_path: str = "") -> dict:
    """Every named word list a ruleset checks against, with its POLARITY
    ("allow" = matching terms are permitted, "deny" = matching terms are
    flagged) and where each term came from: shipped built-ins, opt-in
    vocabulary packs, or this project's own registrations.

    Pass file_path when you care about a specific file: vocabulary packs
    are enabled per path glob, not per ruleset, so two files handled by the
    same ruleset can have genuinely different effective vocabularies. Also
    reports any pack terms the ruleset refused because its own standard
    forbids them.
    """
    active = _resolve(ruleset or None)
    if "terms" not in active.CAPABILITIES:
        return _unsupported(active, "terms", "list term lists for")
    return {"ruleset": active.RULESET_ID,
            "lists": active.list_term_lists(file_path or None)}


@mcp.tool()
def add_term(list_id: str, term: str, note: str = "", force: str = "",
             ruleset: str = "") -> dict:
    """Add one term to a ruleset's term list -- what the gate should stop
    flagging (an "allow" list, e.g. ste100's project vocabulary) or start
    flagging (a "deny" list, e.g. slopwatch's marketing cliches). Call
    list_term_lists first to see the ids and their polarity.

    Registration is meant to be deliberate: confirm with the person you're
    working with before calling this, the same way the project's own
    workflow does (ask, then register on approval), even though this tool
    doesn't enforce that step.

    `force` is a REASON string, not a flag. A list backed by a real
    external standard (ste100's) refuses a word that standard explicitly
    forbids unless you give one -- that is overriding a real rule, not
    filling a coverage gap, and belongs on the record.
    """
    active = _resolve(ruleset or None)
    if "terms" not in active.CAPABILITIES:
        return _unsupported(active, "terms", "add a term for")
    try:
        return active.add_term(list_id, term, note, force=force or False)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}


@mcp.tool()
def remove_term(list_id: str, term: str, ruleset: str = "") -> dict:
    """Remove one term from a ruleset's term list -- undoes a mistaken
    add_term call. A no-op, not an error, if the term was never registered.
    """
    active = _resolve(ruleset or None)
    if "terms" not in active.CAPABILITIES:
        return _unsupported(active, "terms", "remove a term for")
    try:
        return active.remove_term(list_id, term)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}


@mcp.tool()
def list_path_packs() -> dict:
    """Every available vocabulary pack, and which routing rule/list each is
    currently bound to. Read-only -- see set_path_packs to bind one.

    A pack is bulk, pre-curated vocabulary from a real external source
    (MDN, NIST, the Microsoft style guide). It is inert content: it does
    NOT declare which ruleset or list reads it -- that's why "available"
    lists packs with no mention of a consumer, and the binding lives
    entirely in "enabled_by_rule".
    """
    from core import glossary_packs
    return {"ok": True, "status": "listed",
            "available": glossary_packs.list_packs(),
            "enabled_by_rule": [{"glob": g, "ruleset": r, "packs_by_list": by_list}
                                 for g, r, by_list in core_config.rule_packs(REPO_ROOT)]}


@mcp.tool()
def set_path_packs(glob: str, list_id: str, pack_ids: list[str] = None) -> dict:
    """Point vocabulary packs at a term list on a path glob. Call
    list_path_packs first to see the available pack ids and the current
    bindings.

    Both halves of the binding -- which rule, which list -- are project
    decisions made here, because the same pack can reasonably feed
    different lists in different repos, or be read at the opposite
    polarity: an allow list by one ruleset, a deny list by another.

    A pack attaches to a routing rule rather than to a ruleset because a
    pack is domain content and domain is a property of the text: NIST
    security vocabulary belongs to docs/security/, not to every file
    ste100 happens to gate.

    Sets exactly the pack_ids given (an empty list detaches every pack
    from that list). Unknown pack ids and unknown globs both refuse
    rather than silently doing nothing.
    """
    from core import glossary_packs
    if not list_id:
        return {"ok": False, "status": "refused",
                 "message": "list_id is required: a pack feeds a named term list, "
                             "and the pack itself does not say which one. Call "
                             "list_term_lists to see the ids."}
    # The same kind guard the dashboard applies. Without it this entry point
    # walks straight past a rule enforced at three other layers: a pack of
    # plain words could be bound to a list of regex patterns from here.
    spec = None
    for module in rulesets.list_rulesets():
        if list_id in getattr(module, "TERM_LISTS", {}):
            spec = module.TERM_LISTS[list_id]
            break
    admissible = None
    if spec is not None:
        admissible = lambda pid: core_terms.pack_kind_admissible(
            spec, glossary_packs.AVAILABLE_PACKS.get(pid, {}))
    try:
        core_config.set_rule_packs(REPO_ROOT, glob, list_id, pack_ids or [],
                                    known_packs=glossary_packs.AVAILABLE_PACKS,
                                    admissible=admissible)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}
    return {"ok": True, "status": "saved",
            "message": f"{glob} -> {list_id}: {', '.join(pack_ids or []) or '(none)'}"}


@mcp.tool()
def list_checks(ruleset: str = "") -> dict:
    """Every individual check a ruleset can run (id, what it catches, what
    to do instead, whether it's currently enabled), if that ruleset supports
    per-check
    toggles at all (see list_rulesets). Every check runs by default --
    turning one off is a project-level choice, made with set_checks.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "list_checks"):
        return _unsupported(active, "checks", "list individual checks for")
    return {"ruleset": active.RULESET_ID, "checks": active.list_checks()}


@mcp.tool()
def set_checks(states: dict[str, bool], ruleset: str = "") -> dict:
    """Turn individual checks on or off, leaving every check you do not
    name alone: {"swallowed_exception": false}.

    MERGE semantics, deliberately. This tool replaced an enable_checks that
    set exactly the list it was given and disabled everything else -- so
    "turn off this one noisy check" was expressed as "turn the other 19
    back on",
    and getting that list slightly wrong silently disabled real checks. A
    caller here almost never holds the full picture; the CLI's
    `stopslop.py checks --enable a b c` does, and keeps replace semantics
    for that reason. See core.config.merge_disabled_checks.

    An unknown check id refuses rather than silently doing nothing. Takes
    effect on the next gate call, with no session restart.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "set_checks_enabled"):
        return _unsupported(active, "checks", "toggle individual checks for")
    try:
        active.set_checks_enabled(states)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}
    on = sorted(k for k, v in states.items() if v)
    off = sorted(k for k, v in states.items() if not v)
    return {"ok": True, "status": "saved",
            "message": f"on: {', '.join(on) or '(none)'} · off: {', '.join(off) or '(none)'}",
            "checks": active.list_checks()}


@mcp.tool()
def list_check_config(ruleset: str = "") -> dict:
    """Every check's own {threshold, action}: how many times it has to
    fire in a document before it counts as triggered, and whether a
    triggered check denies the write on its own (block) or is only shown
    (warn) -- if that ruleset supports per-check config at all (see
    list_rulesets). Replaces one shared ruleset-wide flag-count number
    with real, per-check settings.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "list_check_config"):
        return _unsupported(active, "check_config", "list per-check threshold/action for")
    return {"ruleset": active.RULESET_ID, "check_config": active.list_check_config()}


@mcp.tool()
def set_check_config(check_id: str, threshold: int = 0, action: str = "",
                      ruleset: str = "") -> dict:
    """Set one check's threshold and/or action, leaving whatever you don't
    pass alone. threshold: how many times this check has to fire before
    it counts as triggered. action: "block" (denies the write once
    triggered) or "warn" (shown, never denies by itself). Leave a
    parameter at its default (threshold=0, action="") to not change it --
    0 is never a valid threshold, so it doubles as "not set" here.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "set_check_config"):
        return _unsupported(active, "check_config", "set per-check threshold/action for")
    try:
        active.set_check_config(check_id, threshold=threshold or None, action=action or None)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}
    return {"ok": True, "status": "saved",
            "message": f"{check_id}: " + ", ".join(
                p for p in (f"threshold={threshold}" if threshold else "",
                            f"action={action}" if action else "") if p),
            "check_config": active.list_check_config()}


@mcp.tool()
def list_options(ruleset: str = "") -> dict:
    """Every tunable option a ruleset exposes (e.g. slopwatch's block-flag-
    count threshold), its current effective value, and its built-in
    default, if that ruleset has any tunable options at all.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "list_options"):
        return _unsupported(active, "options", "list tunable options for")
    return {"ruleset": active.RULESET_ID, "options": active.list_options()}


@mcp.tool()
def set_ruleset_options(options: dict, ruleset: str = "") -> dict:
    """Set one or more tunable options for a ruleset. An option this call
    doesn't mention keeps its current value -- this merges, it does not
    replace the whole set. Validated against the known option names and
    each one's real type first: an unknown option or a wrong type refuses
    instead of silently doing nothing.
    """
    active = _resolve(ruleset or None)
    if not hasattr(active, "set_options"):
        return _unsupported(active, "options", "set tunable options for")
    try:
        active.set_options(options)
    except Exception as exc:
        return {"ok": False, "status": "refused", "message": str(exc)}
    return {"ok": True, "status": "set",
            "message": f"set: {', '.join(f'{k}={v}' for k, v in options.items()) or '(none)'}"}


@mcp.tool()
def scan_codebase(paths: list[str] = None, ruleset: str = "", glob: str = "*") -> dict:
    """Bulk-check an existing tree of files against a ruleset, with no live
    write -- the missing piece for adopting stopslop onto a codebase that
    already exists, not just files edited going forward. `paths` (relative
    to the project root, or absolute) defaults to the whole project if
    empty. Leave `ruleset` empty to resolve each file's ruleset from
    stopslop.config.json, the same as a live write -- a file out of scope
    under the current routing is skipped, not flagged. Pass a ruleset id to
    force every matched file through that one ruleset regardless of
    routing (e.g. testing slopwatch against an existing docs/ tree before
    ever adding a routing rule for it); `glob` then narrows which
    filenames are included (default: every regular file).
    """
    target_paths = [p if os.path.isabs(p) else os.path.join(REPO_ROOT, p) for p in (paths or [])] or [REPO_ROOT]
    for p in target_paths:
        if not os.path.exists(p):
            return {"ok": False, "status": "not_found", "message": f"{p!r} does not exist."}
    if ruleset:
        try:
            rulesets.get_ruleset(ruleset)
        except rulesets.UnknownRulesetError as exc:
            return {"ok": False, "status": "unknown_ruleset", "message": str(exc)}

    report = core_scan.scan_tree(target_paths, REPO_ROOT, rulesets,
                                  ruleset_id=ruleset or None, glob_pattern=glob)
    fail = [r for r in report["results"] if r["would_block"]]
    return {
        "ok": True,
        "scanned": report["scanned"],
        "skipped_out_of_scope": report["skipped_out_of_scope"],
        "skipped_unreadable": report["skipped_unreadable"],
        "would_fail_count": len(fail),
        "results": [
            {
                "path": os.path.relpath(r["path"], REPO_ROOT),
                "ruleset": r["ruleset"],
                "would_block": r["would_block"],
                "blocking_issues": _flag_summary(r["blocking_flags"]),
                "mechanical_fixes": _flag_summary(r["mechanical_flags"]),
            }
            for r in report["results"] if r["blocking_flags"] or r["mechanical_flags"]
        ],
    }


@mcp.tool()
def explain(file_path: str) -> dict:
    """Everything that will happen to one file, in one call.

    The rest of this surface is organised by CONFIG KEY -- list_checks,
    list_options, list_term_lists, list_path_packs -- which is the shape of
    the storage, not the shape of the question. An agent about to write a
    file wants one answer: what gates this, what would block me, and what
    can I do about it. Getting that from the other tools meant knowing to
    call list_rulesets, guessing which ruleset applies, then four more
    calls; and only one of those tools even took a file path.

    Returns the matched routing rule, the ruleset, its deny policy in
    words, the checks that actually run on this path (with the ones that
    deny on their own marked), the vocabulary reaching it, and the tools
    that resolve each kind of flag.
    """
    full = file_path if os.path.isabs(file_path) else os.path.join(REPO_ROOT, file_path)
    rule = core_config.matching_rule(full, REPO_ROOT)
    if rule is None:
        return {"ok": True, "status": "unrouted", "file": file_path,
                "message": "No routing rule matches this path, so the gate "
                            "never runs on it. Add a rule to "
                            "stopslop.config.json to bring it into scope."}
    if rule["ruleset"] is None:
        return {"ok": True, "status": "out_of_scope", "file": file_path,
                "rule": rule["glob"],
                "message": f"The rule {rule['glob']!r} puts this path out of "
                            f"scope deliberately. Nothing is checked here."}

    module = rulesets.get_ruleset(rule["ruleset"])
    options = core_flags.display_options(module)
    policy = getattr(module, "DENY_POLICY", {})
    try:
        policy_text = policy.get("text", "").format(**options)
    except KeyError:
        policy_text = policy.get("text", "")

    disabled = set(core_config.disabled_checks_for_path(
        REPO_ROOT, module.RULESET_ID, full))
    blocks_alone_at = policy.get("blocks_alone_at", {})
    checks = {}
    if "checks" in module.CAPABILITIES:
        for check_id, meta in sorted(module.list_checks().items()):
            if check_id in disabled:
                continue
            checks[check_id] = {"catches": meta["catches"],
                                 "instead": meta["instead"],
                                 # Occurrences of THIS check alone that deny a
                                 # write, or null if it only ever contributes
                                 # to the ruleset's shared flag-count pool.
                                 # A bare "denies_alone: true/false" would lie
                                 # for any check declared at N > 1.
                                 "denies_alone_at": blocks_alone_at.get(check_id),
                                 "remedies": core_flags.remedies_for(module, check_id)}
    return {
        "ok": True, "status": "gated", "file": file_path,
        "rule": rule["glob"], "ruleset": module.RULESET_ID,
        "denies_when": policy_text,
        "checks_that_run": checks,
        "checks_disabled_here": sorted(disabled),
        "options": options,
        "vocabulary": (module.list_term_lists(file_path=full)
                       if "terms" in module.CAPABILITIES else {}),
    }


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
    # Daemon thread: ensure_running does its own locking/probing and can
    # block up to _SPAWN_TIMEOUT_SECONDS on a slow boot, but nothing here
    # should ever delay the stdio handshake below it -- see
    # dashboard_launch.py's module docstring for why this is safe to fire
    # from every session without piling up duplicate Streamlit processes.
    threading.Thread(target=dashboard_launch.ensure_running, args=(REPO_ROOT,),
                      daemon=True).start()
    mcp.run(transport="stdio")
