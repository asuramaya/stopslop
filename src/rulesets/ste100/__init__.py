"""Contract surface for the ste100 ruleset -- the thin wrapper the core
dispatcher (pretool_hook.py, stopslop.py, mcp_server.py) actually talks to.
All real rule logic lives in lint.py; all glossary logic lives in
glossary.py. This module only assembles them into the shape
rulesets/__init__.py's registration check requires, plus the two pieces
(context defaulting, history-log wiring) that are genuinely ste100's own
policy rather than generic plumbing.
"""
from rulesets.ste100 import lint, glossary
from core import checks as _checks, glossary_packs as _glossary_packs, history, paths, terms as _terms

RULESET_ID = "ste100"
# "STE100", not "ASD-STE100" -- matches the exact prefix the pre-refactor
# hook used in every deny/auto_fix message ("STE100 gate: ..."), kept
# byte-for-byte to satisfy this refactor's own backward-compatibility bar
# (see docs/incidents/ and the hook-output diff run during migration).
RULESET_NAME = "STE100"
# The same per-check {threshold, action} surface as slopwatch and
# codewatch. ste100 was the last ruleset on the older ruleset-wide
# "options" mechanism, and its leftovers (excluded_vocab_types, a
# format()ed DENY_POLICY sentence, sparse CHECK_OPTIONS columns) were the
# special cases every consumer had to branch around. Rule 5.1's word
# limits live on the `length` check's own config entry now -- see
# lint.DEFAULT_CHECK_CONFIG.
CAPABILITIES = frozenset({"terms", "word_lookup", "checks", "check_config"})

# Relative to this package's own directory -- integrity_check.py resolves
# these against the ruleset's install location, not the repo root.
# No "glossary_packs/*": packs moved to core/glossary_packs/ (ruleset-
# agnostic now) -- see integrity_check.py's own CORE_TRACKED_FILES, which
# tracks them there instead. No "project-terms.json": Tier-2 project terms
# are project-editable config now (stopslop.config.json's "wordlists"
# key), not shipped enforcement data -- the same reason stopslop.config.json
# itself was never in this list. Integrity tracking is for "did the
# standard's own fixed data or rule logic change," not "did the project
# register a word."
TRACKED_FILES = ["dictionary.json", "lint.py", "glossary.py", "build_dictionary.py"]

def _history_path():
    return history.history_log_path(paths.find_project_root(__file__))


def lint_and_gate(text, *, context=None, file_path=None):
    """context: "procedure" (20-word limit, step-by-step instructions) or
    "description" (25-word limit, whole documents). Any other value
    (including None, the contract's default) falls back to "description" --
    ste100's own validation, per the plugin contract leaving context
    interpretation to each ruleset."""
    ctx = context if context in ("procedure", "description") else "description"
    return lint.lint_and_gate(text, context=ctx, file_path=file_path)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text, file_path=None):
    return lint.apply_mechanical_fixes(text, file_path=file_path)


TERM_LISTS = lint.TERM_LISTS
CHECKS_TABLE = lint.CHECKS_TABLE


def list_check_config():
    return _checks.list_check_config(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID)


def set_check_config(check_id, threshold=None, action=None, **params):
    _checks.set_check_config(lint.CHECKS_TABLE, paths.find_project_root(__file__),
                              RULESET_ID, check_id, threshold=threshold, action=action, **params)


def list_term_lists(file_path=None):
    """ste100's one term list (project vocabulary), in the same shape
    slopwatch's five and codewatch's one report -- see core/terms.py.
    file_path matters here: which vocabulary packs are layered in depends
    on the routing rule matching the file, not on the ruleset."""
    return _terms.list_term_lists(RULESET_ID, TERM_LISTS,
                                   paths.find_project_root(__file__),
                                   file_path=file_path)


