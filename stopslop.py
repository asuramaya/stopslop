#!/usr/bin/env python3
"""stopslop: one entry point for everything a person actually does with
this tool by hand. The gate itself (prototype/pretool_hook.py,
sessionstart_hook.py) runs automatically once wired up via Claude Code
hooks and never needs a person to invoke it directly -- this script is for
the parts that do: first-time setup, an ad-hoc compliance check outside a
live write, registering project vocabulary, and checking the tool's own
state. Before this existed, each of those was a separate script under
prototype/ that a person could only find by reading source.

    stopslop.py init                 wire up .claude/settings.local.json
    stopslop.py lint TEXT            check text without writing it anywhere
    stopslop.py lint --file PATH     check an existing file the same way
    stopslop.py register WORD [NOTE] add a project-glossary term
    stopslop.py status               dictionary/glossary/gate-activity summary
"""
import argparse
import json
import os
import sys
from collections import Counter

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_DIR = os.path.join(REPO_ROOT, "prototype")
sys.path.insert(0, PROTOTYPE_DIR)

HISTORY_LOG = os.path.join(REPO_ROOT, ".claude", "ste100-history.log")
SETTINGS_EXAMPLE = os.path.join(REPO_ROOT, ".claude", "settings.local.json.example")
SETTINGS_REAL = os.path.join(REPO_ROOT, ".claude", "settings.local.json")


