#!/usr/bin/env python3
"""
The ASD-STE100 rule engine. Formerly prototype/ste100_lint.py -- moved here
during the pluggable-ruleset refactor so STE100 is one ruleset among
potentially several, not baked into the gate/CLI/MCP layers directly. Only
the ruleset-agnostic plumbing moved out: block/sentence tokenization
(core/blocks.py) and flag dedup (core/flags.py). Everything below is
ASD-STE100-specific rule logic; see rulesets/ste100/__init__.py for the
thin contract surface (RULESET_ID, CAPABILITIES, etc.) that wraps this
module for the core dispatcher.

Implements the pipeline: tokenize -> length check -> vocabulary scan ->
verb form scan -> modal scan -> punctuation scan.
"""

import re
import sys
import json
import os

from core.blocks import (
    tokenize_sentences, words, split_into_blocks,
    HEADER_RE as _HEADER_RE, LIST_ITEM_RE as _LIST_ITEM_RE, FENCE_RE as _FENCE_RE,
)
from core.flags import dedup_flags, default_label as _label
from core import config as _core_config, paths as _paths, terms as _terms
from core import glossary_packs

# --- Tier 1: base approved dictionary, loaded from the real ASD-STE100
# extraction (dictionary.json, built by build_dictionary.py from
# docs/ASD-STE100-dictionary-extracted.dat -- see that file's docstring
# for how the extraction was verified before being trusted as enforcement
# data).
MODAL_WORDS = {"should", "would", "may", "might", "could"}


def _load_dictionary():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dictionary.json")
    with open(path) as f:
        data = json.load(f)
    approved = set(data["approved_words"])
    unapproved_map = {}
    unapproved_no_replacement = set()
    unapproved_ambiguous = set()
    for word, info in data["unapproved_map"].items():
        if word in MODAL_WORDS:
            continue  # rule 5.3 (check_modals) owns these, not rule 1.1 vocabulary -- see below
        if info["replacement"] is None:
            unapproved_no_replacement.add(word)
        else:
            unapproved_map[word] = info["replacement"]
            if len(info["alternatives"]) > 1:
                unapproved_ambiguous.add(word)
    return approved, unapproved_map, unapproved_no_replacement, unapproved_ambiguous


APPROVED_WORDS, UNAPPROVED_MAP, UNAPPROVED_NO_REPLACEMENT, UNAPPROVED_MULTI_ALTERNATIVE = _load_dictionary()
# ALL unapproved_synonym auto-fix is disabled -- not just the words in
# UNAPPROVED_MULTI_ALTERNATIVE (kept above for reference/future use, no
# longer read by check_vocabulary or _vocab_sub below). Originally only
# multi-alternative words were held back -- "guide" -> PUT, MOVE auto-
# "fixing" to "the maintenance put" was the first sign. But a SINGLE-
# alternative entry can still be unsafe to substitute in place, found live
# while stress-testing this project's own README: "real (adj)" maps to the
# ONE alternative "AGREE (v)" -- not a synonym at all, but the verb of a
# differently-structured sentence ("the gauge shows the real quantity" ->
# "the indication AGREES WITH the quantity"). The source PDF marks the
# replacement's own part of speech for exactly this reason; this extraction
# didn't capture it, so there's no cheap way to tell a safe verb-for-verb
# swap (utilize -> use) from an unsafe adjective-for-verb one (real ->
# agree) without re-extracting that data. Confirmed live: this one word
# alone silently corrupted the just-written public README ("before they
# land on disk" -> "before they landing on disk", from a second unsafe
# single-alternative entry, "land (v)" -> "LANDING"). Until replacement POS
# is re-extracted and checked against the headword's own POS, vocabulary
# substitution is flag-only across the board -- the same "over-flag rather
# than silently ship wrong" call this project has made every other time
# this exact failure mode showed up.
UNAPPROVED_NO_AUTOFIX = set(UNAPPROVED_MAP)

# Tier 2: project glossary -- domain-specific technical vocabulary the real
# ASD-STE100 dictionary was never going to cover (an aviation-maintenance
# standard, not a software one), e.g. "repository" or "endpoint". Registered
# terms persist through core.config's generic wordlist store (stopslop.
# config.json's "wordlists" key, list_id "project_terms") -- the same
# project-root-scoped mechanism slopwatch/codewatch's own list-shaped
# checks use, not a bespoke ste100-only file anymore. See glossary.py to
# add a word; see _migrate_legacy_project_terms below for the one-time
# move off the pre-refactor location.
_LEGACY_PROJECT_TERMS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "project-terms.json")


def _migrate_legacy_project_terms(project_root):
    """One-time: fold the pre-pluggable-ruleset project-terms.json --
    stored inside this package's own directory, a leftover from when
    "the ste100 package" and "the project ste100 protects" were the same
    thing -- into stopslop.config.json's "wordlists" key at the real
    project root. Never touches anything if the new location already has
    content (an already-migrated project, or a fresh one where terms were
    registered directly against the new store) or the legacy file doesn't
    exist. Deletes the legacy file only after a successful write, so a
    crash mid-migration leaves the original data intact to retry from,
    never in a state where both copies are gone."""
    if _terms.project_terms(project_root, "ste100", "project_terms"):
        return
    if not os.path.exists(_LEGACY_PROJECT_TERMS_PATH):
        return
    try:
        with open(_LEGACY_PROJECT_TERMS_PATH) as f:
            legacy_terms = json.load(f)
    except (OSError, json.JSONDecodeError):
        return
    if not legacy_terms:
        return
    _terms.save_project_terms(project_root, "ste100", "project_terms", legacy_terms)
    try:
        os.remove(_LEGACY_PROJECT_TERMS_PATH)
    except OSError as ignored:
        pass


def _load_manual_terms():
    """Only the words a person (or an agent on their behalf) deliberately
    registered via register_term -- never pack content. glossary.py's
    list_terms()/register()/unregister() all operate on exactly this set,
    so "what's registered" stays a small, deliberate list even when a
    large vocabulary pack is enabled (see _load_project_terms below for
    the merged view check_vocabulary() actually uses)."""
    try:
        project_root = _paths.find_project_root(__file__)
    except Exception:
        return {}
    _migrate_legacy_project_terms(project_root)
    return _terms.project_terms(project_root, "ste100", "project_terms")


def _pack_admissible(term):
    """Whether a vocabulary PACK may introduce `term` into the project
    glossary. A pack may fill a coverage gap; it may never quietly cancel a
    rule the real ASD-STE100 dictionary states.

    The three packs shipped today collide with the forbidden list exactly
    zero times -- but only because each build_glossary_pack_*.py script
    hand-excludes words the dictionary already covers. That made the
    invariant a property of how those three files happened to be BUILT, not
    of the model, and it evaporates the moment a fourth pack arrives from
    anywhere else: a pack containing `utilize` would silently un-forbid a
    word the standard explicitly replaces, which is a gate that has quietly
    stopped gating. A project registration can still override a prohibition
    -- deliberately, with a stated reason, via register_term's
    override_unapproved -- because a human typing one word is an act; a bulk
    import of several hundred is not."""
    return (term not in UNAPPROVED_MAP
            and term not in UNAPPROVED_NO_REPLACEMENT
            and term not in MODAL_WORDS)


_NO_SUPPRESSION = {"approved": frozenset(), "unapproved": frozenset()}


