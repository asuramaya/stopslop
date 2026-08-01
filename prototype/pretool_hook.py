#!/usr/bin/env python3
"""PreToolUse hook: gate Write/Edit calls on text files through the STE100
linter prototype. Denies the tool call outright if lint_and_gate reports any
real semantic_flags; auto-fixes and rewrites the tool call if only mechanical
violations remain; lets genuinely clean text through unmodified.

Scope: only .md/.txt/.rst files under the project (excluding .claude/) are
linted -- code files, files outside the project, and tooling/config
pass through untouched.
"""
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ste100_lint as lint
import bash_write_detect
import generate_coaching_memory

LINTED_EXTENSIONS = (".md", ".txt", ".rst")
# Explicit, reviewed allowlist of non-linted extensions this project's own
# tooling legitimately writes -- deliberately NOT "anything that isn't
# .md/.txt/.rst is fine," which is what let the .dat bypass in
# docs/incidents/2026-08-01-ste100-dictionary-extraction-gate-bypass.md go
# unnoticed. A new non-linted extension needs adding here on purpose; until
# then it's still allowed through (linting genuinely non-prose files would
# break normal development) but it's LOGGED, not silent -- see
# is_unscoped_write below.
ALLOWED_UNLINTED_EXTENSIONS = (".py", ".json")
PROJECT_ROOT = "/home/asuramaya/code/stopslop/"
HISTORY_LOG = os.path.join(PROJECT_ROOT, ".claude", "ste100-history.log")
RETRY_CAP = 3  # configurable: consecutive denials on the same file before
                # the gate tells the model to stop retrying and ask the user
                # directly, per the design doc's own section 10.1 idea


# A near-simultaneous duplicate log entry was observed once earlier this
# session and initially attributed to Claude Code firing PreToolUse twice
# per tool call. Investigated properly (task #6): every timestamped event
# since has been exactly one per real tool call, with multi-second gaps
# between genuine retries -- no true near-simultaneous duplicate has
# recurred. The original observation is much better explained by a manual
# pipe-test run with identical content immediately before the live call
# that "confirmed" it: two separate invocations logging identical data,
# not one call firing twice. Correction noted in project memory. This
# collapsing logic is kept anyway as cheap, harmless defense in case a
# real double-fire does occur under some condition not yet seen.
DOUBLE_FIRE_WINDOW_SECONDS = 2.0


def log_event(event):
    try:
        event = dict(event, ts=time.time())
        os.makedirs(os.path.dirname(HISTORY_LOG), exist_ok=True)
        with open(HISTORY_LOG, "a") as f:
            f.write(json.dumps(event) + "\n")
    except OSError:
        pass  # logging must never break the gate itself

    # Regenerate the coaching memory right here, inline, after every event --
    # not in a separate PostToolUse hook. PostToolUse only fires once a tool
    # call actually succeeds; it never fires after a PreToolUse denial, which
    # means it would silently miss every deny event -- exactly the signal
    # this memory loop most needs. Broad except: memory regeneration must
    # never break the gate itself, same principle as the log write above.
    # regenerate() is silent by design (see generate_coaching_memory.py) --
    # it must never print, since this whole process's stdout is Claude
    # Code's hook-response channel.
    try:
        generate_coaching_memory.regenerate()
    except Exception:
        pass


def dedupe_double_fire(events):
    """Collapse entries that are the SAME logical event fired twice (same
    file+action, within DOUBLE_FIRE_WINDOW_SECONDS of each other) -- but,
    unlike naive content-equality dedup, does NOT collapse genuinely
    separate repeat events (e.g. three real consecutive denials minutes
    apart) just because their file+action happen to match. Older log
    entries written before the "ts" field existed sort first (ts=0) and
    never merge with anything, which is safe -- undercounts by at most one
    pre-timestamp entry, never overcounts."""
    out = []
    prev = None
    for e in events:
        if (prev is not None
                and e.get("file") == prev.get("file")
                and e.get("action") == prev.get("action")
                and (e.get("ts", 0) - prev.get("ts", 0)) < DOUBLE_FIRE_WINDOW_SECONDS):
            prev = e
            continue
        out.append(e)
        prev = e
    return out


def count_consecutive_denials(file_path):
    """How many times in a row has this exact file been denied, with no
    successful write in between? Reused history log, no new state file."""
    if not os.path.exists(HISTORY_LOG):
        return 0
    try:
        with open(HISTORY_LOG) as f:
            lines = [json.loads(l) for l in f if l.strip()]
    except (OSError, json.JSONDecodeError):
        return 0
    deduped = dedupe_double_fire(lines)
    count = 0
    for e in reversed(deduped):
        if e.get("file") != file_path:
            continue  # other files don't affect this file's streak
        if e.get("action") == "deny":
            count += 1
        else:
            break  # a successful write for this file resets the streak
    return count


def resolve_target_path(target):
    """Bash targets are often relative. Absolute paths are used as-is; a
    relative path is assumed relative to PROJECT_ROOT -- a known, documented
    limitation (doesn't account for a `cd` earlier in the same command or
    session), consistent with this whole module's bias toward under- rather
    than over-triggering."""
    if target.startswith("/"):
        return target
    return os.path.normpath(os.path.join(PROJECT_ROOT, target))


