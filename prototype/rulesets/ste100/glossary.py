#!/usr/bin/env python3
"""CLI/library for Tier 2 registration: add a word to the persistent
PROJECT_TERMS glossary (project-terms.json), so check_vocabulary and
_vocab_sub stop flagging it. Formerly prototype/register_term.py.

This is the human-facing half of the "model suggests, user confirms" flow
the design doc describes: when a live session hits a vocabulary denial (or,
today, an unknown_vocabulary/unapproved_no_replacement/ambiguous flag it
would otherwise just silently pass through -- see EXCLUDED_VOCAB_TYPES in
lint.py), the agent judges whether the word is genuine project/domain
vocabulary the real ASD-STE100 dictionary was never going to cover, asks the
user to confirm (AskUserQuestion), and only on explicit approval calls
register(). Nothing in this codebase calls it automatically -- registration
is a deliberate, logged, one-word-at-a-time act.

Usage:
    python3 glossary.py WORD ["a short note on why"]
    python3 glossary.py WORD --override-unapproved "why this overrides the standard"
"""
import argparse
import json
import os
import sys

from rulesets.ste100 import lint
from core import history, paths


def register(word, note="", override_unapproved=None, history_path=None):
    """The actual logic, as a pure function: never exits, never prints --
    returns {"ok": bool, "status": str, "message": str}. status is one of
    "registered", "no-op", "refused". Split out from main() so a caller
    that must never terminate the process (the MCP server) can use the
    exact same validation as the CLI, instead of a second copy that could
    silently diverge from it.

    history_path is optional: when given, the registration is also logged
    to the shared gate-activity log via core.history.log_event, tagged
    ruleset="ste100". Callers that don't want log side effects (tests,
    library use with no repo context) simply omit it."""
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
    # Refresh the in-process copy, not just the file on disk -- lint.py
    # loads PROJECT_TERMS once at import time, so a long-running process
    # (mcp_server.py, one process for the whole session) would otherwise
    # keep flagging this exact word right after registering it.
    lint.PROJECT_TERMS = lint._load_project_terms()

    if history_path:
        history.log_event(
            {"action": "register_term", "word": word,
             "overrides_unapproved": is_forbidden, "note": terms[word]["note"]},
            "ste100", history_path)
    message = f"registered '{word}'" + (" (overrides a real ASD-STE100 prohibition)" if is_forbidden else "")
    return {"ok": True, "status": "registered", "message": message}


def unregister(word, history_path=None):
    """Remove a word from the glossary. Pure function, same shape as
    register() -- {"ok", "status", "message"}, status one of "removed",
    "no-op" (was never registered)."""
    word = word.strip().lower()
    terms = lint._load_project_terms()
    if word not in terms:
        return {"ok": True, "status": "no-op", "message": f"'{word}' was not registered"}

    del terms[word]
    with open(lint.PROJECT_TERMS_PATH, "w") as f:
        json.dump(terms, f, indent=2, sort_keys=True)
        f.write("\n")
    lint.PROJECT_TERMS = lint._load_project_terms()  # see register()'s comment on why

    if history_path:
        history.log_event({"action": "unregister_term", "word": word}, "ste100", history_path)
    return {"ok": True, "status": "removed", "message": f"removed '{word}' from the project glossary"}


def list_terms():
    """All registered terms as {"word": {"note", "overrides_unapproved"}, ...},
    freshly re-read from disk (not the module-level lint.PROJECT_TERMS
    snapshot, which won't reflect a registration made later in the same
    process by another caller)."""
    return lint._load_project_terms()


def main(argv=None, history_path=None):
    """argv defaults to sys.argv[1:] (normal CLI use); an explicit list lets
    stopslop.py's unified dispatcher delegate to this without a subprocess.
    history_path defaults to this repo's real shared log when run as a
    script directly (matching the pre-refactor behavior of always logging),
    but can be overridden or suppressed by a caller that manages its own."""
    parser = argparse.ArgumentParser(description="Register a Tier 2 project vocabulary term.")
    parser.add_argument("word")
    parser.add_argument("note", nargs="?", default="")
    parser.add_argument("--override-unapproved", metavar="REASON", default=None,
                         help="Required if the word is already forbidden by the real "
                              "ASD-STE100 dictionary -- registering it anyway silently "
                              "overrides a real rule, not a coverage gap, so it needs an "
                              "explicit, on-the-record reason, not a casual default.")
    args = parser.parse_args(argv)

    if history_path is None:
        history_path = history.history_log_path(paths.find_project_root(__file__))
    result = register(args.word, args.note, args.override_unapproved, history_path=history_path)
    stream = sys.stdout if result["status"] == "registered" else sys.stderr
    prefix = "" if result["status"] == "registered" else f"{result['status']}: "
    print(f"{prefix}{result['message']}", file=stream)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