def suppressed_vocabulary():
    """Words this project has removed from the shipped ASD-STE100 lists.

    The dictionary is 1,990 words in a git-tracked JSON file -- a project
    cannot edit it, and should not have to fork a standard to disagree with
    four entries. Removing one records a tombstone (core.terms) which these
    checks subtract, so the control the vocabulary table offers is real
    rather than decorative. Read fresh and cheaply: the mapping is empty for
    almost every project, and building the full layered view of a 787-word
    list on every gated write would not be."""
    try:
        project_root = _paths.find_project_root(__file__)
        return {
            "approved": _terms.suppressed_terms(project_root, "ste100", "approved_words"),
            "unapproved": _terms.suppressed_terms(project_root, "ste100", "unapproved_words"),
        }
    except Exception as ignored:
        return _NO_SUPPRESSION


def effective_project_terms(file_path=None):
    """The full Tier 2 glossary the checks actually run against for one
    file: the manual registrations, plus whatever packs the routing rule
    matching `file_path` turns on. Packs are resolved PER PATH -- NIST
    security vocabulary belongs to docs/security/, not to "the ste100
    ruleset" -- see core.config.packs_for_path.

    Any failure (unresolvable project root, unreadable pack file) yields
    the manual terms alone rather than raising: packs are a convenience
    layer on top of a working gate, never a reason to break it, the same
    principle history.log_event's own OSError handling uses."""
    try:
        project_root = _paths.find_project_root(__file__)
        return _terms.effective_terms(TERM_LISTS["project_terms"], project_root,
                                       "ste100", "project_terms", file_path=file_path)
    except Exception as ignored:
        return _load_manual_terms()


# The manual layer only -- deliberately NOT including packs. Pack content
# depends on which file is being written, so there is no single correct
# import-time answer; lint_and_gate/apply_mechanical_fixes resolve the real
# set per call via effective_project_terms(). This global remains as the
# strictest sensible default for a direct check_vocabulary()/check_ing()
# call that names no file.
PROJECT_TERMS = _load_manual_terms()

# would/may/might/could default replacements for check_modals' non-heuristic
# fallback path -- deliberately NOT in UNAPPROVED_MAP, unlike the old
# hand-curated stand-in and an earlier version of this dictionary load, both
# of which put them there. That was a real bug, found live while verifying
# this change: check_vocabulary's word-level scan has no notion of the
# semi-modal collocation check_modals guards against ("may need to" must NOT
# blindly become "can need to"), so it auto-fixed "may" on sight regardless
# of context. "the operator may need to stop the test" came out as "the
# operator can necessary to stop the test" -- check_modals correctly flagged
# the same word as a non-auto-fixable collocation in the same call, but
# check_vocabulary's independent, uncoordinated substitution won anyway.
# Keeping these out of UNAPPROVED_MAP means check_vocabulary never touches
# them at all; check_modals is the only path that acts on modal words.
# "should" needs no entry here: rule 10.6 flags it unconditionally and never
# auto-fixes it, so check_modals never reaches this fallback for it.
MODAL_DEFAULT_REPLACEMENTS = {
    "would": "will", "may": "can", "might": "can", "could": "can",
}

# Corporate jargon the real ASD-STE100 dictionary doesn't itemize (it isn't
# real aviation/technical vocabulary) but is still worth catching.
UNAPPROVED_MAP.update({
    "leverage": "use", "seamlessly": "", "robustly": "", "effectively": "",
})

# Declared here, not beside the other lists above, because UNAPPROVED_MAP is
# still being extended at this point -- a term list built from it any earlier
# would silently miss the corporate-jargon entries added just above.
TERM_LISTS = {
    "approved_words": {
        "content_kind": "word",
        # Which CHECK this list feeds. Declared, not inferred from the
        # id: ste100's three lists all feed one check, so any UI that
        # paired them by name would show that check as having no
        # vocabulary at all. A list naming its check is fine (both are
        # internal to this ruleset); a PACK naming its consumer was not,
        # because a pack is shared content -- see core/glossary_packs.
        "feeds": "vocabulary",
        "label": "Approved vocabulary",
        "description": "The real ASD-STE100 dictionary's approved words. A word "
                        "here is never flagged as unknown or unapproved.",
        "polarity": "allow",
        "accepts_packs": False,
                # The published ASD-STE100 dictionary. A project cannot ADD to
        # it -- "the standard also approves X" is not this project's
        # claim to make, and project_terms exists to say it locally.
        # Removal stays open: refusing a dictionary word here is real
        # curation, recorded as a tombstone (see core/terms.py).
        "accepts_additions": False,
        "built_ins": APPROVED_WORDS,
    },
    "unapproved_words": {
        "content_kind": "word",
        "feeds": "vocabulary",
        "label": "Forbidden vocabulary",
        "description": "Words the real ASD-STE100 dictionary forbids, most with "
                        "an approved replacement.",
        "polarity": "deny",
        "accepts_packs": False,
                # The published ASD-STE100 dictionary. A project cannot ADD to
        # it -- "the standard also approves X" is not this project's
        # claim to make, and project_terms exists to say it locally.
        # Removal stays open: refusing a dictionary word here is real
        # curation, recorded as a tombstone (see core/terms.py).
        "accepts_additions": False,
        "built_ins": dict(
            {w: {"note": f"use \u201c{r}\u201d instead"} for w, r in UNAPPROVED_MAP.items() if r},
            **{w: {"note": "no replacement given"} for w in UNAPPROVED_MAP if not UNAPPROVED_MAP[w]},
            **{w: {"note": "no replacement given"} for w in UNAPPROVED_NO_REPLACEMENT},
        ),
    },
    "project_terms": {
        "content_kind": "word",
        "feeds": "vocabulary",
        "label": "Project vocabulary",
        "description": "Domain words the real ASD-STE100 dictionary was never "
                        "going to cover (it is an aviation-maintenance standard, "
                        "not a software one) that this project permits anyway.",
        "polarity": "allow",
        "accepts_packs": True,
        "built_ins": (),   # nothing ships pre-registered; the 787-word approved
                            # dictionary is the STANDARD this list exempts from,
                            # not a built-in layer of the list itself
        "pack_admissible": _pack_admissible,
    },
}



# Real ASD-STE100 rule 3.5 whitelist (docs/ASD-STE100-rules-extracted.md):
# nouns (lighting, opening, routing, servicing), adjectives (mating, missing,
# remaining), pronoun (something), preposition (during). The earlier list here
# was a placeholder guess made before the real spec was extracted -- wrong.
ING_NOUN_EXCEPTIONS = {"lighting", "opening", "routing", "servicing",
                        "mating", "missing", "remaining", "something", "during"}

# Separate from ASD-STE100 itself -- a deliberately small, closed list of
# ordinary English words that happen to end in "-ing" but have no plausible
# verb-derived (gerund/present-participle) reading in normal usage at all, so
# rule 3.5 (which targets verb-derived -ing misuse) cannot actually apply to
# them. Found live: "The meeting starts in the morning. Check the wing and
# the ceiling before flight." denied the write over "morning"/"wing"/
# "ceiling" -- none of them a verb form of anything, just ordinary nouns the
# aviation-scoped dictionary never had a reason to list. check_vocabulary
# already resolves inflected forms of REAL verbs via _dictionary_base_form;
# check_ing has no equivalent, and adding one on the same "does a base form
# exist in the dictionary" basis was tried and rejected here -- it would
# also silently un-flag genuine software-domain gerund misuse the dictionary
# was never going to cover either (configuring, deploying, validating have
# no dictionary entry, so "is configuring" would stop flagging too, exactly
# the kind of violation this check exists to catch). A short, explicit,
# human-reviewed list is the safer trade: it can only ever suppress a flag
# on the exact words listed, never on a whole class of unknown words.
# Deliberately excludes anything with a real, plausible verb-derived reading
# in technical prose (building, meeting, feeling) -- those stay flagged,
# same "over-flag when genuinely ambiguous" call this module makes
# everywhere else.
ING_NEVER_VERBAL = {"thing", "nothing", "anything", "everything",
                     "morning", "evening", "ceiling", "king", "ring",
                     "wing", "spring", "string"}