def in_scope(file_path):
    if not file_path.startswith(PROJECT_ROOT):
        return False  # this session touches files outside the project (e.g.
                        # memory notes) -- the gate is scoped to stopslop's
                        # own text, not everything touched anywhere on disk
    if file_path.startswith(PROJECT_ROOT + ".claude/"):
        return False  # tooling/config is meta-documentation about the rules,
                        # not shipped product text -- not in scope
    return file_path.endswith(LINTED_EXTENSIONS)


def is_unscoped_write(file_path):
    """True for a write under the project (excluding .claude/) landing on an
    extension that's neither linted nor on the explicit allowlist above --
    not blocked (see ALLOWED_UNLINTED_EXTENSIONS comment) but worth logging,
    since silence here is exactly what let the .dat bypass go unnoticed."""
    if not file_path.startswith(PROJECT_ROOT):
        return False
    if file_path.startswith(PROJECT_ROOT + ".claude/"):
        return False
    return not file_path.endswith(LINTED_EXTENSIONS + ALLOWED_UNLINTED_EXTENSIONS)


def recent_deny_nearby(window_seconds=300):
    """Cheap, non-conclusive signal attached to an unscoped_write log entry:
    was there any deny event, on any file, in roughly the last few minutes?
    Deliberately NOT a verdict that this IS evasion -- content-based intent
    detection was tried elsewhere in this project (the noun-modifier -ing
    exemption heuristic) and reverted because it silently exempted genuine
    misuse too. This just puts a timestamp-proximity fact on the record for
    a human to judge, not a conclusion the gate draws on its own."""
    if not os.path.exists(HISTORY_LOG):
        return False
    try:
        with open(HISTORY_LOG) as f:
            lines = [json.loads(l) for l in f if l.strip()]
    except (OSError, json.JSONDecodeError):
        return False
    now = time.time()
    return any(e.get("action") == "deny" and (now - e.get("ts", 0)) < window_seconds
               for e in lines[-20:])


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return  # malformed input -- allow silently, don't break the harness

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        detected = bash_write_detect.extract_bash_write(command)
        if not detected:
            return  # no confident write pattern detected -- allow, don't guess
        target, text = detected
        file_path = resolve_target_path(target)
        if not in_scope(file_path):
            if text.strip() and is_unscoped_write(file_path):
                log_event({"file": file_path, "action": "unscoped_write", "kinds": [],
                           "word_count": len(text.split()), "nearby_deny": recent_deny_nearby()})
            return
        if not text.strip():
            return
        can_autofix = False  # no auto-fix/rewrite for Bash -- see module docstring
    elif tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        text = tool_input.get("content", "") if tool_name == "Write" else tool_input.get("new_string", "")
        if not in_scope(file_path):
            if text.strip() and is_unscoped_write(file_path):
                log_event({"file": file_path, "action": "unscoped_write", "kinds": [],
                           "word_count": len(text.split()), "nearby_deny": recent_deny_nearby()})
            return
        if not text.strip():
            return
        can_autofix = True
    else:
        return

    result = lint.lint_and_gate(text, context="description")

    # See ste100_lint.blocking_semantic_flags for what's excluded and why --
    # this is the single source of truth for what counts as blocking,
    # shared with stopslop.py's `lint` command so the two can't diverge.
    flags = lint.blocking_semantic_flags(result["semantic_flags"])

    if flags:
        summary_lines = []
        for f in flags[:8]:
            d = f["detail"]
            label = d.get("word") or d.get("phrase") or d.get("modal") or d.get("rule", "?")
            summary_lines.append(f"- [{f['kind']}] {label}")
        more = f"\n...and {len(flags) - 8} more" if len(flags) > 8 else ""
        attempt_number = count_consecutive_denials(file_path) + 1
        reason = (
            f"STE100 gate: {file_path} has {len(flags)} semantic flag(s) requiring "
            f"human/model resolution before this can be written.\n"
            + "\n".join(summary_lines) + more
        )
        if attempt_number >= RETRY_CAP:
            reason += (
                f"\n\nThis is denial #{attempt_number} in a row on this file. Stop "
                f"retrying -- ask the user directly how to resolve the remaining "
                f"flag(s) instead of attempting another rewrite."
            )
        log_event({"file": file_path, "action": "deny",
                   "kinds": [f["kind"] for f in flags]})
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
        log_event({"file": file_path, "action": "deny", "kinds": kinds})
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"STE100 gate: this Bash command would write {len(result['mechanical_violations'])} "
                    f"mechanically-fixable violation(s) ({', '.join(sorted(set(kinds)))}) to {file_path}. "
                    f"Auto-fix isn't supported for Bash writes -- use the Write or Edit tool instead, "
                    f"where these get corrected automatically."
                ),
            }
        }))
        return

    if result["mechanical_violations"]:
        fixed_text = lint.apply_mechanical_fixes(text)
        updated_input = dict(tool_input)
        if tool_name == "Write":
            updated_input["content"] = fixed_text
        else:
            updated_input["new_string"] = fixed_text
        kinds = [f["kind"] for f in result["mechanical_violations"]]
        log_event({"file": file_path, "action": "auto_fix", "kinds": kinds})
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": (
                    f"STE100 gate: auto-fixed {len(result['mechanical_violations'])} "
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
    # the streak on. Without this, a clean write between two real denials
    # left no trace at all, so the two denial runs looked like one
    # unbroken streak and the retry cap fired on the wrong attempt number --
    # found live: file was denied 3x, written clean once, denied again, and
    # the 4th denial was mislabeled "denial #4 in a row" instead of #1.
    log_event({"file": file_path, "action": "clean", "kinds": []})


if __name__ == "__main__":
    main()
