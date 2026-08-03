"""Contract surface for the ste100 ruleset -- the thin wrapper the core
dispatcher (pretool_hook.py, stopslop.py, mcp_server.py) actually talks to.
All real rule logic lives in lint.py; all glossary logic lives in
glossary.py. This module only assembles them into the shape
rulesets/__init__.py's registration check requires, plus the two pieces
(context defaulting, history-log wiring) that are genuinely ste100's own
policy rather than generic plumbing.
"""
from rulesets.ste100 import lint, glossary
from core import config as _core_config, glossary_packs as _glossary_packs, history, paths, terms as _terms

RULESET_ID = "ste100"
# "STE100", not "ASD-STE100" -- matches the exact prefix the pre-refactor
# hook used in every deny/auto_fix message ("STE100 gate: ..."), kept
# byte-for-byte to satisfy this refactor's own backward-compatibility bar
# (see docs/incidents/ and the hook-output diff run during migration).
RULESET_NAME = "STE100"
# No "options": unlike slopwatch/codewatch, ste100 has no tunable numeric
# thresholds today (its checks are the real ASD-STE100 standard's own
# fixed rules, not density judgments) -- "checks" (per-rule on/off) is a
# separate, real capability it does have now, see list_checks() below.
CAPABILITIES = frozenset({"terms", "word_lookup", "checks"})

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

# flag kind -> (what the check catches, what to do instead). ste100-specific:
# a different ruleset's flag kinds need their own text, not this one. See
# rulesets/slopwatch/__init__.py's CHECKS for why the two facts stay apart
# instead of being stored as one prewritten coaching sentence.
CHECKS = {
    "modal": ("Hedging modals: should, would, may, might, could",
              "must for requirements, can for real possibility; delete or "
              "state as fact for recommendations"),
    "passive": ("Passive voice with no clear actor",
                "name the actor, or restructure to active voice"),
    "ing_form": ("-ing misuse",
                 "infinitive or simple tense, unless it is one of the ~9 "
                 "whitelisted -ing nouns and adjectives"),
    "progressive": ("Progressive tense: is/are/was/were + -ing",
                    "use simple tense instead"),
    "length": ("Sentences over the context's word limit",
               "split at the clause boundary while drafting, rather than "
               "writing long and splitting after"),
    "punctuation": ("Contractions and semicolons",
                    "write contractions in full; use two sentences instead "
                    "of a semicolon"),
    "perfect_tense": ("Present perfect and present perfect passive: "
                      "has/have/had (been) + V-ed",
                      "use simple past instead"),
    "vocabulary": ("Words outside the approved dictionary: utilize, "
                   "leverage, seamlessly",
                   "use the plain approved equivalent"),
    "trailing_condition": ("A condition trailing after the command",
                           "put 'if' and 'when' clauses at the start of "
                           "the sentence"),
    "synonym_rotation": ("One concept named with rotating synonyms: "
                         "check, verify, confirm",
                         "pick one term per concept and stay with it"),
    "latin_abbrev": ("Latin abbreviations: e.g., i.e., etc., vs.",
                     "ASD-STE100 forbids them; write the plain English "
                     "equivalent"),
    "inclusive_language": ("Gendered pronouns and terms",
                           "name the actor, use 'they', or use the "
                           "standard's gender-neutral term"),
    "safety_instruction": ("A malformed WARNING/CAUTION/NOTE label "
                           "(rules 7.1-7.3)",
                           "format only: this cannot detect a MISSING "
                           "label, only a badly-formed one"),
}


def _history_path():
    return history.history_log_path(paths.find_project_root(__file__))


# What actually denies a write, in the ruleset's own words. The dashboard
# renders this beside the checks rather than leaving the single most
# consequential setting in the product unstated: the page used to say which
# checks fire and which words are known, and never what blocks.
# `text` is format()ed with this ruleset's live option values, so a tunable
# number in the sentence shows what it is right now, not its default.
DENY_POLICY = {
    "text": "Denies on every semantic flag EXCEPT unapproved vocabulary "
            "(unknown words, unapproved synonyms, words with no approved "
            "replacement). Those are reported and let through, because the "
            "dictionary cannot know a project's own domain words.",
    "always_blocking": (),
}

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