# Irregular past-participle -> simple-past mapping, for perfect-tense
# detection/fix. Needed because "has given", "has written", "has gone" don't
# end in "-ed" and were silently invisible to the plain \w+ed regex -- this
# table is what actually closes that gap. Not exhaustive (English has ~200+
# irregular verbs); covers the common ones likely in technical writing.
IRREGULAR_PARTICIPLES = {
    "given": "gave", "written": "wrote", "taken": "took", "done": "did",
    "gone": "went", "seen": "saw", "known": "knew", "grown": "grew",
    "shown": "showed", "begun": "began", "broken": "broke", "chosen": "chose",
    "spoken": "spoke", "driven": "drove", "risen": "rose", "fallen": "fell",
    "forgotten": "forgot", "frozen": "froze", "hidden": "hid", "ridden": "rode",
    "stolen": "stole", "woken": "woke", "torn": "tore", "worn": "wore",
    "sworn": "swore", "thrown": "threw", "flown": "flew", "drawn": "drew",
    "blown": "blew", "eaten": "ate", "become": "became", "come": "came",
    "run": "ran", "held": "held", "left": "left", "kept": "kept",
    "meant": "meant", "found": "found", "sent": "sent", "spent": "spent",
    "built": "built", "made": "made", "paid": "paid", "said": "said",
    "sold": "sold", "told": "told", "thought": "thought", "brought": "brought",
    "bought": "bought", "caught": "caught", "taught": "taught",
    "fought": "fought", "sought": "sought", "understood": "understood",
    "stood": "stood", "won": "won", "sat": "sat", "met": "met", "read": "read",
    "set": "set", "put": "put", "cut": "cut", "shut": "shut", "hit": "hit",
    "let": "let", "cost": "cost", "hurt": "hurt", "split": "split",
    "spread": "spread", "burst": "burst", "sung": "sang", "swum": "swam",
    "rung": "rang", "drunk": "drank", "sunk": "sank", "shrunk": "shrank",
    "slept": "slept", "wept": "wept", "lost": "lost", "led": "led",
    "bent": "bent", "lent": "lent", "bled": "bled", "fed": "fed",
    "fled": "fled", "bred": "bred", "dealt": "dealt", "felt": "felt",
    "knelt": "knelt", "smelt": "smelt", "spelt": "spelt", "spilt": "spilt",
    "burnt": "burnt", "learnt": "learnt", "dreamt": "dreamt",
}

# Contraction expansions (rule 4.2). Only a closed set -- an apostrophe-word
# NOT in this set is treated as a possessive (GR-8 explicitly permits the
# Saxon genitive), not a contraction. Matters for auto-fix: blindly expanding
# every \w+'\w+ match would corrupt legitimate possessives like "system's".
CONTRACTION_EXPANSIONS = {
    "don't": "do not", "doesn't": "does not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "can't": "cannot", "won't": "will not", "shouldn't": "should not",
    "wouldn't": "would not", "couldn't": "could not", "didn't": "did not",
    "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
    "mustn't": "must not", "i'm": "I am", "i've": "I have", "i'll": "I will",
    "i'd": "I would", "you're": "you are", "you've": "you have",
    "you'll": "you will", "you'd": "you would", "we're": "we are",
    "we've": "we have", "we'll": "we will", "we'd": "we would",
    "they're": "they are", "they've": "they have", "they'll": "they will",
    "they'd": "they would", "it's": "it is", "that's": "that is",
    "there's": "there is", "here's": "here is", "what's": "what is",
    "who's": "who is", "let's": "let us", "she's": "she is", "he's": "he is",
}


# The two numbers ASD-STE100 rule 5.1 fixes, exposed as options like every
# other ruleset's thresholds. They were hardcoded inside check_length, which
# left ste100 the only ruleset declaring no "options" capability at all --
# an asymmetry with no reason behind it, and one the folded Configure page
# made visible: em_dash_cluster showed a tunable number and `length` showed
# none, side by side, as though one check were more configurable in kind.
#
# The defaults ARE the standard. A project lowering them is tightening its
# own house style; raising them is departing from ASD-STE100 knowingly,
# which is a choice the tool should let a project make and record in its
# config, not one it should silently prevent.
DEFAULT_OPTIONS = {
    "procedure_word_limit": 20,
    "description_word_limit": 25,
    # Which vocabulary "type"s (see check_vocabulary's "type" field --
    # unknown_vocabulary/unapproved_no_replacement/unapproved_synonym are
    # the only three that ever occur) are reported but never block a
    # write. See blocking_semantic_flags below for why this exists at all;
    # this used to be a fixed module constant (EXCLUDED_VOCAB_TYPES) --
    # a project narrowing or widening the staged set had no way to say so.
    "excluded_vocab_types": ["unknown_vocabulary", "unapproved_no_replacement",
                              "unapproved_synonym"],
}


def _options():
    """DEFAULT_OPTIONS with any valid override from stopslop.config.json's
    "options" key layered on top. Same never-break-the-gate posture as
    slopwatch's: a bad type or an unresolvable project root falls back to
    the default rather than raising inside a live gate call."""
    opts = dict(DEFAULT_OPTIONS)
    try:
        project_root = _paths.find_project_root(__file__)
        overrides = _core_config.ruleset_options(project_root, "ste100")
    except Exception as unresolvable:  # no project on disk: use the standard
        del unresolvable
        return opts
    for key, value in overrides.items():
        if key in opts and isinstance(value, type(opts[key])):
            opts[key] = value
    return opts


def check_length(sentence, context="procedure"):
    opts = _options()
    limit = (opts["description_word_limit"] if context == "description"
             else opts["procedure_word_limit"])
    n = len(sentence.split())
    if n > limit:
        return {"rule": "5.1", "word_count": n, "limit": limit}
    return None


# The real dictionary lists verb/noun HEADWORDS only (base/infinitive form:
# "BE", "HAVE", "CHECK", "GUIDE"), so any inflected form -- is/are/was,
# checks/checked, guides -- fails to exact-match its own approved or
# unapproved headword at all. Confirmed live, measuring against this
# project's own real prose: "is", "are", "was", "has", "did", "utilizes",
# "checks" all showed as unknown_vocabulary even though "be"/"have"/"do"/
# "utilize"/"check" are themselves already dictionary entries. This
# resolver only ever answers "does this word's base form appear in the
# dictionary" for the LOOKUP -- it is never used for auto-fix (getting a
# replacement's own conjugation right is a separate, harder problem, out of
# scope here; a conjugated unapproved word is flagged, not silently
# rewritten -- see the auto_fix: False below).
IRREGULAR_BASE_FORMS = {
    "is": "be", "are": "be", "was": "be", "were": "be", "been": "be",
    "am": "be", "being": "be",
    "does": "do", "did": "do", "done": "do", "doing": "do",
    "has": "have", "had": "have", "having": "have",
    "goes": "go", "went": "go", "gone": "go", "going": "go",
}


