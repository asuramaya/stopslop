#!/usr/bin/env python3
"""
Throwaway Tier 1 prototype for SGS (STE100 Gatekeeper System).

Implements the pipeline exactly as specified in the design doc, section 5.3:
tokenize -> length check -> vocabulary scan -> verb form scan -> modal scan
-> punctuation scan.

This is NOT the real ASD-STE100 dictionary (that's a licensed standard --
see design doc section 12, Q8). APPROVED_WORDS below is a small
representative "simple English" stand-in built for design validation only.
Where the doc's own sections disagree with each other, this script follows
whichever section is noted in a comment, and the disagreement itself is
left visible rather than silently resolved.
"""

import re
import sys
import json
import os

# --- Tier 1: base approved dictionary, loaded from the real ASD-STE100
# extraction (prototype/ste100_dictionary.json, built by build_dictionary.py
# from docs/ASD-STE100-dictionary-extracted.dat -- see that file's docstring
# for how the extraction was verified before being trusted as enforcement
# data). Replaces the earlier ~120-word "simple English" stand-in.
MODAL_WORDS = {"should", "would", "may", "might", "could"}


def _load_dictionary():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ste100_dictionary.json")
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
# ALL unapproved_synonym auto-fix is disabled -- not just the 409 words in
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
# standard, not a software one), e.g. "repository" or "endpoint". Persisted
# to prototype/ste100-project-terms.json, alongside ste100_dictionary.json --
# shipped seed data, not session-local runtime state (unlike
# .claude/ste100-history.log), so it lives with the tool's other data files
# and ships in version control -- so a registration survives past this
# process. It used to be an in-memory {} that reset on every run, meaning
# nothing registered "live" ever actually stuck. See register_term.py to
# add a word.
PROJECT_TERMS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ste100-project-terms.json")


def _load_project_terms():
    if not os.path.exists(PROJECT_TERMS_PATH):
        return {}
    try:
        with open(PROJECT_TERMS_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


PROJECT_TERMS = _load_project_terms()

# would/may/might/could default replacements for check_modals' non-heuristic
# fallback path -- deliberately NOT in UNAPPROVED_MAP. They used to be (both
# the old hand-curated stand-in and an earlier version of this dictionary
# load put them there), and that was a real bug, found live while verifying
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

# Real ASD-STE100 rule 3.5 whitelist (docs/ASD-STE100-rules-extracted.md):
# nouns (lighting, opening, routing, servicing), adjectives (mating, missing,
# remaining), pronoun (something), preposition (during). The earlier list here
# was a placeholder guess made before the real spec was extracted -- wrong.
ING_NOUN_EXCEPTIONS = {"lighting", "opening", "routing", "servicing",
                        "mating", "missing", "remaining", "something", "during"}

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


def tokenize_sentences(text):
    """Naive regex sentence splitter -- the FAST option from doc section 12
    Q4, not the accurate-but-slow spaCy option. Deliberately naive so we can
    see where it breaks on abbreviations."""
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text.strip())
    return [s.strip() for s in raw if s.strip()]


def words(sentence):
    return re.findall(r"[A-Za-z']+", sentence)


def check_length(sentence, context="procedure"):
    limit = 25 if context == "description" else 20
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


def check_vocabulary(sentence):
    violations = []
    for w in words(sentence):
        lw = w.lower().strip("'")
        if not lw or lw in APPROVED_WORDS or lw in PROJECT_TERMS:
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
            # out of gate denial anyway (see pretool_hook.py) alongside
            # unknown_vocabulary, pending a PROJECT_TERMS glossary and a real
            # registration flow -- see project memory for why.
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