def cmd_init(args):
    if os.path.exists(SETTINGS_REAL) and not args.force:
        print(f"{SETTINGS_REAL} already exists -- not overwriting.")
        print("Re-run with --force if you really want to replace it.")
        return 1

    with open(SETTINGS_EXAMPLE) as f:
        settings = json.load(f)

    # The example ships with a placeholder path; substitute this actual
    # clone's location so nobody has to hand-edit JSON to get started.
    pretool_path = os.path.join(PROTOTYPE_DIR, "pretool_hook.py")
    sessionstart_path = os.path.join(PROTOTYPE_DIR, "sessionstart_hook.py")
    settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = f"python3 {pretool_path}"
    settings["hooks"]["SessionStart"][0]["hooks"][0]["command"] = f"python3 {sessionstart_path}"

    os.makedirs(os.path.dirname(SETTINGS_REAL), exist_ok=True)
    with open(SETTINGS_REAL, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print(f"Wrote {SETTINGS_REAL}")
    print("Start (or restart) a Claude Code session in this directory to pick it up.")
    return 0


def cmd_lint(args):
    import ste100_lint as lint

    if args.file:
        with open(args.file) as f:
            text = f.read()
    elif args.text:
        text = " ".join(args.text)
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("Nothing to check.", file=sys.stderr)
        return 1

    result = lint.lint_and_gate(text, context=args.context)
    mechanical = result["mechanical_violations"]
    # Same filter the live gate applies (lint.blocking_semantic_flags) --
    # this command reports what a real write would actually do, not every
    # flag the engine can produce. The full, unfiltered set (including
    # unknown/forbidden vocabulary staged out of denial for now) is
    # available with --all.
    blocking = lint.blocking_semantic_flags(result["semantic_flags"])
    excluded_count = len(result["semantic_flags"]) - len(blocking)
    semantic = result["semantic_flags"] if args.all else blocking

    if not mechanical and not semantic:
        if excluded_count and not args.all:
            print(f"PASS -- would go through the live gate unchanged "
                  f"({excluded_count} vocabulary note(s) hidden, see --all).")
        else:
            print("PASS -- clean, no violations.")
        return 0

    if semantic:
        print(f"FAIL -- {len(semantic)} issue(s) need a person's judgment:\n")
        for f in semantic:
            d = f["detail"]
            label = d.get("word") or d.get("phrase") or d.get("modal") or d.get("rule", "?")
            rule = d.get("rule", "?")
            note = d.get("note") or d.get("basis") or ""
            extra = f" -- {note}" if note else ""
            print(f"  [{f['kind']}, rule {rule}] {label!r}{extra}")
        print()

    if mechanical:
        print(f"{len(mechanical)} mechanical fix(es) would be applied automatically on a real write:\n")
        for m in mechanical:
            d = m["detail"]
            label = d.get("word") or d.get("phrase") or d.get("modal") or d.get("rule", "?")
            repl = d.get("replacement")
            arrow = f" -> {repl!r}" if repl else ""
            print(f"  [{m['kind']}] {label!r}{arrow}")

    return 1 if semantic else 0


def cmd_register(args):
    import register_term
    return register_term.main(args.rest) or 0


def _read_history():
    if not os.path.exists(HISTORY_LOG):
        return []
    events = []
    with open(HISTORY_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def cmd_status(args):
    import ste100_lint as lint

    print("stopslop status\n")

    print(f"Dictionary:      {len(lint.APPROVED_WORDS)} approved words, "
          f"{len(lint.UNAPPROVED_MAP) + len(lint.UNAPPROVED_NO_REPLACEMENT)} forbidden words")
    print(f"Project terms:   {len(lint.PROJECT_TERMS)} registered "
          f"(prototype/ste100-project-terms.json)")

    events = _read_history()
    action_counts = Counter(e.get("action") for e in events)
    print(f"\nGate activity:   {len(events)} event(s) logged")
    for action in ("deny", "auto_fix", "clean", "unscoped_write", "register_term"):
        if action_counts.get(action):
            print(f"  {action:16s} {action_counts[action]}")

    memory_path = os.path.join(REPO_ROOT, ".claude", "ste100-memory.md")
    if os.path.exists(memory_path):
        with open(memory_path) as f:
            pattern_count = f.read().count("\n- (")
        print(f"\nCoaching memory: {pattern_count} recurring pattern(s) tracked "
              f"(.claude/ste100-memory.md)")
    else:
        print("\nCoaching memory: none yet -- no gate activity logged so far")

    integrity_path = os.path.join(REPO_ROOT, ".claude", "ste100-integrity.json")
    print(f"\nIntegrity:       {'baseline recorded' if os.path.exists(integrity_path) else 'not established yet -- start a session to record one'}")

    settings_status = "configured" if os.path.exists(SETTINGS_REAL) else "NOT SET UP -- run `stopslop.py init`"
    print(f"Hook wiring:     {settings_status}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="stopslop.py",
        description="stopslop: an STE100 Gatekeeper System prototype. "
                     "The gate runs automatically once `init` has wired it up; "
                     "these commands are for everything else a person does by hand.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="wire up .claude/settings.local.json for this clone")
    p_init.add_argument("--force", action="store_true", help="overwrite an existing settings file")
    p_init.set_defaults(func=cmd_init)

    p_lint = sub.add_parser("lint", help="check text or a file without writing it anywhere")
    p_lint.add_argument("text", nargs="*", help="text to check (omit to read a file or stdin instead)")
    p_lint.add_argument("--file", help="check an existing file's content instead of inline text")
    p_lint.add_argument("--context", choices=["procedure", "description"], default="description",
                         help="procedure = 20-word sentence limit (real ASD-STE100 step-by-step "
                              "instructions); description = 25-word limit (default, matches what "
                              "the live gate uses for whole documents)")
    p_lint.add_argument("--all", action="store_true",
                         help="show every flag the engine produces, including vocabulary notes "
                              "the live gate doesn't currently act on (see README's gap list)")
    p_lint.set_defaults(func=cmd_lint)

    p_register = sub.add_parser("register", help="add a word to the project glossary (Tier 2)",
                                 add_help=False)
    p_register.add_argument("rest", nargs=argparse.REMAINDER,
                             help="WORD [NOTE] [--override-unapproved REASON]")
    p_register.set_defaults(func=cmd_register)

    p_status = sub.add_parser("status", help="dictionary, glossary, and gate-activity summary")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
