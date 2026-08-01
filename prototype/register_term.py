#!/usr/bin/env python3
"""CLI for Tier 2 registration: add a word to the persistent PROJECT_TERMS
glossary (.claude/ste100-project-terms.json), so check_vocabulary and
_vocab_sub stop flagging it.

This is the human-facing half of the "model suggests, user confirms" flow
the design doc describes: when a live session hits a vocabulary denial (or,
today, an unknown_vocabulary/unapproved_no_replacement/ambiguous flag it
would otherwise just silently pass through -- see pretool_hook.py's
EXCLUDED_VOCAB_TYPES), the agent judges whether the word is genuine
project/domain vocabulary the real ASD-STE100 dictionary was never going to
cover, asks the user to confirm (AskUserQuestion), and only on explicit
approval runs this script. Nothing in this codebase calls it automatically
-- registration is a deliberate, logged, one-word-at-a-time act.

Usage:
    python3 register_term.py WORD ["a short note on why"]
    python3 register_term.py WORD --override-unapproved "why this overrides the standard"
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ste100_lint as lint

PROJECT_ROOT = "/home/asuramaya/code/stopslop/"
HISTORY_LOG = os.path.join(PROJECT_ROOT, ".claude", "ste100-history.log")


def log_event(event):
    try:
        event = dict(event, ts=time.time())
        os.makedirs(os.path.dirname(HISTORY_LOG), exist_ok=True)
        with open(HISTORY_LOG, "a") as f:
            f.write(json.dumps(event) + "\n")
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(description="Register a Tier 2 project vocabulary term.")
    parser.add_argument("word")
    parser.add_argument("note", nargs="?", default="")
    parser.add_argument("--override-unapproved", metavar="REASON", default=None,
                         help="Required if the word is already forbidden by the real "
                              "ASD-STE100 dictionary -- registering it anyway silently "
                              "overrides a real rule, not a coverage gap, so it needs an "
                              "explicit, on-the-record reason, not a casual default.")
    args = parser.parse_args()

    word = args.word.strip().lower()
    if not word or " " in word:
        print(f"refused: '{args.word}' is not a single word", file=sys.stderr)
        sys.exit(1)

    if word in lint.APPROVED_WORDS:
        print(f"no-op: '{word}' is already approved by the real ASD-STE100 dictionary", file=sys.stderr)
        sys.exit(0)

    is_forbidden = word in lint.UNAPPROVED_MAP or word in lint.UNAPPROVED_NO_REPLACEMENT or word in lint.MODAL_WORDS
    if is_forbidden and not args.override_unapproved:
        replacement = lint.UNAPPROVED_MAP.get(word)
        hint = f" (suggested replacement: {replacement})" if replacement else " (no replacement given)"
        print(f"refused: '{word}' is explicitly forbidden by the real ASD-STE100 "
              f"dictionary{hint}. Registering it as a project term would silently "
              f"override that rule, not fill a genuine coverage gap. If this is "
              f"really intended, re-run with --override-unapproved \"reason\".",
              file=sys.stderr)
        sys.exit(1)

    terms = lint._load_project_terms()
    if word in terms:
        print(f"no-op: '{word}' is already registered ({terms[word].get('note', 'no note')})", file=sys.stderr)
        sys.exit(0)

    terms[word] = {
        "note": args.override_unapproved or args.note,
        "overrides_unapproved": is_forbidden,
    }
    os.makedirs(os.path.dirname(lint.PROJECT_TERMS_PATH), exist_ok=True)
    with open(lint.PROJECT_TERMS_PATH, "w") as f:
        json.dump(terms, f, indent=2, sort_keys=True)
        f.write("\n")

    log_event({"action": "register_term", "word": word,
                "overrides_unapproved": is_forbidden, "note": terms[word]["note"]})
    print(f"registered '{word}'" + (" (overrides a real ASD-STE100 prohibition)" if is_forbidden else ""))


if __name__ == "__main__":
    main()