def _regular_base_candidates(word):
    """Ordered, conservative candidate base forms for a regular inflection
    (verb conjugation or noun plural -- the dictionary's singular/base-form
    listing convention makes both the same problem here). A wrong candidate
    that coincidentally matches a real dictionary word is a rare, safe-
    direction false negative on unknown_vocabulary (this function is never
    consulted by the fixer), not a false auto-fix."""
    candidates = []
    if word.endswith("ies") and len(word) > 4:
        candidates.append(word[:-3] + "y")            # tries -> try
    if word.endswith("es") and len(word) > 3:
        candidates.append(word[:-2])                   # watches -> watch
    if word.endswith("s") and len(word) > 2:
        candidates.append(word[:-1])                    # checks -> check
    if word.endswith("ied") and len(word) > 4:
        candidates.append(word[:-3] + "y")             # tried -> try
    if word.endswith("ed") and len(word) > 3:
        stem = word[:-2]
        candidates.append(stem)                         # checked -> check
        candidates.append(stem + "e")                   # used -> use
        if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            candidates.append(stem[:-1])                 # stopped -> stop
    return candidates


def _dictionary_base_form(lw):
    """First candidate base form found in either the approved or unapproved
    dictionary, or None if nothing resolves."""
    irregular = IRREGULAR_BASE_FORMS.get(lw)
    if irregular and (irregular in APPROVED_WORDS or irregular in UNAPPROVED_MAP
                       or irregular in UNAPPROVED_NO_REPLACEMENT):
        return irregular
    for cand in _regular_base_candidates(lw):
        if cand in APPROVED_WORDS or cand in UNAPPROVED_MAP or cand in UNAPPROVED_NO_REPLACEMENT:
            return cand
    return None


def check_vocabulary(sentence, project_terms=None, suppressed=None):
    _pt = PROJECT_TERMS if project_terms is None else project_terms
    _sup = suppressed or _NO_SUPPRESSION
    violations = []
    for w in words(sentence):
        lw = w.lower().strip("'")
        # MODAL_WORDS are deliberately absent from UNAPPROVED_MAP (see the
        # comment above MODAL_DEFAULT_REPLACEMENTS) so check_modals is the
        # only path that acts on them. Without this check they fell through
        # to unknown_vocabulary below and double-reported every should/
        # would/may/could/might under kind:vocabulary too, alongside the
        # real kind:modal flag check_modals already produces for the same
        # word -- harmless for the gate decision (unknown_vocabulary is
        # excluded from denial either way) but noisy everywhere the raw
        # flag list gets read: --all output, coaching-memory aggregation.
        if not lw or lw in _pt or lw in MODAL_WORDS:
            continue
        if lw in APPROVED_WORDS and lw not in _sup["approved"]:
            continue
        if lw in _sup["unapproved"]:
            continue
        if lw in UNAPPROVED_MAP:
            violations.append({
                "word": w, "rule": "1.1", "type": "unapproved_synonym",
                "replacement": UNAPPROVED_MAP[lw],
                "auto_fix": False,  # see module-level note above UNAPPROVED_MAP's
                                     # construction: even single-alternative entries
                                     # aren't safe to blindly substitute.
            })
        elif lw in UNAPPROVED_NO_REPLACEMENT:
            # Real dictionary explicitly forbids the word but gives no
            # substitute (source says "NONE") -- distinct from
            # unknown_vocabulary below: this isn't a dictionary-coverage gap,
            # it's a known rule with no safe auto-fix target. Currently held
            # out of gate denial anyway (see blocking_semantic_flags below)
            # alongside unknown_vocabulary, pending a PROJECT_TERMS glossary
            # and a real registration flow -- see project memory for why.
            violations.append({
                "word": w, "rule": "1.1", "type": "unapproved_no_replacement",
                "replacement": None, "auto_fix": False,
            })
        else:
            base = _dictionary_base_form(lw)
            if base is not None and base in APPROVED_WORDS:
                continue  # inflected form of an approved word -- e.g. "checks" -> "check"
            elif base is not None:
                violations.append({
                    "word": w, "rule": "1.1", "type": "unapproved_synonym",
                    "replacement": UNAPPROVED_MAP.get(base), "auto_fix": False,
                    "note": f"inflected form of unapproved '{base}' -- flagged, not "
                            f"auto-fixed (this fixer doesn't attempt to conjugate "
                            f"a replacement to match)",
                })
            else:
                violations.append({
                    "word": w, "rule": "1.5", "type": "unknown_vocabulary",
                    "replacement": None, "auto_fix": False,
                })
    return violations


def check_ing(sentence, project_terms=None, suppressed=None):
    # Deliberately does NOT try to auto-exempt "-ing NOUN" compounds
    # (monitoring alerts, troubleshooting section) even though rule 3.5
    # permits them -- tried that heuristic and it silently exempted genuine
    # misuse too ("initiating failover" reads identically to "monitoring
    # alerts" at the regex level: ING + NOUN, no way to tell gerund-object
    # from noun-modifier without real parsing). A false positive here costs
    # a cheap human/model glance; a false negative ships a real violation
    # silently. For a gate, over-flag and let it be reviewed.
    _pt = PROJECT_TERMS if project_terms is None else project_terms
    _sup = suppressed or _NO_SUPPRESSION
    hits = []
    for m in re.finditer(r"\b(\w+ing)\b", sentence, re.IGNORECASE):
        w = m.group(1).lower()
        if w in ING_NOUN_EXCEPTIONS or w in ING_NEVER_VERBAL:
            continue
        # If the word is independently approved in the general dictionary
        # (rule 1.1/1.5) -- e.g. "warning" as its own noun entry -- it
        # doesn't need separate rule-3.5 clearance. Rule 3.5 restricts
        # improperly verb-derived -ing forms; it isn't meant to re-ban
        # every dictionary noun that happens to end in those letters.
        # Different from the reverted noun-modifier heuristic (which
        # guessed from syntactic context and got it wrong on "initiating
        # failover") -- this is a direct dictionary lookup on the word
        # itself, not a guess about what follows it.
        if (w in APPROVED_WORDS and w not in _sup["approved"]) or w in _pt:
            continue
        hits.append({"word": m.group(1), "rule": "3.5", "auto_fix": None,
                      "note": "not in the closed whitelist -- flagged even "
                              "though some hits will be legitimate technical-"
                              "noun compounds (e.g. 'monitoring alerts'); "
                              "over-flagging is the safer failure mode here"})
    return hits


def check_perfect(sentence):
    # Three branches: "have/has/had been" (perfect-passive, arbitrary word
    # after "been"), "has/have/had + V-ed" (regular participle), and
    # "has/have/had + [irregular participle]" via IRREGULAR_PARTICIPLES.
    # The third branch is what closes the gap: without it, "has given",
    # "has written", "has gone" don't match \w+ed at all and were silently
    # invisible. Words after has/have/had that are neither -ed nor in the
    # irregular table (e.g. "has three components") are correctly ignored --
    # not every word following these auxiliaries is a participle.
    #
    # For the "been" branch, approximate number agreement: have->were,
    # has/had->was. Imperfect (plural "had been" should stay "were"), but
    # closer than leaving "been" in the text.
    been_aux_to_replacement = {"has": "was", "have": "were", "had": "was"}
    hits = [{"phrase": f"{a} been", "rule": "3.4", "auto_fix": True,
             "replacement_prefix": been_aux_to_replacement[a.lower()]}
            for a in re.findall(r"\b(has|have|had)\s+been\b", sentence, re.IGNORECASE)]
    for m in re.finditer(r"\b(has|have|had)\s+(?!been\b)(\w+)\b", sentence, re.IGNORECASE):
        aux, participle = m.group(1), m.group(2)
        lp = participle.lower()
        if lp.endswith("ed"):
            hits.append({"phrase": f"{aux} {participle}", "rule": "3.4",
                        "auto_fix": True, "replacement_prefix": "", "replacement": participle})
        elif lp in IRREGULAR_PARTICIPLES:
            hits.append({"phrase": f"{aux} {participle}", "rule": "3.4",
                        "auto_fix": True, "replacement_prefix": "",
                        "replacement": IRREGULAR_PARTICIPLES[lp]})
    return hits


