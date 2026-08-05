#!/usr/bin/env python3
"""PreToolUse hook: gate Write/Edit/Bash file writes through whichever
ruleset stopslop.config.json (or the built-in defaults) resolves for the
target path. Denies the tool call outright if the resolved ruleset reports
any real blocking semantic_flags; auto-fixes and rewrites the tool call if
only mechanical violations remain; lets genuinely clean text through
unmodified.

Formerly hardcoded to ste100 directly -- generalized during the pluggable-
ruleset refactor into a ruleset-agnostic dispatcher: this file now knows
nothing about STE100's rules, vocabulary, or grammar. It resolves a path to
a ruleset via core.config.resolve_ruleset(), then calls that ruleset's
lint_and_gate/blocking_semantic_flags/apply_mechanical_fixes -- the same
four functions every registered ruleset's contract guarantees (see
rulesets/__init__.py).

Scope -- which extensions get linted, and by which ruleset -- is entirely
config-driven now. With no stopslop.config.json present, core.config's
DEFAULT_RULES reproduces the original STE100-on-.md/.txt/.rst,
excluding-.claude/ scope exactly.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bash_write_detect
import generate_coaching_memory
import rulesets
from core import config as core_config
from core import extract as core_extract
from core import flags as flags_mod
from core import history, paths

PROJECT_ROOT = paths.find_project_root(__file__)
HISTORY_LOG = history.history_log_path(PROJECT_ROOT)
RETRY_CAP = 3  # configurable: consecutive denials on the same file before
                # the gate tells the model to stop retrying and ask the user
                # directly, per the design doc's own section 10.1 idea

# Explicit, reviewed allowlist of non-linted extensions this project's own
# tooling legitimately writes -- deliberately NOT "anything with no matching
# ruleset is fine," which is what let the .dat bypass in
# docs/incidents/2026-08-01-ste100-dictionary-extraction-gate-bypass.md go
# unnoticed. A new non-linted extension needs adding here on purpose; until
# then it's still allowed through (linting genuinely non-prose files would
# break normal development) but it's LOGGED, not silent -- see
# is_unscoped_write below. ".py" isn't here: it's a real codewatch default
# now (see core.config.DEFAULT_RULES), so resolve_ruleset() already handles
# it before this allowlist is ever consulted.
ALLOWED_UNLINTED_EXTENSIONS = (".json",)


def _log_and_regenerate(event, ruleset_id):
    """Log one real gate-decision event (deny/auto_fix/clean) to the shared
    history, then regenerate that ruleset's coaching memory inline -- not
    via a separate PostToolUse hook. PostToolUse only fires once a tool
    call actually succeeds; it never fires after a PreToolUse denial, which
    means it would silently miss every deny event -- exactly the signal
    this memory loop most needs. Broad except on the regen call: memory
    regeneration must never break the gate itself, same principle as
    history.log_event's own OSError handling. generate_coaching_memory
    must never print, since this whole process's stdout is Claude Code's
    hook-response channel."""
    history.log_event(event, ruleset_id, HISTORY_LOG)
    try:
        generate_coaching_memory.regenerate(ruleset_id)
    except Exception as ignored:
        pass


def _log_config_write(file_path):
    """True (and logged) when this write targets stopslop.config.json.

    The config file is the gate's own control surface, writable through
    the unlinted-json allowlist -- which meant an agent denied by the
    gate could raise its own threshold, or disable the check that fired,
    and retry, with no record anywhere. Not blocked: the config is the
    human's file, local-first by design, and the dashboard edits it
    constantly. No longer silent either -- the event lands in history,
    so Watch shows the gate's own rules being changed mid-session."""
    if os.path.abspath(file_path) != core_config.config_path(PROJECT_ROOT):
        return False
    history.log_event({"file": file_path, "action": "config_write",
                        "kinds": []}, "_core", HISTORY_LOG)
    return True