def add_term(list_id, term, note="", force=False):
    """Uniform contract entry point, for EVERY list this ruleset declares.

    It used to raise UnknownTermListError for anything but project_terms,
    which was two untruths at once: the list is declared right here in
    TERM_LISTS, and the caller had done nothing wrong. It also opted this
    ruleset out of the shared primitive it is supposed to be built on.
    approved_words and unapproved_words are the published dictionary, so
    they carry accepts_additions=False and core.terms refuses an addition
    with a reason -- the same refusal shape every other path returns.

    project_terms keeps the validator, which is ste100's one genuine
    difference: a real external standard exists to check a word against."""
    if list_id == "project_terms":
        # `force` is a bool in the uniform contract but a REASON string in
        # ste100's own register(): overriding a real prohibition has to go
        # on the record with why. A bare force=True falls back to the note.
        reason = (force if isinstance(force, str)
                  else (note or "forced via add_term") if force else None)
        return glossary.register(term, note, reason, history_path=_history_path())
    return _terms.add_term(RULESET_ID, TERM_LISTS,
                            paths.find_project_root(__file__),
                            list_id, term, note=note, force=force)


def remove_term(list_id, term):
    """Removal works on every list, including the shipped dictionary.

    Removing a dictionary word cannot delete it -- the word lives in
    dictionary.json -- so core.terms records a tombstone the resolver
    subtracts. "This project does not accept this approved word" is exactly
    the curation the subtraction model was added for, and ste100 was the
    one ruleset that could not do it."""
    if list_id == "project_terms":
        return glossary.unregister(term, history_path=_history_path())
    return _terms.remove_term(RULESET_ID, TERM_LISTS,
                               paths.find_project_root(__file__), list_id, term)



def check_word(word):
    """Look up a single word against the real ASD-STE100 dictionary and
    this project's own glossary. Returns whether it's approved, forbidden
    (with a replacement if the standard gives one), a registered project
    term, a modal needing resolution, or simply not covered by any of
    those. Cheaper than lint_and_gate when all you need is one word's
    status, e.g. before choosing how to phrase a sentence.

    Handles modal words explicitly: lint.check_vocabulary() deliberately
    never classifies should/would/may/might/could (check_modals is the only
    function that does -- see the comment above MODAL_WORDS' use in
    lint.check_vocabulary), so without this branch a modal would fall
    through to the "approved" case below, even though modals are this
    project's single most-flagged violation category."""
    lw = word.strip().lower()
    if lw in lint.MODAL_WORDS:
        hit = lint.check_modals(word)[0]
        return {
            "word": word, "status": "modal", "rule": hit["rule"],
            "auto_fix": hit["auto_fix"], "replacement": hit.get("replacement"),
            "note": hit.get("note") or hit.get("basis"),
        }
    violations = lint.check_vocabulary(word)
    if not violations:
        effective = lint.effective_project_terms()
        if lw in effective:
            return {"word": word, "status": "project_term",
                    "note": effective[lw].get("note", "")}
        return {"word": word, "status": "approved"}
    v = violations[0]
    return {
        "word": word,
        "status": v["type"],
        "replacement": v.get("replacement"),
        "rule": v.get("rule"),
    }


def stats():
    return {
        "approved_words": str(len(lint.APPROVED_WORDS)),
        "forbidden_words": str(len(lint.UNAPPROVED_MAP) + len(lint.UNAPPROVED_NO_REPLACEMENT)),
        "project_terms": str(len(lint.effective_project_terms())),
    }


def list_checks():
    return _checks.list_checks(lint.CHECKS_TABLE, paths.find_project_root(__file__), RULESET_ID)


def set_enabled_checks(check_ids):
    _checks.set_enabled_checks(lint.CHECKS_TABLE, paths.find_project_root(__file__),
                                RULESET_ID, check_ids)


def set_checks_enabled(states):
    _checks.set_checks_enabled(lint.CHECKS_TABLE, paths.find_project_root(__file__),
                                RULESET_ID, states)


# list_glossary_packs()/set_enabled_glossary_packs() USED to live here: two
# bare functions the ruleset registry knew nothing about, which
# dashboard.py, stopslop.py and mcp_server.py each reached for with a
# hasattr() guess. They are gone, not moved -- a pack is enabled on a PATH
# GLOB, not on a ruleset (core.config.packs_for_path / set_rule_packs), so
# there was never a ruleset method for them to be. That mismatch is exactly
# why they sat outside the contract for as long as they did.
