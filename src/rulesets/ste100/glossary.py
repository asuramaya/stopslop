#!/usr/bin/env python3
"""CLI/library for Tier 2 registration: add a word to the persistent
PROJECT_TERMS glossary, so check_vocabulary and _vocab_sub stop flagging
it. Formerly prototype/register_term.py. Storage is core.config's generic
wordlist store (stopslop.config.json, list_id "project_terms" under
ruleset "ste100") -- see lint.py's _migrate_legacy_project_terms for the
one-time move off the old bespoke project-terms.json file.

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
import sys

from rulesets.ste100 import lint
from core import history, paths, terms as _terms


def validate_term(term, force):
    """core.terms.add_term's validator hook for ste100's project vocabulary.

    This is the ONE thing that makes ste100's term list different from
    slopwatch's or codewatch's: there is a real external standard behind it,
    so a registration can be checked against something. That difference used
    to justify an entire parallel API ("glossary" vs "wordlists"); it is now
    one optional callback on one shared primitive, which is all it ever
    warranted.

    Returns (result_or_None, extra_metadata). A non-None result short-
    circuits add_term. extra_metadata is stored beside the note, which is
    how "this registration knowingly overrode a real prohibition" stays
    visible on the record afterwards rather than looking like an ordinary
    coverage-gap entry."""
    if " " in term:
        return {"ok": False, "status": "refused",
                "message": f"'{term}' is not a single word"}, {}
    if term in lint.APPROVED_WORDS:
        return {"ok": True, "status": "no-op",
                "message": f"'{term}' is already approved by the real "
                            f"ASD-STE100 dictionary"}, {}

    is_forbidden = (term in lint.UNAPPROVED_MAP
                    or term in lint.UNAPPROVED_NO_REPLACEMENT
                    or term in lint.MODAL_WORDS)
    if is_forbidden and not force:
        replacement = lint.UNAPPROVED_MAP.get(term)
        hint = f" (suggested replacement: {replacement})" if replacement else " (no replacement given)"
        return {"ok": False, "status": "refused",
                "message": f"'{term}' is explicitly forbidden by the real ASD-STE100 "
                            f"dictionary{hint}. Registering it as a project term would "
                            f"silently override that rule, not fill a genuine coverage "
                            f"gap. If this is really intended, call again with "
                            f"override_unapproved set to a reason."}, {}
    return None, {"overrides_unapproved": is_forbidden}


def register(word, note="", override_unapproved=None, history_path=None):
    """The actual logic, as a pure function: never exits, never prints --
    returns {"ok": bool, "status": str, "message": str}. status is one of
    "registered", "no-op", "refused". Split out from main() so a caller
    that must never terminate the process (the MCP server) can use the
    exact same validation as the CLI, instead of a second copy that could
    silently diverge from it.

    history_path is optional: when given, the registration is also logged
    to the shared gate-activity log via core.history.log_event, tagged
    ruleset="ste100"."""
    word = word.strip().lower()
    if not word:
        return {"ok": False, "status": "refused", "message": "'' is not a single word"}

    project_root = paths.find_project_root(__file__)
    result = _terms.add_term(
        "ste100", lint.TERM_LISTS, project_root, "project_terms", word,
        note=override_unapproved or note, force=bool(override_unapproved),
        validator=validate_term)
    if result["status"] != "registered":
        return result

    is_forbidden = result.get("metadata", {}).get("overrides_unapproved", False)
    # Refresh the in-process copy, not just the file on disk -- lint.py
    # loads PROJECT_TERMS once at import time, so a long-running process
    # (mcp_server.py, one process for the whole session) would otherwise
    # keep flagging this exact word right after registering it.
    lint.PROJECT_TERMS = lint._load_manual_terms()

    if history_path:
        history.log_event(
            {"action": "register_term", "word": word,
             "overrides_unapproved": is_forbidden,
             "note": override_unapproved or note},
            "ste100", history_path)
    return {"ok": True, "status": "registered",
            "message": f"registered '{word}'" +
                        (" (overrides a real ASD-STE100 prohibition)" if is_forbidden else "")}


def unregister(word, history_path=None):
    """Remove a word from the glossary. Pure function, same shape as
    register() -- {"ok", "status", "message"}, status one of "removed",
    "no-op" (was never registered)."""
    word = word.strip().lower()
    project_root = paths.find_project_root(__file__)
    result = _terms.remove_term("ste100", lint.TERM_LISTS, project_root,
                                 "project_terms", word)
    if result["status"] == "no-op":
        return result

    lint.PROJECT_TERMS = lint._load_manual_terms()  # see register()'s comment on why
    if history_path:
        history.log_event({"action": "unregister_term", "word": word,
                            "status": result["status"]}, "ste100", history_path)
    # "suppressed" (the word came from a pack or a built-in, so a tombstone
    # was written) is a real outcome, not a failure to find anything --
    # passing the primitive's own message through keeps that distinction.
    return result


def list_terms():
    """Every MANUALLY registered term (never a vocabulary pack's content --
    packs are a separate layer, resolved per path) as {"word": {"note",
    "overrides_unapproved"}, ...}, freshly re-read from disk rather than
    from the module-level lint.PROJECT_TERMS snapshot, which won't reflect
    a registration made later in the same process by another caller."""
    return lint._load_manual_terms()


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