# Direct -ing-form -> simple-past mapping, for past-progressive auto-fix
# ("was running" -> "ran"). Deliberately NOT a base-verb table + orthographic
# rules (undoubling consonants, restoring dropped "e") -- that reversal is
# error-prone without a real lexicon, so this maps the whole -ing form
# directly instead. Only covers past progressive ("was/were" + V-ing):
# simple past is the same form regardless of subject person/number, so no
# subject-verb agreement problem. Present progressive ("is/are" + V-ing)
# has NO safe fix here -- "is running" needs 3rd-person-singular agreement
# ("runs") that isn't reliably determinable from regex alone, and guessing
# wrong would repeat the exact mistake the -ing noun-modifier heuristic
# already taught this session to avoid. Present progressive stays flag-only.
PROGRESSIVE_ING_TO_PAST = {
    "running": "ran", "going": "went", "writing": "wrote", "reading": "read",
    "sending": "sent", "receiving": "received", "throwing": "threw",
    "catching": "caught", "building": "built", "checking": "checked",
    "trying": "tried", "waiting": "waited", "starting": "started",
    "stopping": "stopped", "failing": "failed", "loading": "loaded",
    "processing": "processed", "connecting": "connected", "closing": "closed",
    "opening": "opened", "testing": "tested", "deploying": "deployed",
    "restarting": "restarted", "updating": "updated", "installing": "installed",
    "configuring": "configured", "syncing": "synced", "retrying": "retried",
    "logging": "logged", "monitoring": "monitored", "queuing": "queued",
    "scaling": "scaled", "restoring": "restored", "validating": "validated",
    "verifying": "verified", "creating": "created", "deleting": "deleted",
    "uploading": "uploaded", "downloading": "downloaded", "compiling": "compiled",
    "executing": "executed", "returning": "returned", "handling": "handled",
    "blocking": "blocked", "polling": "polled", "timing": "timed",
    "backing": "backed", "working": "worked", "saving": "saved",
}


def check_progressive(sentence):
    hits = []
    for a, b in re.findall(r"\b(is|are|was|were)\s+(\w+ing)\b", sentence, re.IGNORECASE):
        lb = b.lower()
        if a.lower() in ("was", "were") and lb in PROGRESSIVE_ING_TO_PAST:
            hits.append({"phrase": f"{a} {b}", "rule": "3.2", "auto_fix": True,
                        "replacement": PROGRESSIVE_ING_TO_PAST[lb]})
        else:
            hits.append({"phrase": f"{a} {b}", "rule": "3.2", "auto_fix": False,
                        "note": "present progressive needs subject-verb agreement "
                                "not reliably determinable from regex, or the verb "
                                "isn't in the past-progressive fix table -- flagged, "
                                "not guessed"})
    return hits


def check_passive(sentence):
    return [{"phrase": f"{a} {b}", "rule": "3.6", "auto_fix": False,
              "note": "agent-unknown passive -- requires semantic flag per doc 5.3/10"}
            for a, b in re.findall(r"\b(is|are|was|were|be|been|being)\s+(\w+ed)\b", sentence, re.IGNORECASE)]


SEMI_MODAL_COLLOCATION = re.compile(
    r"\b(would|may|might|could)\s+(need|want|have|wish|like)\s+to\b", re.IGNORECASE)


def _modal_resolution(modal, is_collocation, has_if, has_warning):
    """Single source of truth for how one should/would/may/might/could
    occurrence resolves -- used by BOTH check_modals (detection) and
    fix_sentence (the actual auto-fix), so the two can't silently diverge
    the way they did before this was factored out. Returns (auto_fix,
    replacement, rule, note_or_basis)."""
    if modal == "should":
        return False, None, "10.6", "critical severity -- always flagged, never auto-fixed"
    if is_collocation:
        return False, None, "5.3/13.3", (
            "semi-modal collocation (e.g. 'may need to') -- Table 7's "
            "'All contexts' blind replacement is ungrammatical here "
            "('can need to'); requires semantic rewrite, not substitution")
    if has_if:
        return True, "can", "5.3", "if-clause heuristic (doc 5.3)"
    if has_warning:
        return True, "must", "5.3", "warning/caution heuristic (doc 5.3)"
    return True, MODAL_DEFAULT_REPLACEMENTS.get(modal), "5.3", "table 7 default (no heuristic matched)"


def check_modals(sentence):
    hits = []
    has_if = bool(re.search(r"\bif\b", sentence, re.IGNORECASE))
    has_warning = bool(re.search(r"\b(warning|caution)\b", sentence, re.IGNORECASE))
    collocation_spans = {m.start(1) for m in SEMI_MODAL_COLLOCATION.finditer(sentence)}
    for m in re.finditer(r"\b(should|would|may|might|could)\b", sentence, re.IGNORECASE):
        modal = m.group(1).lower()
        auto_fix, replacement, rule, note = _modal_resolution(
            modal, m.start() in collocation_spans, has_if, has_warning)
        hit = {"modal": modal, "rule": rule, "auto_fix": auto_fix}
        if auto_fix:
            hit["replacement"] = replacement
            hit["basis"] = note
        else:
            hit["note"] = note
        hits.append(hit)
    return hits


def check_punctuation(sentence):
    out = []
    if ";" in sentence:
        out.append({"rule": "8.1", "type": "semicolon", "auto_fix": True})
    for c in re.findall(r"\b\w+'\w+\b", sentence):
        if c.lower() in CONTRACTION_EXPANSIONS:
            out.append({"rule": "8.2", "type": "contraction", "word": c,
                        "replacement": CONTRACTION_EXPANSIONS[c.lower()], "auto_fix": True})
        # else: likely a possessive (GR-8 permits it) -- not flagged at all
    return out


# GR-6: Latin abbreviations. Closed, finite word list -- rated fully
# deterministic (a) in the real spec extraction. "etc." maps to "and more"
# rather than blind deletion, since deleting it outright can leave a
# dangling comma ("...things, etc." -> "...things,"); GR-6 itself names
# "and more" as one of its two suggested alternatives.
LATIN_ABBREV_MAP = {
    "e.g.": "for example", "i.e.": "that is", "etc.": "and more",
    "et al.": "and others", "vs.": "versus", "cf.": "compare",
    "n.b.": "note", "viz.": "namely",
}
_LATIN_PATTERN = "|".join(re.escape(k) for k in sorted(LATIN_ABBREV_MAP, key=len, reverse=True))
LATIN_ABBREV_RE = re.compile(r"\b(" + _LATIN_PATTERN + r")", re.IGNORECASE)


def check_latin_abbrev(sentence):
    hits = []
    for m in LATIN_ABBREV_RE.finditer(sentence):
        key = m.group(1).lower()
        hits.append({"rule": "GR-6", "word": m.group(1),
                     "replacement": LATIN_ABBREV_MAP[key], "auto_fix": True})
    return hits


