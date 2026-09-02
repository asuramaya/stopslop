"""Shared gate-activity log: one append-only JSONL stream at
.claude/stopslop-history.log, read and written through this module rather
than each caller keeping its own copy. Before this consolidation,
pretool_hook.py and register_term.py each defined their own near-identical
log_event(), and status_report.py's history reader never applied the same
double-fire dedup pretool_hook.py's own count_consecutive_denials() already
did -- silently inflating gate-activity counts whenever a near-simultaneous
duplicate log entry occurred. Found while building this module; fixed by
giving every reader exactly one implementation to go stale in, the same
"duplicated logic drifts" lesson this project has already paid for twice
with detection/fixer pairs (see rulesets/ste100/lint.py's own history).

Each event now carries a "ruleset" field identifying which ruleset produced
it, since the log is shared across all rulesets going forward. Legacy log
lines written before this field existed (the single-ruleset era) are read
back as ruleset="ste100" -- see read_history() below -- so no historical
line needs rewriting.

log_event() is deliberately a pure append: it has no opinion on whether a
caller should also regenerate that ruleset's coaching memory afterward.
pretool_hook.py's gate events do (that's the signal the coaching loop
learns from); glossary registration events deliberately don't (they carry
no "kinds" for the coaching aggregator to act on, so regenerating after one
would be pure wasted I/O) -- that asymmetry existed before this
consolidation and is preserved by leaving it to each caller rather than
baking one behavior into this module.
"""
import json
import os
import time

DOUBLE_FIRE_WINDOW_SECONDS = 2.0

_LEGACY_HISTORY_NAME = "ste100-history.log"
_HISTORY_NAME = "stopslop-history.log"


def history_log_path(project_root):
    path = os.path.join(project_root, ".claude", _HISTORY_NAME)
    legacy_path = os.path.join(project_root, ".claude", _LEGACY_HISTORY_NAME)
    if not os.path.exists(path) and os.path.exists(legacy_path):
        # One-time best-effort migration from the pre-ruleset filename --
        # never breaks the gate if it fails, same principle as every other
        # try/except in this module.
        try:
            os.rename(legacy_path, path)
        except OSError:
            return legacy_path  # keep reading/writing the old file rather than losing history
    return path


def log_event(event, ruleset_id, history_path):
    """Append one event, tagged with which ruleset produced it."""
    try:
        record = dict(event, ruleset=ruleset_id, ts=time.time())
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        with open(history_path, "a") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # logging must never break the gate itself


def read_history(history_path):
    """All events, oldest first, silently skipping unparseable lines.
    Legacy (pre-ruleset) lines default to ruleset="ste100"."""
    if not os.path.exists(history_path):
        return []
    events = []
    with open(history_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            e.setdefault("ruleset", "ste100")
            events.append(e)
    return events


def dedupe_double_fire(events):
    """Collapse entries that are the SAME logical event fired twice (same
    file+action, within DOUBLE_FIRE_WINDOW_SECONDS of each other) -- but,
    unlike naive content-equality dedup, does NOT collapse genuinely
    separate repeat events (e.g. three real consecutive denials minutes
    apart) just because their file+action happen to match. Older log
    entries written before the "ts" field existed sort first (ts=0) and
    never merge with anything, which is safe -- undercounts by at most one
    pre-timestamp entry, never overcounts.

    Requires a real "file" value on both sides -- gate-decision events
    (deny/auto_fix/clean/unscoped_write) always have one; glossary events
    (register_term/unregister_term) never do. Without this guard, every
    e.get("file") on a fileless event resolves to the same None, so any
    burst of distinct registrations fired within the window (e.g. seeding
    a glossary from a word list) silently collapsed into one entry --
    found live while consolidating this function out of pretool_hook.py:
    a real run of 40+ distinct register_term events undercounted to 7."""
    out = []
    prev = None
    for e in events:
        if (prev is not None
                and e.get("file") is not None
                and e.get("file") == prev.get("file")
                and e.get("action") == prev.get("action")
                and (e.get("ts", 0) - prev.get("ts", 0)) < DOUBLE_FIRE_WINDOW_SECONDS):
            prev = e
            continue
        out.append(e)
        prev = e
    return out


def read_history_deduped(history_path):
    """The one path every consumer (retry-cap counting, recent-deny
    signaling, status reporting) should read through, so double-fire
    handling can't silently diverge between them again."""
    return dedupe_double_fire(read_history(history_path))


def count_consecutive_denials(file_path, history_path):
    """How many times in a row has this exact file been denied, with no
    successful write in between?"""
    deduped = read_history_deduped(history_path)
    count = 0
    for e in reversed(deduped):
        if e.get("file") != file_path:
            continue  # other files don't affect this file's streak
        if e.get("action") == "deny":
            count += 1
        else:
            break  # a successful write for this file resets the streak
    return count


def recent_deny_nearby(history_path, window_seconds=300):
    """Cheap, non-conclusive signal: was there any deny event, on any file,
    in roughly the last few minutes? Deliberately NOT a verdict that this IS
    evasion -- just a timestamp-proximity fact on the record for a human to
    judge, not a conclusion the gate draws on its own."""
    events = read_history(history_path)
    now = time.time()
    return any(e.get("action") == "deny" and (now - e.get("ts", 0)) < window_seconds
               for e in events[-20:])


# Actions that represent the gate actually judging a piece of text. A
# config write or a term registration is not a gate event and must not
# count toward "how many chances has this check had to fire".
GATE_ACTIONS = frozenset({"deny", "auto_fix", "clean"})


def check_hit_counts(history_path, ruleset_id=None):
    """How often each check has actually fired, out of how many gate events.

    Returns (hits, gate_events): a dict of check_id -> count, and the
    number of judged writes those counts are drawn from. Scoped to one
    ruleset when `ruleset_id` is given, because a check id means nothing
    across rulesets and two of them could share a name.

    This exists to answer a question the dashboard could not: which
    checks earn their keep. A ruleset's check set decays -- this project
    measured five checks drawn from a 2023-24 catalogue of AI writing
    tells firing zero times against current model output -- and the only
    way anyone noticed was by scoring corpora offline. A check that has
    never fired across hundreds of judged writes is either aimed at
    something that has stopped happening, or is broken. Both are worth
    seeing, and neither is visible from the check's own definition.

    Reads the deduped history for the same reason every other consumer
    does: a double-fired event would otherwise inflate a check's count
    and make dead weight look busy.
    """
    hits = {}
    gate_events = 0
    for event in read_history_deduped(history_path):
        if event.get("action") not in GATE_ACTIONS:
            continue
        if ruleset_id is not None and event.get("ruleset") != ruleset_id:
            continue
        gate_events += 1
        for kind in event.get("kinds") or ():
            hits[kind] = hits.get(kind, 0) + 1
    return hits, gate_events