def _log_unscoped(event):
    """unscoped_write events aren't about any particular ruleset's rules --
    they're a governance/audit signal about a write that matched no active
    ruleset scope at all -- so there's nothing meaningful to regenerate a
    coaching primer from. Tagged "_core", the same namespace
    integrity_check.py uses for gate-mechanism (not ruleset) trust anchors."""
    history.log_event(event, "_core", HISTORY_LOG)


def count_consecutive_denials(file_path):
    return history.count_consecutive_denials(file_path, HISTORY_LOG)


def recent_deny_nearby():
    return history.recent_deny_nearby(HISTORY_LOG)


def _read_current(file_path):
    """The file as it exists NOW, or "" -- nonexistent and unreadable are
    both 'no before-state', and the gate must never crash on either."""
    try:
        with open(file_path) as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def _resulting_text(tool_name, tool_input, before_text):
    """The file as it will exist AFTER this write, or None when it cannot
    be reconstructed (Bash; an Edit whose old_string is not found -- the
    tool itself will fail on that anyway).

    The gate judges the RESULT, not the chunk. Delta-linting had two
    exploitable holes: a file could accrete unbounded slop threshold-1
    flags per Edit, forever under the bar; and the embedded-prose pass
    silently never ran for Edit at all, because a new_string fragment
    almost never parses as Python, so the extractor saw nothing."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    old = tool_input.get("old_string", "")
    new = tool_input.get("new_string", "")
    if not old or old not in before_text:
        return None
    count = -1 if tool_input.get("replace_all") else 1
    return before_text.replace(old, new, count)


def resolve_target_path(target):
    """Bash targets are often relative. Absolute paths are used as-is; a
    relative path is assumed relative to PROJECT_ROOT -- a known, documented
    limitation (doesn't account for a `cd` earlier in the same command or
    session), consistent with this whole module's bias toward under- rather
    than over-triggering."""
    if target.startswith("/"):
        return target
    return os.path.normpath(os.path.join(PROJECT_ROOT, target))


def is_unscoped_write(file_path):
    """True for a write under the project (excluding .claude/) landing on
    an extension that neither resolves to a ruleset nor is on the explicit
    allowlist above -- not blocked (see ALLOWED_UNLINTED_EXTENSIONS comment)
    but worth logging, since silence here is exactly what let the .dat
    bypass go unnoticed. Only ever called once resolve_ruleset() has
    already returned None for this path, so this only needs to distinguish
    "expected non-prose tooling file" from "everything else.\""""
    if not file_path.startswith(PROJECT_ROOT):
        return False
    if file_path.startswith(os.path.join(PROJECT_ROOT, ".claude") + os.sep):
        return False  # tooling/config is meta, not shipped product text -- never "unscoped"
    linted_exts = tuple(core_config.known_extensions(PROJECT_ROOT))
    return not file_path.endswith(linted_exts + ALLOWED_UNLINTED_EXTENSIONS)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # malformed input -- allow silently, don't break the harness

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        extensions = tuple(core_config.known_extensions(PROJECT_ROOT)) or bash_write_detect.DEFAULT_EXTENSIONS
        detected = bash_write_detect.extract_bash_write(command, extensions)
        if not detected:
            return  # no confident write pattern detected -- allow, don't guess
        target, text = detected
        file_path = resolve_target_path(target)
        ruleset = core_config.resolve_ruleset(file_path, PROJECT_ROOT, rulesets)
        if ruleset is None:
            if _log_config_write(file_path):
                return
            if text.strip() and is_unscoped_write(file_path):
                _log_unscoped({"file": file_path, "action": "unscoped_write", "kinds": [],
                                "word_count": len(text.split()), "nearby_deny": recent_deny_nearby()})
            return
        if not text.strip():
            return
        can_autofix = False  # no auto-fix/rewrite for Bash -- see module docstring
    elif tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        text = tool_input.get("content", "") if tool_name == "Write" else tool_input.get("new_string", "")
        ruleset = core_config.resolve_ruleset(file_path, PROJECT_ROOT, rulesets)
        if ruleset is None:
            if _log_config_write(file_path):
                return
            if text.strip() and is_unscoped_write(file_path):
                _log_unscoped({"file": file_path, "action": "unscoped_write", "kinds": [],
                                "word_count": len(text.split()), "nearby_deny": recent_deny_nearby()})
            return
        if not text.strip():
            return
        can_autofix = True
    else:
        return

    # file_path is passed, not just resolved-and-discarded: vocabulary
    # packs attach to the routing rule that matched this path, so the
    # effective glossary genuinely differs between two files the same
    # ruleset gates. See core.config.packs_for_path.
    # Mechanical fixes act on the written CHUNK (the delta is what the
    # hook can rewrite via updatedInput), so this lint stays delta-based.
    result = ruleset.lint_and_gate(text, file_path=file_path)

    rule = core_config.matching_rule(file_path, PROJECT_ROOT)
    embedded = core_extract.rule_embedded_ruleset(rule, rulesets)
    extension = os.path.splitext(file_path)[1]

    # Semantic judgment runs on the RESULTING FILE where it can be
    # reconstructed (see _resulting_text for the two cheats delta-linting
    # allowed), with RATCHET semantics: when the file already exists, a
    # write is denied only if the result is deniable AND the write made
    # it worse -- measured in flag OCCURRENCES, so repeats count. A file
    # with legacy flags stays editable; it just cannot gain more. Bash
    # stays delta-judged: a heredoc target is not reconstructable here.
    before_text = _read_current(file_path) if can_autofix else ""
    after_text = (_resulting_text(tool_name, tool_input, before_text)
                  if can_autofix else None)
    judged = after_text if after_text is not None else text
    semantic = (result["semantic_flags"] if judged == text
                else ruleset.lint_and_gate(judged, file_path=file_path)["semantic_flags"])
    # A code rule can also name a prose ruleset for its embedded string
    # literals and docstrings -- the crack between "codewatch reads code"
    # and "prose rulesets read .md" is where this project's own UI copy
    # lived unlinted. Either gate denying denies. See core/extract.py.
    embedded_pool = (core_extract.embedded_prose_pool(
                         judged, extension, embedded, file_path=file_path)
                     if embedded is not None else [])

    # See <ruleset>.blocking_semantic_flags for what's excluded and why --
    # every caller (this hook, stopslop.py's `lint` command, the MCP
    # server) calls the resolved ruleset's own blocking_semantic_flags
    # rather than each keeping its own copy of this filter.
    flags = list(ruleset.blocking_semantic_flags(semantic))
    if embedded is not None:
        for f in embedded.blocking_semantic_flags(embedded_pool):
            f = dict(f)
            f["embedded"] = True
            flags.append(f)

    before_weight = after_weight = None
    if flags and after_text is not None and before_text.strip():
        before_semantic = ruleset.lint_and_gate(
            before_text, file_path=file_path)["semantic_flags"]
        before_pool = (core_extract.embedded_prose_pool(
                           before_text, extension, embedded, file_path=file_path)
                       if embedded is not None else [])
        before_weight = (flags_mod.flag_weight(before_semantic)
                         + flags_mod.flag_weight(before_pool))
        after_weight = (flags_mod.flag_weight(semantic)
                        + flags_mod.flag_weight(embedded_pool))
        if after_weight <= before_weight:
            flags = []      # deniable, but no worse than it already was

    if flags:
        summary_lines = []
        for f in flags[:8]:
            where = ""
            if f.get("embedded"):
                where = (f" (embedded prose, line {f['embedded_line']})"
                         if "embedded_line" in f else " (embedded prose)")
            summary_lines.append(f"- [{f['kind']}] {flags_mod.display_label(f)}{where}")
        more = f"\n...and {len(flags) - 8} more" if len(flags) > 8 else ""
        attempt_number = count_consecutive_denials(file_path) + 1
        gate_name = ruleset.RULESET_NAME
        if any(f.get("embedded") for f in flags):
            gate_name += f" + {embedded.RULESET_NAME} on embedded prose"
        reason = (
            f"{gate_name} gate: {file_path} has {len(flags)} flag(s) "
            f"requiring human/model resolution before this can be written.\n"
            + "\n".join(summary_lines) + more
        )
        if before_weight is not None:
            reason += (
                f"\n\nRatchet: the file carries {before_weight} "
                f"flag-occurrence(s) before this write and {after_weight} "
                f"after it. A write that does not add flags passes."
            )
        # Say what can be DONE, not only what is wrong. A deny used to list
        # its flags and stop there, so an agent blocked on a legitimate
        # domain word never learned that add_term exists. Derived from the
        # ruleset's own declarations (core.flags.remedies_for), so a new
        # check or list is covered without anyone updating a table here.
        remedy_lines = []
        host_kinds = {f["kind"] for f in flags if not f.get("embedded")}
        for kind in dict.fromkeys(f["kind"] for f in flags[:8]):
            # A remedy comes from the ruleset that owns the check -- the
            # embedded ruleset's kinds mean nothing to the host's lists.
            owner = ruleset if kind in host_kinds else embedded
            for line in flags_mod.remedies_for(owner, kind):
                remedy_lines.append(f"- {kind}: {line}")
        if remedy_lines:
            reason += ("\n\nIf a flag is a false positive here, these resolve it "
                       "(MCP tools, or the same names in the dashboard):\n"
                       + "\n".join(remedy_lines[:10]))
        if attempt_number >= RETRY_CAP:
            reason += (
                f"\n\nThis is denial #{attempt_number} in a row on this file. Stop "
                f"retrying -- ask the user directly how to resolve the remaining "
                f"flag(s) instead of attempting another rewrite."
            )
        _log_and_regenerate({"file": file_path, "action": "deny",
                              "kinds": [f["kind"] for f in flags]}, ruleset.RULESET_ID)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
        return

    if result["mechanical_violations"] and not can_autofix:
        # Bash: no rewrite attempted (see module docstring on bash_write_detect
        # -- reconstructing a shell command string safely is real additional
        # risk not taken on here). Deny and point at Write/Edit instead,
        # rather than silently letting uncorrected text through a path that
        # happens to have weaker guarantees than the proven one.
        kinds = [f["kind"] for f in result["mechanical_violations"]]
        _log_and_regenerate({"file": file_path, "action": "deny", "kinds": kinds}, ruleset.RULESET_ID)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{ruleset.RULESET_NAME} gate: this Bash command would write "
                    f"{len(result['mechanical_violations'])} mechanically-fixable violation(s) "
                    f"({', '.join(sorted(set(kinds)))}) to {file_path}. "
                    f"Auto-fix isn't supported for Bash writes -- use the Write or Edit tool instead, "
                    f"where these get corrected automatically."
                ),
            }
        }))
        return

    if result["mechanical_violations"]:
        fixed_text = ruleset.apply_mechanical_fixes(text, file_path=file_path)
        updated_input = dict(tool_input)
        if tool_name == "Write":
            updated_input["content"] = fixed_text
        else:
            updated_input["new_string"] = fixed_text
        kinds = [f["kind"] for f in result["mechanical_violations"]]
        _log_and_regenerate({"file": file_path, "action": "auto_fix", "kinds": kinds}, ruleset.RULESET_ID)
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": (
                    f"{ruleset.RULESET_NAME} gate: auto-fixed {len(result['mechanical_violations'])} "
                    f"mechanical violation(s) before write ({', '.join(sorted(set(kinds)))})."
                ),
                "updatedInput": updated_input,
            }
        }))
        return

    # Genuinely clean: no hook output (silent pass, unmodified), but DO log
    # a "clean" event with no kinds -- harmless for the coaching-memory
    # aggregator (it only sums "kinds", which this has none of) and
    # necessary for count_consecutive_denials to have something to break
    # the streak on.
    _log_and_regenerate({"file": file_path, "action": "clean", "kinds": []}, ruleset.RULESET_ID)


if __name__ == "__main__":
    main()
