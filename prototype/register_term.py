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


def register(word, note="", override_unapproved=None):
    """The actual logic, as a pure function: never exits, never prints --
    returns {"ok": bool, "status": str, "message": str}. status is one of
    "registered", "no-op", "refused". Split out from main() so a caller
    that must never terminate the process (the MCP server -- see
    mcp_server.py) can use the exact same validation as the CLI, instead of
    a second copy that could silently diverge from it (the same "duplicated
    logic drifts" lesson this project has already paid for twice with
    detection/fixer pairs -- see project memory)."""
    word = word.strip().lower()
    if not word or " " in word:
        return {"ok": False, "status": "refused", "message": f"'{word}' is not a single word"}

    if word in lint.APPROVED_WORDS:
        return {"ok": True, "status": "no-op",
                "message": f"'{word}' is already approved by the real ASD-STE100 dictionary"}

    is_forbidden = word in lint.UNAPPROVED_MAP or word in lint.UNAPPROVED_NO_REPLACEMENT or word in lint.MODAL_WORDS
    if is_forbidden and not override_unapproved:
        replacement = lint.UNAPPROVED_MAP.get(word)
        hint = f" (suggested replacement: {replacement})" if replacement else " (no replacement given)"
        return {"ok": False, "status": "refused",
                "message": f"'{word}' is explicitly forbidden by the real ASD-STE100 "
                           f"dictionary{hint}. Registering it as a project term would silently "
                           f"override that rule, not fill a genuine coverage gap. If this is "
                           f"really intended, call again with override_unapproved set to a reason."}

    terms = lint._load_project_terms()
    if word in terms:
        return {"ok": True, "status": "no-op",
                "message": f"'{word}' is already registered ({terms[word].get('note', 'no note')})"}

    terms[word] = {"note": override_unapproved or note, "overrides_unapproved": is_forbidden}
    os.makedirs(os.path.dirname(lint.PROJECT_TERMS_PATH), exist_ok=True)
    with open(lint.PROJECT_TERMS_PATH, "w") as f:
        json.dump(terms, f, indent=2, sort_keys=True)
        f.write("\n")

    log_event({"action": "register_term", "word": word,
                "overrides_unapproved": is_forbidden, "note": terms[word]["note"]})
    message = f"registered '{word}'" + (" (overrides a real ASD-STE100 prohibition)" if is_forbidden else "")
    return {"ok": True, "status": "registered", "message": message}


def unregister(word):
    """Remove a word from the glossary. Pure function, same shape as
    register() -- {"ok", "status", "message"}, status one of "removed",
    "no-op" (was never registered). Before this existed, undoing a
    mistaken registration meant hand-editing
    prototype/ste100-project-terms.json directly."""
    word = word.strip().lower()
    terms = lint._load_project_terms()
    if word not in terms:
        return {"ok": True, "status": "no-op", "message": f"'{word}' was not registered"}

    del terms[word]
    with open(lint.PROJECT_TERMS_PATH, "w") as f:
        json.dump(terms, f, indent=2, sort_keys=True)
        f.write("\n")

    log_event({"action": "unregister_term", "word": word})
    return {"ok": True, "status": "removed", "message": f"removed '{word}' from the project glossary"}


def list_terms():
    """All registered terms as {"word": {"note", "overrides_unapproved"}, ...},
    freshly re-read from disk (not the module-level ste100_lint.PROJECT_TERMS
    snapshot, which was loaded once at import time and won't reflect a
    registration made later in the same process)."""
    return lint._load_project_terms()


def main(argv=None):
    """argv defaults to sys.argv[1:] (normal CLI use); an explicit list lets
    stopslop.py's unified dispatcher delegate to this without a subprocess."""
    parser = argparse.ArgumentParser(description="Register a Tier 2 project vocabulary term.")
    parser.add_argument("word")
    parser.add_argument("note", nargs="?", default="")
    parser.add_argument("--override-unapproved", metavar="REASON", default=None,
                         help="Required if the word is already forbidden by the real "
                              "ASD-STE100 dictionary -- registering it anyway silently "
                              "overrides a real rule, not a coverage gap, so it needs an "
                              "explicit, on-the-record reason, not a casual default.")
    args = parser.parse_args(argv)

    result = register(args.word, args.note, args.override_unapproved)
    stream = sys.stdout if result["status"] == "registered" else sys.stderr
    prefix = "" if result["status"] == "registered" else f"{result['status']}: "
    print(f"{prefix}{result['message']}", file=stream)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
