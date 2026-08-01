#!/usr/bin/env python3
"""Reads .claude/ste100-history.log (written by pretool_hook.py on every
deny/auto_fix event) and generates .claude/ste100-memory.md: a short,
principle-level summary of recurring violation patterns, per the design
doc's section 6.2 ("Coaching Principle" -- abstract patterns, not word
lists, kept small enough to be cheap to inject at session start).

A near-simultaneous duplicate log entry was observed once and initially
attributed to Claude Code firing PreToolUse twice per tool call -- since
corrected (task #6, project memory): every timestamped event since has been
exactly one per real tool call. The original observation is much better
explained by a manual pipe-test run with identical content immediately
before the live call that "confirmed" it. This script still collapses
entries that are the same logical event fired within a couple seconds of
each other via the "ts" field pretool_hook.py writes -- cheap, harmless
defense in case a real double-fire occurs under some condition not yet
seen -- without collapsing genuinely separate repeat events on the same
file just because their content happens to match too (an earlier
content-only dedup did exactly that, which would have under-counted a
violation type that kept recurring across real retries).
"""
import json
import os
import sys
from collections import Counter

PROJECT_ROOT = "/home/asuramaya/code/stopslop/"
HISTORY_LOG = os.path.join(PROJECT_ROOT, ".claude", "ste100-history.log")
MEMORY_FILE = os.path.join(PROJECT_ROOT, ".claude", "ste100-memory.md")

PRINCIPLE_TEXT = {
    "modal": "Hedging modals (should/would/may/might/could) keep showing up -- "
             "resolve intent before drafting: must for requirements, delete or "
             "state as fact for recommendations, can for real possibility.",
    "passive": "Passive voice with an unclear actor keeps showing up -- name the "
               "actor, or restructure to active voice.",
    "ing_form": "-ing misuse keeps showing up -- infinitive or simple tense "
               "unless it's one of the ~9 whitelisted -ing nouns/adjectives.",
    "progressive": "Progressive tense (is/are/was/were + -ing) keeps showing up -- "
                   "use simple tense instead.",
    "length": "Sentences keep running long -- split at the clause boundary "
              "before drafting, don't write long then split after.",
    "punctuation": "Contractions or semicolons keep showing up -- write "
                   "contractions in full; use two sentences instead of a semicolon.",
    "perfect_tense": "Present-perfect / present-perfect-passive constructions "
                     "(has/have/had (been) + V-ed) keep showing up -- use simple "
                     "past instead.",
    "vocabulary": "Unapproved synonyms (utilize, leverage, seamlessly, etc.) "
                  "keep showing up -- use the plain equivalent from the start.",
    "trailing_condition": "Conditions keep trailing after the command -- put "
                          "'if'/'when' clauses at the start of the sentence.",
    "synonym_rotation": "The same concept keeps getting named with rotating "
                        "synonyms (check/verify/confirm...) -- pick one term "
                        "per concept before drafting and stay with it.",
}


DOUBLE_FIRE_WINDOW_SECONDS = 2.0


def dedupe_consecutive(events):
    out = []
    prev = None
    for e in events:
        if (prev is not None
                and e.get("file") == prev.get("file")
                and e.get("action") == prev.get("action")
                and sorted(e.get("kinds", [])) == sorted(prev.get("kinds", []))
                and (e.get("ts", 0) - prev.get("ts", 0)) < DOUBLE_FIRE_WINDOW_SECONDS):
            prev = e
            continue
        out.append(e)
        prev = e
    return out


def regenerate():
    """Does the actual work, silently -- no stdout/stderr output. Returns a
    short status string ('no-log', 'no-violations', or 'wrote:<path>') for
    the caller to report however fits its own context. Split out from
    main() so pretool_hook.py can call this inline after every log_event()
    (see that module for why: PostToolUse never fires after a PreToolUse
    denial, so this can't run as a separate hook without missing every
    deny -- exactly the event this coaching loop most needs to learn from.
    A print() here would corrupt pretool_hook.py's own stdout, which
    Claude Code parses as the hook's JSON response -- silence is required,
    not just tidy."""
    if not os.path.exists(HISTORY_LOG):
        return "no-log"

    events = []
    with open(HISTORY_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    events = dedupe_consecutive(events)

    kind_counts = Counter()
    for e in events:
        for k in e.get("kinds", []):
            kind_counts[k] += 1

    if not kind_counts:
        return "no-violations"

    ranked = kind_counts.most_common(5)  # keep it small -- ~200 token budget

    lines = [
        "# STE100 Coaching Memory (auto-generated)",
        f"# Based on {len(events)} gate event(s) in .claude/ste100-history.log",
        "",
        "## Recurring patterns (highest frequency first)",
        "",
    ]
    for kind, count in ranked:
        text = PRINCIPLE_TEXT.get(kind, f"'{kind}' violations keep showing up.")
        lines.append(f"- ({count}x) {text}")

    content = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        f.write(content)
    return f"wrote:{MEMORY_FILE}"


def main():
    status = regenerate()
    if status == "no-log":
        print("No history log yet -- nothing to summarize.", file=sys.stderr)
    elif status == "no-violations":
        print("History log has no violation events yet.", file=sys.stderr)
    else:
        path = status.split(":", 1)[1]
        with open(path) as f:
            content = f.read()
        print(f"Wrote {path} ({len(content.split())} words, ~{len(content)//4} tokens)")


if __name__ == "__main__":
    main()