# GR-7: inclusive language (new in Issue 9). Gendered pronouns are not
# permitted at all -- flag every occurrence, no exception. "man"/"woman" are
# not permitted UNLESS necessary in context (e.g. medical text) -- that
# exception is a genuine judgment call no regex can make, so these are
# always flagged for review rather than either auto-fixed or silently
# allowed. Flag-only per design choice: picking "they" vs. naming the actor
# needs sentence-level judgment the rule itself doesn't resolve.
GENDERED_PRONOUNS = {"he", "him", "his", "she", "her", "hers", "himself", "herself"}
GENDERED_TERMS = {"man", "woman", "men", "women"}


def check_inclusive_language(sentence):
    hits = []
    for w in words(sentence):
        lw = w.lower()
        if lw in GENDERED_PRONOUNS:
            hits.append({"rule": "GR-7", "word": w, "type": "pronoun", "auto_fix": False,
                        "note": "gendered pronouns are not permitted in STE at all -- "
                                "name the actor, or use 'they'"})
        elif lw in GENDERED_TERMS:
            hits.append({"rule": "GR-7", "word": w, "type": "term", "auto_fix": False,
                        "note": "not permitted unless necessary in context (e.g. medical "
                                "text) -- judgment call, always flagged for review"})
    return hits


# Ported from SimpleEnglish's evals/ste_lint.py (MIT) --
# https://github.com/AminBlg/SimpleEnglish, see NOTICE -- condition-
# before-command (rules 5.4/7.2): the "if"/"when" clause should open the
# sentence, not trail after the command. Requires restructuring (move the
# clause), not a substitution, so this is a semantic flag, not auto-fixable.
TRAILING_COND = re.compile(r"\w[^.!?\n]{3,}\s\b(if|when)\b\s", re.IGNORECASE)


def check_trailing_condition(sentence):
    if TRAILING_COND.search(sentence) and not re.match(r"^(if|when)\b", sentence, re.IGNORECASE):
        return {"rule": "5.4", "auto_fix": False,
                "note": "condition should open the sentence, not trail after the command"}
    return None


# Ported from SimpleEnglish's evals/ste_lint.py (MIT) --
# https://github.com/AminBlg/SimpleEnglish, see NOTICE -- one term per
# concept (rules 1.11/9.4), document-level: flags when 2+ members of the
# same rotation set appear anywhere in the text. Which term to standardize
# on is a judgment call (semantic, not auto-fixable) -- same category as glossary
# registration.
ROTATION_SETS = [
    ("check-verify", re.compile(r"\b(check|verify|confirm|validate|ensure)\w*\b", re.IGNORECASE)),
    ("config-settings", re.compile(r"\b(config|configuration|settings|options)\b", re.IGNORECASE)),
    ("delete-remove", re.compile(r"\b(delete|remove|drop|destroy)\w*\b", re.IGNORECASE)),
    ("run-execute", re.compile(r"\b(run|execute|invoke|launch)\w*\b", re.IGNORECASE)),
    ("show-display", re.compile(r"\b(show|display|render|present)\w*\b", re.IGNORECASE)),
]


def check_synonym_rotation(full_text):
    hits = []
    for set_name, rx in ROTATION_SETS:
        stems = {m.group(1).lower().rstrip("s") for m in rx.finditer(full_text)}
        if len(stems) > 1:
            hits.append({"rule": "1.11", "set": set_name, "terms_used": sorted(stems),
                         "auto_fix": False,
                         "note": "pick one term for this concept and use it throughout"})
    return hits


# Safety instructions, rule 7 (rules 7.1-7.3). FORMAT-ONLY by design
# choice: this checks that a block ALREADY carrying a recognized risk-level
# label is well-formed. It does NOT try to detect where a label is MISSING
# from text that should have had one -- "does this paragraph describe a
# real hazard" isn't mechanically checkable (same limit the real spec's own
# text admits for rule 7.1: a linter can verify a label exists and is
# well-formed, never that the correct severity was chosen). Operates on
# whole blocks (paragraph/list_item), not single sentences, since the
# command-first and consequence-stated requirements span the block.
SAFETY_LABEL_RE = re.compile(r"^\**(WARNING|CAUTION|DANGER|NOTICE|ATTENTION)\**\s*:?\s*", re.IGNORECASE)
_CONSEQUENCE_RE = re.compile(
    r"\b(can|will|may)\s+\w*\s*(cause|result|occur|damage|injure|injury|death)\b|"
    r"\b(causes?|results?\s+in|leads?\s+to)\b", re.IGNORECASE)
_IMPERATIVE_OR_CONDITION_START = re.compile(r"^(if|when|do not|don't|\w+)\b", re.IGNORECASE)


def check_safety_instruction(block_text):
    m = SAFETY_LABEL_RE.match(block_text.strip())
    if not m:
        return []
    label = m.group(1).upper()
    body = block_text.strip()[m.end():].strip()
    hits = []
    if not body:
        hits.append({"rule": "7.2", "label": label, "auto_fix": False,
                    "note": "safety label has no instruction text after it"})
        return hits
    # 7.2: command or condition first. Heuristic: the body's first word
    # should be an imperative verb or "if"/"when"/"do not" -- this is a
    # weak check (any first word matches \w+), so it only catches the
    # clearly-wrong case of starting mid-explanation with a lowercase
    # conjunction like "but"/"and"/"so" or a passive-voice opener.
    first_word = body.split()[0].lower().strip(".,;:")
    if first_word in ("but", "and", "so", "however", "this", "it", "there"):
        hits.append({"rule": "7.2", "label": label, "auto_fix": False,
                    "note": f"starts with '{first_word}' -- should open with a "
                            "direct command or a fronted if/when condition, "
                            "not an explanation"})
    # 7.3: must state a consequence somewhere in the block.
    if not _CONSEQUENCE_RE.search(body):
        hits.append({"rule": "7.3", "label": label, "auto_fix": False,
                    "note": "no stated consequence found -- a safety instruction "
                            "must say what happens if the reader doesn't obey, "
                            "never a bare command"})
    return hits


# Every "kind" string this ruleset's checks can produce -- the modularity
# surface rulesets/ste100/__init__.py's list_checks()/set_enabled_checks()
# expose, same shape slopwatch/codewatch already have. Previously ste100
# had no per-check toggles at all (the per-check-toggle work only ever
# touched the other two rulesets) -- the real gap that made the three
# rulesets' configurability inconsistent with each other.
ALL_CHECK_IDS = frozenset({
    "safety_instruction", "length", "vocabulary", "ing_form", "perfect_tense",
    "progressive", "passive", "modal", "punctuation", "trailing_condition",
    "latin_abbrev", "inclusive_language", "synonym_rotation",
})


def _enabled_check_ids(file_path=None):
    """Same never-cache-it, read-fresh-every-call shape as slopwatch's/
    codewatch's own _enabled_check_ids()."""
    try:
        project_root = _paths.find_project_root(__file__)
        disabled = set(_core_config.disabled_checks_for_path(
            project_root, "ste100", file_path))
    except Exception:
        return set(ALL_CHECK_IDS)
    return ALL_CHECK_IDS - disabled


def lint_sentence(sentence, context="procedure", project_terms=None, suppressed=None):
    return {
        "text": sentence,
        "length": check_length(sentence, context),
        "vocabulary": check_vocabulary(sentence, project_terms, suppressed),
        "ing_forms": check_ing(sentence, project_terms, suppressed),
        "perfect_tense": check_perfect(sentence),
        "progressive": check_progressive(sentence),
        "passive": check_passive(sentence),
        "modals": check_modals(sentence),
        "punctuation": check_punctuation(sentence),
        "trailing_condition": check_trailing_condition(sentence),
        "latin_abbrev": check_latin_abbrev(sentence),
        "inclusive_language": check_inclusive_language(sentence),
    }