def check_ing(sentence):
    # Deliberately does NOT try to auto-exempt "-ing NOUN" compounds
    # (monitoring alerts, troubleshooting section) even though rule 3.5
    # permits them -- tried that heuristic and it silently exempted genuine
    # misuse too ("initiating failover" reads identically to "monitoring
    # alerts" at the regex level: ING + NOUN, no way to tell gerund-object
    # from noun-modifier without real parsing). A false positive here costs
    # a cheap human/model glance; a false negative ships a real violation
    # silently. For a gate, over-flag and let it be reviewed.
    hits = []
    for m in re.finditer(r"\b(\w+ing)\b", sentence, re.IGNORECASE):
        w = m.group(1).lower()
        if w in ING_NOUN_EXCEPTIONS:
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
        if w in APPROVED_WORDS or w in PROJECT_TERMS:
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
    the way they did before this was factored out: fix_sentence used to
    substitute modal words straight off UNAPPROVED_MAP, with no knowledge of
    the collocation exception or the if/warning heuristic below. Live-tested
    live regression: "the operator may need to stop the test" auto-"fixed"
    to "the operator can need to stop the test" via that blind substitution,
    despite check_modals correctly flagging the very same word as non-auto-
    fixable in the same call -- detection and fixing had just never agreed.
    Returns (auto_fix, replacement, rule, note_or_basis)."""
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


# Ported from SimpleEnglish's ste_lint.py (MIT) -- condition-before-command
# (rules 5.4/7.2): the "if"/"when" clause should open the sentence, not
# trail after the command. Requires restructuring (move the clause), not a
# substitution, so this is a semantic flag, not auto-fixable.
TRAILING_COND = re.compile(r"\w[^.!?\n]{3,}\s\b(if|when)\b\s", re.IGNORECASE)


def check_trailing_condition(sentence):
    if TRAILING_COND.search(sentence) and not re.match(r"^(if|when)\b", sentence, re.IGNORECASE):
        return {"rule": "5.4", "auto_fix": False,
                "note": "condition should open the sentence, not trail after the command"}
    return None


# Ported from SimpleEnglish's ste_lint.py (MIT) -- one term per concept
# (rules 1.11/9.4), document-level: flags when 2+ members of the same
# rotation set appear anywhere in the text. Which term to standardize on is
# a judgment call (semantic, not auto-fixable) -- same category as glossary
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


# Section 7: safety instructions (rules 7.1-7.3). FORMAT-ONLY by design
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


def lint_sentence(sentence, context="procedure"):
    return {
        "text": sentence,
        "length": check_length(sentence, context),
        "vocabulary": check_vocabulary(sentence),
        "ing_forms": check_ing(sentence),
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
_DEDUP_EXCLUDE_KINDS = {"length", "trailing_condition", "synonym_rotation"}


def dedup_flags(flags):
    """Collapse repeated occurrences of the exact same word/phrase/modal
    into one flag with an 'occurrences' count, keeping the first instance's
    'text' as the example. Only applies to word/phrase-level kinds -- see
    _DEDUP_EXCLUDE_KINDS for what's deliberately never collapsed."""
    groups = {}
    order = []
    for f in flags:
        if f["kind"] in _DEDUP_EXCLUDE_KINDS:
            key = ("__no_dedup__", id(f))
        else:
            d = f["detail"]
            ident = d.get("word") or d.get("phrase") or d.get("modal")
            key = (f["kind"], ident.lower()) if ident else ("__no_dedup__", id(f))
        groups.setdefault(key, []).append(f)
        if key not in order:
            order.append(key)
    result = []
    for key in order:
        group = groups[key]
        first = dict(group[0])
        if len(group) > 1:
            first["detail"] = dict(first["detail"])
            first["detail"]["occurrences"] = len(group)
        result.append(first)
    return result


def lint_and_gate(text, context="procedure"):
    # Block-aware via split_into_blocks (defined below, shared with
    # apply_mechanical_fixes): code fences are never linted at all, and each
    # header/list-item/paragraph is sentence-tokenized within its own bounds
    # rather than the whole document being flattened into one blob -- see
    # split_into_blocks's docstring for the false-positive this fixed.
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
        # caller passed for the surrounding document's prose. Found live
        # while stress-testing: pretool_hook.py always calls this with
        # context="description" (25-word limit), so a genuine 21-word
        # numbered setup step passed cleanly even though it would fail the
        # stricter procedure limit real ASD-STE100 writing actually uses
        # for step-by-step instructions -- the exact content type the
        # standard was built for was the one type never getting checked at
        # its own real limit. A BULLETED item does NOT get this treatment --
        # found live in the same pass: a bulleted item can be plain
        # descriptive enumeration (a limitations list, a feature list), not
        # a command to carry out, and the 20-word limit incorrectly
        # penalized one of exactly that kind.
        block_context = "procedure" if is_numbered_item else context
        sentences.extend((s, block_context) for s in tokenize_sentences(block_text))
    results = [lint_sentence(s, ctx) for s, ctx in sentences]

    mechanical = []
    semantic = []
    for h, block_text in safety_hits:
        semantic.append({"kind": "safety_instruction", "detail": h, "text": block_text})
    for r in results:
        if r["length"]:
            (mechanical if "conjunction-splittable" in [] else semantic).append(
                {"kind": "length", "detail": r["length"], "text": r["text"]})
        for v in r["vocabulary"]:
            (mechanical if v["auto_fix"] else semantic).append(
                {"kind": "vocabulary", "detail": v, "text": r["text"]})
        for v in r["ing_forms"]:
            semantic.append({"kind": "ing_form", "detail": v, "text": r["text"]})
        for v in r["perfect_tense"]:
            mechanical.append({"kind": "perfect_tense", "detail": v, "text": r["text"]})
        for v in r["progressive"]:
            # Past progressive with a table match is safely auto-fixable
            # (see PROGRESSIVE_ING_TO_PAST); present progressive and
            # untabled past progressive stay flag-only -- no safe fix
            # without subject-verb agreement or a wider verb table.
            (mechanical if v["auto_fix"] else semantic).append(
                {"kind": "progressive", "detail": v, "text": r["text"]})
        for v in r["passive"]:
            semantic.append({"kind": "passive", "detail": v, "text": r["text"]})
        for v in r["modals"]:
            (mechanical if v["auto_fix"] and v.get("replacement") else semantic).append(
                {"kind": "modal", "detail": v, "text": r["text"]})
        for v in r["punctuation"]:
            mechanical.append({"kind": "punctuation", "detail": v, "text": r["text"]})
        if r["trailing_condition"]:
            semantic.append({"kind": "trailing_condition", "detail": r["trailing_condition"], "text": r["text"]})
        for v in r["latin_abbrev"]:
            mechanical.append({"kind": "latin_abbrev", "detail": v, "text": r["text"]})
        for v in r["inclusive_language"]:
            semantic.append({"kind": "inclusive_language", "detail": v, "text": r["text"]})

    lintable_text = " ".join(s for s, _ctx in sentences)  # excludes fence content, matches what was actually linted
    for v in check_synonym_rotation(lintable_text):
        semantic.append({"kind": "synonym_rotation", "detail": v, "text": None})

    mechanical = dedup_flags(mechanical)
    semantic = dedup_flags(semantic)

    status = "clean" if not mechanical and not semantic else (
        "semantic_flags" if semantic else "mechanical_violations")

    return {
        "status": status,
        "sentence_count": len(sentences),
        "mechanical_violations": mechanical,
        "semantic_flags": semantic,
    }


