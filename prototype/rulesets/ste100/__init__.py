"""Contract surface for the ste100 ruleset -- the thin wrapper the core
dispatcher (pretool_hook.py, stopslop.py, mcp_server.py) actually talks to.
All real rule logic lives in lint.py; all glossary logic lives in
glossary.py. This module only assembles them into the shape
rulesets/__init__.py's registration check requires, plus the two pieces
(context defaulting, history-log wiring) that are genuinely ste100's own
policy rather than generic plumbing.
"""
from rulesets.ste100 import lint, glossary
from core import history, paths

RULESET_ID = "ste100"
# "STE100", not "ASD-STE100" -- matches the exact prefix the pre-refactor
# hook used in every deny/auto_fix message ("STE100 gate: ..."), kept
# byte-for-byte to satisfy this refactor's own backward-compatibility bar
# (see docs/incidents/ and the hook-output diff run during migration).
RULESET_NAME = "STE100"
CAPABILITIES = frozenset({"glossary", "word_lookup"})

# Relative to this package's own directory -- integrity_check.py resolves
# these against the ruleset's install location, not the repo root.
TRACKED_FILES = ["dictionary.json", "project-terms.json", "lint.py",
                  "glossary.py", "build_dictionary.py"]

# kind -> coaching prose for generate_coaching_memory.py's aggregator.
# Formerly generate_coaching_memory.py's own PRINCIPLE_TEXT; moved here
# since it's ste100-specific (a different ruleset's flag kinds need their
# own text, not this one).
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


def _history_path():
    return history.history_log_path(paths.find_project_root(__file__))


def lint_and_gate(text, *, context=None):
    """context: "procedure" (20-word limit, step-by-step instructions) or
    "description" (25-word limit, whole documents). Any other value
    (including None, the contract's default) falls back to "description" --
    ste100's own validation, per the plugin contract leaving context
    interpretation to each ruleset."""
    ctx = context if context in ("procedure", "description") else "description"
    return lint.lint_and_gate(text, context=ctx)


def blocking_semantic_flags(semantic_flags):
    return lint.blocking_semantic_flags(semantic_flags)


def apply_mechanical_fixes(text):
    return lint.apply_mechanical_fixes(text)


def register_term(word, note="", override_unapproved=None):
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
        if lw in lint.PROJECT_TERMS:
            return {"word": word, "status": "project_term",
                    "note": lint.PROJECT_TERMS[lw].get("note", "")}
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
        "project_terms": str(len(lint.PROJECT_TERMS)),
    }