def list_term_lists(file_path=None):
    """ste100's one term list (project vocabulary), in the same shape
    slopwatch's five and codewatch's one report -- see core/terms.py.
    file_path matters here: which vocabulary packs are layered in depends
    on the routing rule matching the file, not on the ruleset."""
    return _terms.list_term_lists(RULESET_ID, TERM_LISTS,
                                   paths.find_project_root(__file__),
                                   file_path=file_path)


def add_term(list_id, term, note="", force=False):
    """Uniform contract entry point. Delegates to glossary.register, which
    adds ste100's own validation against the real ASD-STE100 dictionary --
    the one genuine difference between this ruleset's list and the others',
    now a validator callback rather than a whole parallel API."""
    if list_id != "project_terms":
        raise _terms.UnknownTermListError(
            f"unknown term list {list_id!r} -- known: ['project_terms']")
    # `force` is a bool in the uniform contract but a REASON string in
    # ste100's own register(): overriding a real prohibition has to go on
    # the record with why. A bare force=True falls back to the note.
    reason = force if isinstance(force, str) else (note or "forced via add_term") if force else None
    return glossary.register(term, note, reason, history_path=_history_path())


def remove_term(list_id, term):
    if list_id != "project_terms":
        raise _terms.UnknownTermListError(
            f"unknown term list {list_id!r} -- known: ['project_terms']")
    return glossary.unregister(term, history_path=_history_path())


def register_term(word, note="", override_unapproved=None):
    """ste100's own richer registration entry point, kept because
    override_unapproved carries a REASON string, not just a boolean -- a
    prohibition override has to go on the record with why. add_term above is
    the uniform contract wrapper over this."""
    return glossary.register(word, note, override_unapproved, history_path=_history_path())


def unregister_term(word):
    return glossary.unregister(word, history_path=_history_path())


def list_terms():
    return glossary.list_terms()


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
    """See rulesets/slopwatch/__init__.py's list_checks() -- identical
    shape and rationale, now also given to ste100's own 13 rule checks
    (previously the only ruleset of the three with no per-check toggles
    at all, the actual gap that made the three rulesets' modularity
    inconsistent with each other)."""
    project_root = paths.find_project_root(__file__)
    disabled = set(_core_config.disabled_checks(project_root, RULESET_ID))
    return {
        check_id: {"catches": CHECKS.get(check_id, ("", ""))[0],
                   "instead": CHECKS.get(check_id, ("", ""))[1],
                   "enabled": check_id not in disabled}
        for check_id in sorted(lint.ALL_CHECK_IDS)
    }


def set_enabled_checks(check_ids):
    unknown = set(check_ids) - lint.ALL_CHECK_IDS
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    disabled = sorted(lint.ALL_CHECK_IDS - set(check_ids))
    project_root = paths.find_project_root(__file__)
    _core_config.save_disabled_checks(project_root, RULESET_ID, disabled)


def set_checks_enabled(states):
    """Turn the named checks on or off, leaving every other check alone --
    {check_id: bool}. Merge semantics, the same shape set_options has, and
    the counterpart to set_enabled_checks's replace semantics: see
    core.config.merge_disabled_checks for which callers need which, and for
    the silent-mass-disable bug that made the distinction worth a second
    method rather than a comment."""
    unknown = set(states) - lint.ALL_CHECK_IDS
    if unknown:
        raise ValueError(f"unknown check id(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.ALL_CHECK_IDS)}")
    project_root = paths.find_project_root(__file__)
    _core_config.merge_disabled_checks(project_root, RULESET_ID, states)


# list_glossary_packs()/set_enabled_glossary_packs() USED to live here: two
# bare functions the ruleset registry knew nothing about, which
# dashboard.py, stopslop.py and mcp_server.py each reached for with a
# hasattr() guess. They are gone, not moved -- a pack is enabled on a PATH
# GLOB, not on a ruleset (core.config.packs_for_path / set_rule_packs), so
# there was never a ruleset method for them to be. That mismatch is exactly
# why they sat outside the contract for as long as they did.