def fix_sentence(sentence):
    # Protect inline code spans before any substitution -- the "Untouchables"
    # principle (code, identifiers, CLI flags must never be rewritten) means
    # a contraction or slop word inside backticks must survive unchanged,
    # even though the same regexes would happily match text inside them.
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
        if "'" in w or lw in APPROVED_WORDS or lw in PROJECT_TERMS or lw in UNAPPROVED_NO_AUTOFIX:
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


_HEADER_RE = re.compile(r"^#{1,6}\s")
_LIST_ITEM_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+)(.*)$")
_FENCE_RE = re.compile(r"^```")


def split_into_blocks(text):
    """Split a document into (block_type, content) pairs: 'fence', 'header',
    'list_item', 'paragraph', or 'blank'. SHARED by lint_and_gate (skips
    'fence' entirely, bounds sentence-tokenization to each other block
    individually) and apply_mechanical_fixes (skips 'fence', fixes each
    block independently). Sharing this is not incidental: an earlier version
    had each function do its own ad hoc parsing, and detection wasn't
    block-aware at all -- a real document with a header + list + code fence
    got flattened into one 36-word "sentence" by the plain tokenizer and was
    denied on a false length violation, discovered only by testing an actual
    structured document live through the hook, not by the flat-paragraph
    tests that had been passing until then. One parser, used by both sides,
    is what actually closes that gap rather than re-opening it differently
    each time either function changes."""
    lines = text.split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _FENCE_RE.match(stripped):
            fence_lines = [line]
            i += 1
            while i < len(lines):
                fence_lines.append(lines[i])
                is_close = _FENCE_RE.match(lines[i].strip())
                i += 1
                if is_close:
                    break
            blocks.append(("fence", "\n".join(fence_lines)))
            continue
        if not stripped:
            blocks.append(("blank", line))
            i += 1
            continue
        if _HEADER_RE.match(stripped):
            blocks.append(("header", line))
            i += 1
            continue
        m = _LIST_ITEM_RE.match(line)
        if m:
            blocks.append(("list_item", line))
            i += 1
            continue

        para_lines = []
        while i < len(lines):
            s2 = lines[i].strip()
            if not s2 or _FENCE_RE.match(s2) or _HEADER_RE.match(s2) or _LIST_ITEM_RE.match(lines[i]):
                break
            para_lines.append(lines[i])
            i += 1
        blocks.append(("paragraph", " ".join(l.strip() for l in para_lines)))

    return blocks


def _fix_paragraph(text):
    return " ".join(fix_sentence(s) for s in tokenize_sentences(text))


def apply_mechanical_fixes(text):
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
    out = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            out.append(content)
        elif block_type == "header":
            out.append(fix_sentence(content))
        elif block_type == "list_item":
            marker, item_text = _LIST_ITEM_RE.match(content).groups()
            out.append(marker + (_fix_paragraph(item_text) if item_text.strip() else item_text))
        else:  # paragraph
            out.append(_fix_paragraph(content))
    return "\n".join(out)


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read()
    context = "procedure"
    print(json.dumps(lint_and_gate(text, context), indent=2))