# Kinds deliberately excluded from dedup: each occurrence is independently
# actionable regardless of how many times the same RULE fires elsewhere.
# "length" and "trailing_condition" have no word/phrase key at all (every
# hit shares the same rule ID), so without this exclusion dedup would
# silently collapse every distinct over-length or badly-ordered sentence in
# a document into one reported flag -- losing exactly the information
# needed to actually go fix each one. "synonym_rotation" is already
# document-level (one flag per rotation-set, not per occurrence).
# "safety_instruction"'s label is the severity WORD (WARNING/CAUTION/...),
# a category many distinct blocks share -- two unrelated malformed WARNING
# blocks in the same document would otherwise collapse into one flag.
_DEDUP_EXCLUDE_KINDS = {"length", "trailing_condition", "synonym_rotation",
                         "safety_instruction"}


def lint_and_gate(text, context="procedure", file_path=None):
    # Block-aware via split_into_blocks (core.blocks, shared with
    # apply_mechanical_fixes below): code fences are never linted at all,
    # and each header/list-item/paragraph is sentence-tokenized within its
    # own bounds rather than the whole document being flattened into one
    # blob -- see split_into_blocks's docstring for the false-positive this
    # fixed.
    #
    # The effective glossary is resolved ONCE per call, not per sentence:
    # pack content depends on which file is being written (packs hang off
    # the routing rule that matches the path), so it is no longer a free
    # module-level constant. Same "read fresh, but not per iteration"
    # discipline _enabled_check_ids() already uses.
    project_terms = effective_project_terms(file_path)
    suppressed = suppressed_vocabulary()
    sentences = []
    safety_hits = []
    for block_type, content in split_into_blocks(text):
        is_numbered_item = False
        if block_type in ("fence", "blank"):
            continue
        elif block_type == "header":
            block_text = _HEADER_RE.sub("", content).strip()
        elif block_type == "list_item":
            m = _LIST_ITEM_RE.match(content)
            block_text = m.group(2) if m else content
            is_numbered_item = bool(m and m.group(1).strip()[0].isdigit())
        else:  # paragraph
            block_text = content
        # Inline code spans get the same Untouchables exemption as fences --
        # without this, `you should not retry` inside backticks trips a real
        # "should" flag and denies a write over text that was never supposed
        # to be linted at all. Strip rather than protect-and-restore (unlike
        # fix_sentence): detection only needs the span gone, not preserved.
        block_text = re.sub(r"`[^`\n]+`", " ", block_text)
        if block_type in ("paragraph", "list_item"):
            safety_hits.extend((h, block_text) for h in check_safety_instruction(block_text))
        # A NUMBERED list item is structurally a procedure step (rule 6.x's
        # procedure register, 20-word limit) regardless of what context the
        # caller passed for the surrounding document's prose. A BULLETED
        # item does NOT get this treatment -- a bulleted item can be plain
        # descriptive enumeration (a limitations list, a feature list), not
        # a command to carry out.
        block_context = "procedure" if is_numbered_item else context
        sentences.extend((s, block_context) for s in tokenize_sentences(block_text))
    results = [lint_sentence(s, ctx, project_terms, suppressed) for s, ctx in sentences]

    mechanical = []
    semantic = []
    for h, block_text in safety_hits:
        # h["label"] is the severity word (WARNING/CAUTION/...) the hit
        # already computed -- _label(h) would miss it, since default_label
        # only ever looks for "word"/"phrase"/"modal".
        semantic.append({"kind": "safety_instruction", "label": h.get("label"),
                          "detail": h, "text": block_text})
    for r in results:
        if r["length"]:
            # Always semantic: splitting an over-length sentence needs a
            # judgment call about where the clause boundary is, never a
            # safe mechanical rewrite.
            semantic.append({"kind": "length", "label": _label(r["length"]),
                              "detail": r["length"], "text": r["text"]})
        for v in r["vocabulary"]:
            (mechanical if v["auto_fix"] else semantic).append(
                {"kind": "vocabulary", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["ing_forms"]:
            semantic.append({"kind": "ing_form", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["perfect_tense"]:
            mechanical.append({"kind": "perfect_tense", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["progressive"]:
            # Past progressive with a table match is safely auto-fixable
            # (see PROGRESSIVE_ING_TO_PAST); present progressive and
            # untabled past progressive stay flag-only -- no safe fix
            # without subject-verb agreement or a wider verb table.
            (mechanical if v["auto_fix"] else semantic).append(
                {"kind": "progressive", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["passive"]:
            semantic.append({"kind": "passive", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["modals"]:
            (mechanical if v["auto_fix"] and v.get("replacement") else semantic).append(
                {"kind": "modal", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["punctuation"]:
            mechanical.append({"kind": "punctuation", "label": _label(v), "detail": v, "text": r["text"]})
        if r["trailing_condition"]:
            semantic.append({"kind": "trailing_condition", "label": _label(r["trailing_condition"]),
                              "detail": r["trailing_condition"], "text": r["text"]})
        for v in r["latin_abbrev"]:
            mechanical.append({"kind": "latin_abbrev", "label": _label(v), "detail": v, "text": r["text"]})
        for v in r["inclusive_language"]:
            semantic.append({"kind": "inclusive_language", "label": _label(v), "detail": v, "text": r["text"]})

    lintable_text = " ".join(s for s, _ctx in sentences)  # excludes fence content, matches what was actually linted
    for v in check_synonym_rotation(lintable_text):
        semantic.append({"kind": "synonym_rotation", "label": _label(v), "detail": v, "text": None})

    # Every check above runs unconditionally (they're cheap regex/string
    # ops); a disabled check's own flags are dropped here in one place,
    # same shape slopwatch's/codewatch's own lint_and_gate already use.
    enabled = _enabled_check_ids(file_path)
    mechanical = [f for f in mechanical if f["kind"] in enabled]
    semantic = [f for f in semantic if f["kind"] in enabled]

    mechanical = dedup_flags(mechanical, exclude_kinds=_DEDUP_EXCLUDE_KINDS)
    semantic = dedup_flags(semantic, exclude_kinds=_DEDUP_EXCLUDE_KINDS)

    # "status" reports whether the ENGINE found any semantic flag at all,
    # not whether the write would be denied. Callers that make the actual
    # gate decision never read this field; they call blocking_semantic_flags()
    # instead, which excludes vocabulary flags staged out of denial for now.
    # A sentence can legitimately report status="semantic_flags" here and
    # still pass the live gate cleanly -- e.g. any unknown_vocabulary hit
    # alone produces this status, even though it blocks nothing.
    status = "clean" if not mechanical and not semantic else (
        "semantic_flags" if semantic else "mechanical_violations")

    return {
        "status": status,
        "sentence_count": len(sentences),
        "mechanical_violations": mechanical,
        "semantic_flags": semantic,
    }


# Vocabulary is deliberately held out of the deny decision for now, staged
# rather than flipped on wholesale: unknown_vocabulary and
# unapproved_no_replacement (a real dictionary word with no given
# substitute, e.g. "product") would deny on ordinary software vocabulary
# the aviation-scoped standard was never going to cover.
# unapproved_synonym reaches semantic_flags at all now only because ALL
# vocabulary auto-fix is disabled (see UNAPPROVED_NO_AUTOFIX above) -- it's
# excluded here too, for the same staging reason, not because it's unsafe
# to report. Re-enabling any of these as a denial reason needs a real
# PROJECT_TERMS starter glossary (exists now, see glossary.py's register())
# plus a first-occurrence registration flow (glossary.py, but nothing calls
# it automatically yet) to mature first.
#
# Which types are actually staged out is DEFAULT_OPTIONS["excluded_vocab_types"],
# not a fixed set -- a project can narrow it (start blocking on genuinely
# unknown words) or widen it, the same as any other tunable option.
#
# THE SINGLE SOURCE OF TRUTH for "does this flag actually block a write" --
# every caller (the hook, the CLI, the MCP server) goes through
# blocking_semantic_flags() rather than keeping its own copy of this filter.
def blocking_semantic_flags(semantic_flags):
    excluded = _options()["excluded_vocab_types"]
    return [f for f in semantic_flags
            if not (f["kind"] == "vocabulary" and f["detail"]["type"] in excluded)]


def fix_sentence(sentence, project_terms=None, suppressed=None):
    # Protect inline code spans before any substitution -- the "Untouchables"
    # principle (code, identifiers, CLI flags must never be rewritten) means
    # a contraction or slop word inside backticks must survive unchanged,
    # even though the same regexes would happily match text inside them.
    _pt = PROJECT_TERMS if project_terms is None else project_terms
    _sup = suppressed or _NO_SUPPRESSION
    protected = []
    def _protect(m):
        protected.append(m.group(0))
        return f"\x00{len(protected) - 1}\x00"
    s = re.sub(r"`[^`\n]+`", _protect, sentence)

    # Modal words: resolved through _modal_resolution, the same function
    # check_modals uses for detection, so the applied fix always matches
    # what was flagged -- not a separate, independently-derived substitution.
    # Excluded from the generic vocab pass below entirely (would/may/might/
    # could/should are not in UNAPPROVED_MAP) so this is the only place that
    # touches them.
    _modal_has_if = bool(re.search(r"\bif\b", s, re.IGNORECASE))
    _modal_has_warning = bool(re.search(r"\b(warning|caution)\b", s, re.IGNORECASE))
    _modal_collocation_spans = {m.start(1) for m in SEMI_MODAL_COLLOCATION.finditer(s)}

    def _modal_sub(m):
        modal = m.group(1).lower()
        auto_fix, replacement, _, _ = _modal_resolution(
            modal, m.start(1) in _modal_collocation_spans, _modal_has_if, _modal_has_warning)
        return replacement if auto_fix and replacement else m.group(0)
    s = re.sub(r"\b(should|would|may|might|could)\b", _modal_sub, s, flags=re.IGNORECASE)

    def _contraction_sub(m):
        return CONTRACTION_EXPANSIONS.get(m.group(0).lower(), m.group(0))
    s = re.sub(r"\b\w+'\w+\b", _contraction_sub, s)

    s = re.sub(r"\b(has|have|had)\s+been\b",
               lambda m: {"has": "was", "have": "were", "had": "was"}[m.group(1).lower()],
               s, flags=re.IGNORECASE)

    def _perfect_sub(m):
        participle = m.group(2)
        lp = participle.lower()
        if lp.endswith("ed"):
            return participle
        if lp in IRREGULAR_PARTICIPLES:
            return IRREGULAR_PARTICIPLES[lp]
        return m.group(0)  # not a recognized participle -- e.g. "has three
                             # components" -- leave the whole match untouched,
                             # don't strip a "has" that wasn't an auxiliary
    s = re.sub(r"\b(has|have|had)\s+(?!been\b)(\w+)\b", _perfect_sub, s, flags=re.IGNORECASE)

    # Latin abbreviations (GR-6) -- must run before the vocab pass below,
    # since periods break word boundaries and "e.g." would otherwise be seen
    # as two separate one-letter tokens ("e", "g"), neither touched by it.
    def _latin_sub(m):
        return LATIN_ABBREV_MAP[m.group(1).lower()]
    s = LATIN_ABBREV_RE.sub(_latin_sub, s)

    # Past progressive -> simple past, table-matched cases only (see
    # PROGRESSIVE_ING_TO_PAST). "is/are" progressive and untabled "was/were"
    # cases are left untouched here -- they're semantic flags, not fixed.
    def _progressive_sub(m):
        aux, ing = m.group(1), m.group(2)
        if aux.lower() in ("was", "were"):
            return PROGRESSIVE_ING_TO_PAST.get(ing.lower(), m.group(0))
        return m.group(0)
    s = re.sub(r"\b(is|are|was|were)\s+(\w+ing)\b", _progressive_sub, s, flags=re.IGNORECASE)

    def _vocab_sub(m):
        w = m.group(0)
        lw = w.lower()
        # Mirrors check_vocabulary's own precedence exactly (approved wins).
        # Without this check here too, this pass and detection silently
        # disagreed the moment the real dictionary introduced words that are
        # approved in one part of speech and unapproved in another (70 of
        # them, e.g. "complete" v=approved/adj=unapproved->FULL): detection
        # correctly skipped the approved sense, but this substitution had no
        # APPROVED_WORDS check at all and rewrote it anyway -- live-tested
        # regression, "could complete the task" auto-"fixed" to "can full
        # the task."
        if ("'" in w or lw in _pt or lw in UNAPPROVED_NO_AUTOFIX
                or (lw in APPROVED_WORDS and lw not in _sup["approved"])
                or lw in _sup["unapproved"]):
            return w
        return UNAPPROVED_MAP.get(lw, w)
    s = re.sub(r"\b[A-Za-z]+\b", _vocab_sub, s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = re.sub(r"\s+([.,!?])", r"\1", s)

    if ";" in s:
        parts = [p.strip() for p in s.split(";") if p.strip()]
        capped = []
        for p in parts:
            p = p[0].upper() + p[1:]
            if not p.endswith((".", "!", "?")):
                p += "."
            capped.append(p)
        s = " ".join(capped)

    def _restore(m):
        return protected[int(m.group(1))]
    s = re.sub(r"\x00(\d+)\x00", _restore, s)

    return s


def _fix_paragraph(text, project_terms, suppressed):
    return " ".join(fix_sentence(s, project_terms, suppressed)
                     for s in tokenize_sentences(text))


def apply_mechanical_fixes(text, file_path=None):
    """Only call this when status == 'mechanical_violations' (no semantic
    flags) -- semantic flags mean the text needs a human/model decision, not
    a blind rewrite.

    Block-aware via split_into_blocks: code fences and inline code are never
    touched; headers and list items are fixed individually and kept on their
    own line (never merged with surrounding text); paragraphs are fixed and
    rejoined but stay separated by the original blank lines. KNOWN
    LIMITATION: within a single paragraph, original line-wrap positions are
    not preserved (all sentences of one paragraph collapse onto one output
    line) -- paragraph and block boundaries survive, exact line-wrapping
    does not.
    """
    # Resolved once per call, not once per sentence -- the effective
    # glossary depends on which file is being written (packs are path-
    # scoped), so it can no longer be a module-level constant read for free.
    project_terms = effective_project_terms(file_path)
    suppressed = suppressed_vocabulary()
    out = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            out.append(content)
        elif block_type == "header":
            out.append(fix_sentence(content, project_terms, suppressed))
        elif block_type == "list_item":
            marker, item_text = _LIST_ITEM_RE.match(content).groups()
            out.append(marker + (_fix_paragraph(item_text, project_terms, suppressed)
                                  if item_text.strip() else item_text))
        else:  # paragraph
            out.append(_fix_paragraph(content, project_terms, suppressed))
    return "\n".join(out)


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    context = "procedure"
    print(json.dumps(lint_and_gate(text, context), indent=2))
