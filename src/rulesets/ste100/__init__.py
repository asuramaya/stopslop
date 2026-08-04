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
# "options" arrived late. The claim that ste100 had no tunable numbers was
# never true -- rule 5.1's sentence limits (20 words in a procedure, 25 in a
# description) were hardcoded inside check_length the whole time. See
# lint.DEFAULT_OPTIONS.
CAPABILITIES = frozenset({"terms", "word_lookup", "checks", "options"})

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
    # {excluded_vocab_types} is filled in from the LIVE option value, not
    # hardcoded prose -- excluded_vocab_types is a tunable set now, and a
    # project that narrows or widens it deserves a policy sentence that
    # still describes what the gate actually does.
    "text": "Denies on every semantic flag EXCEPT vocabulary flagged as one "
            "of: {excluded_vocab_types}. Those are reported and let "
            "through, because the dictionary cannot know a project's own "
            "domain words.",
    # Empty by design: ste100 blocks by default and names exceptions,
    # the opposite shape from slopwatch/codewatch's shared-pool-plus-
    # per-check-count. Declared anyway so every ruleset carries the same
    # key -- see rulesets/slopwatch/__init__.py's DENY_POLICY.
    "blocks_alone_at": {},
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


# Which tunable option belongs to which check. Declared, never inferred:
# see rulesets/slopwatch/__init__.py's CHECK_OPTIONS.
CHECK_OPTIONS = {
    "length": ("procedure_word_limit", "description_word_limit"),
    "vocabulary": ("excluded_vocab_types",),
}

# Options whose value is a closed set of choices rather than a free scalar.
# isinstance(value, list) alone (set_options's base type check) accepts a
# list of ANYTHING; a typo'd type name would silently stop being excluded
# with no error anywhere, one drift-goes-off-in-the-quiet-direction bug
# away from a project that thinks it widened blocking and did nothing.
# check_vocabulary is the only source of "type" values on a vocabulary
# flag's detail dict -- these three are the whole domain, not a sample.
_OPTION_CHOICES = {
    "excluded_vocab_types": {"unknown_vocabulary", "unapproved_no_replacement",
                              "unapproved_synonym"},
}


def list_options():
    current = lint._options()
    out = {}
    for name, default in lint.DEFAULT_OPTIONS.items():
        entry = {"value": current[name], "default": default}
        if name in _OPTION_CHOICES:
            entry["choices"] = sorted(_OPTION_CHOICES[name])
        out[name] = entry
    return out


def set_options(options):
    """See rulesets/slopwatch/__init__.py's set_options() -- identical
    merge-not-replace semantics and rationale."""
    unknown = set(options) - set(lint.DEFAULT_OPTIONS)
    if unknown:
        raise ValueError(f"unknown option(s): {sorted(unknown)} -- "
                          f"known: {sorted(lint.DEFAULT_OPTIONS)}")
    for key, value in options.items():
        expected = type(lint.DEFAULT_OPTIONS[key])
        if not isinstance(value, expected):
            raise ValueError(f"option {key!r} must be a {expected.__name__}, got {value!r}")
        choices = _OPTION_CHOICES.get(key)
        if choices is not None:
            bad = sorted(set(value) - choices)
            if bad:
                raise ValueError(f"option {key!r} has unknown value(s) {bad} -- "
                                  f"known: {sorted(choices)}")
    project_root = paths.find_project_root(__file__)
    merged = dict(_core_config.ruleset_options(project_root, RULESET_ID))
    merged.update(options)
    _core_config.save_ruleset_options(project_root, RULESET_ID, merged)


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
