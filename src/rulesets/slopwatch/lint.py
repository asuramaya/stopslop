#!/usr/bin/env python3
"""slopwatch: originally a small demo ruleset proving stopslop's plugin
contract isn't secretly shaped around ASD-STE100, now consolidated with
checks pulled from the wider MIT-licensed "AI slop detection" ecosystem.
Where ste100 exists to ERASE individual voice on purpose (one approved word
per concept, no modals, no stylistic variation -- uniform aviation-manual
clarity), slopwatch targets ordinary AI-writing tells while trying to flag
sparingly rather than demand uniformity -- the two rulesets are pointed in
almost opposite directions on purpose.

Original six checks, in stopslop's own words and regex logic -- not ported
from any specific published word/pattern list:
  - filler_opener        (semantic)  throat-clearing sentence openers
  - stock_adverb          (mechanical) standalone filler adverbs, safe to delete
  - colon_reveal           (semantic)  short-buildup, punchy-reveal construction
  - binary_contrast         (semantic)  "It's not X. It's Y." across sentences
  - em_dash_cluster           (semantic, document-level)  too many em dashes
  - weasel_attribution         (semantic)  unnamed-authority phrasing

Ported from jv-k/deslopper (MIT) -- see NOTICE. deslopper is a real
deterministic tell-matching engine, the closest architectural match to
stopslop of anything surveyed, so these are literal ports of its
recommended preset's patterns, not reimplementations:
  - entity_encoded_punctuation (mechanical) an em dash/section sign/middle
    dot written as an HTML entity -- an evasion vector against a plain-
    character check, not just a style issue
  - bold_bullet_lead      (semantic)  a bolded list-item label used as a tag
  - id_label_lead          (semantic)  a fake ID tag on a list item ("R-1.")
  - not_just_x_but_y        (semantic)  "not just X but Y" padding
  - vague_intensifier         (semantic)  very/really/quite/significantly,
    no number behind it
  - emoji_in_prose             (mechanical) emoji or decorative checkmarks
  - marketing_adjective          (semantic)  seamless/robust/cutting-edge...
  - filler_verb                   (semantic)  leverages/facilitates/unlocks...

Ported from piyushbhattadforapps/pseo-quality-gate (MIT) -- see NOTICE:
  - marketing_cliche       (semantic)  "hidden gem", "let's dive in"...
  - solicit_criticism       (semantic)  fake-humility feedback requests

Own words, informed by the general pattern catalogs published by
petergyang/no-ai-slop and shessenauer/deslop-ai-lint-skill (both MIT) but
not copied from either -- same category as the original six, a
reimplementation of a documented CONCEPT, not a port of code or text:
  - unearned_profundity      (semantic)  a dramatic turning-point sentence
    with nothing concrete behind it
  - canned_question_answer    (semantic)  short rhetorical question
    immediately answered by the next sentence
  - negative_listing            (semantic)  "Not X. Not Y." listing
  - dramatic_fragmentation        (semantic)  "That's it. That's the whole
    thing." one-line punchy fragments

blocking_semantic_flags() below is a genuinely different POLICY from
ste100's (an exclusion list of vocabulary types): individual flags never
block alone here -- an occasional AI-prose tell is normal, this ruleset
protects voice rather than enforcing uniformity -- but a write is denied if
an em-dash cluster fires on its own, or four or more flags of any kind
appear across the whole document. Proves the plugin contract needs no new
core mechanism to support a different deny policy: it's just a function
each ruleset owns.
"""
import re
import statistics

from core.blocks import (
    tokenize_sentences, split_into_blocks,
    HEADER_RE, LIST_ITEM_RE,
)
from core.flags import dedup_flags, default_label as _label
from core import (checks as _checks, config as _config, custom_checks as _custom_checks,
                  paths as _paths, terms as _terms)

# slopwatch builds SENTENCE (the full tokenized-sentence list) and
# DOCUMENT (the whole assembled lintable text) uniformly -- its LINE
# domain is list-item lines ONLY (bold_bullet_lead/id_label_lead), not
# every line, so a custom check may not declare LINE here even though
# codewatch's own custom checks can. See core/custom_checks.py.
CUSTOM_CHECK_UNITS = _custom_checks.DEFAULT_ALLOWED_UNITS


def effective_checks_table():
    """CHECKS_TABLE merged with this ruleset's own custom checks -- see
    core/custom_checks.py, and rulesets/codewatch/lint.py's identical
    helper. Falls back to CHECKS_TABLE alone if project root can't be
    resolved."""
    try:
        project_root = _paths.find_project_root(__file__)
    except Exception:
        return CHECKS_TABLE
    return _custom_checks.effective_checks_table(CHECKS_TABLE, project_root, "slopwatch",
                                                   CUSTOM_CHECK_UNITS)


def _enabled_check_ids(file_path=None):
    """Every check that should actually run right now: this ruleset's
    declared checks minus whatever stopslop.config.json's
    "disabled_checks" names. Read fresh every call, not cached -- see
    core.checks.enabled_check_ids."""
    table = effective_checks_table()
    try:
        project_root = _paths.find_project_root(__file__)
    except Exception:
        return set(_checks.all_check_ids(table))
    return _checks.enabled_check_ids(table, project_root, "slopwatch", file_path)


def _custom_terms(list_id, file_path=None):
    """The non-built-in layers (packs, then the project's own registrations)
    for one term list -- the `extra` every list-shaped check below already
    takes. Same never-cache-it, read-fresh-every-call philosophy as
    _enabled_check_ids(). Falls back to none (never breaks a check) if
    project root can't be resolved.

    file_path matters because pack content is resolved against the routing
    rule that matches the file being written, not against the ruleset --
    see core.config.packs_for_path for why domain is a property of the path."""
    try:
        project_root = _paths.find_project_root(__file__)
        layers = _terms.resolve(TERM_LISTS[list_id], project_root, "slopwatch",
                                 list_id, file_path=file_path)
        return sorted(set(layers["packs"]) | set(layers["project"]))
    except Exception:
        return []


def _lexicon_terms(file_path=None):
    """The project lexicon WITH its notes -- unlike _custom_terms, which
    flattens a list to bare strings. terminology's whole point is that a
    banned synonym's note names the canonical term, so the flag can say
    the fix and not only the fault. Same fall-back-to-nothing posture."""
    try:
        project_root = _paths.find_project_root(__file__)
        layers = _terms.resolve(TERM_LISTS["terminology"], project_root,
                                 "slopwatch", "terminology", file_path=file_path)
        return {term.lower(): {"note": (info or {}).get("note", "")}
                for term, info in layers["effective"].items()}
    except Exception:
        return {}


# --- filler_opener (semantic) ------------------------------------------
FILLER_OPENERS = [
    re.compile(r"^it(?:'s| is) (?:worth noting|important to note) that\b", re.IGNORECASE),
    re.compile(r"^needless to say\b", re.IGNORECASE),
    re.compile(r"^at the end of the day\b", re.IGNORECASE),
    re.compile(r"^when all is said and done\b", re.IGNORECASE),
    re.compile(r"^in (?:today's|this) (?:fast-paced|rapidly evolving|ever-changing)\b", re.IGNORECASE),
]


def check_filler_opener(sentence):
    stripped = sentence.strip()
    for rx in FILLER_OPENERS:
        m = rx.match(stripped)
        if m:
            return [{"phrase": m.group(0), "rule": "slopwatch.filler_opener", "auto_fix": False,
                      "note": "throat-clearing opener -- cut it and state the point directly"}]
    return []


# --- stock_adverb (mechanical) ------------------------------------------
STOCK_ADVERBS = {"undoubtedly", "arguably", "notably", "importantly", "ultimately"}


def check_stock_adverb(sentence, extra=()):
    words = STOCK_ADVERBS | set(extra)
    pattern = re.compile(r"(,\s*)?\b(" + "|".join(re.escape(w) for w in words) + r")\b(,\s*|\s+)?",
                          re.IGNORECASE)
    hits = []
    for m in pattern.finditer(sentence):
        hits.append({"word": m.group(2), "rule": "slopwatch.stock_adverb",
                      "auto_fix": True, "replacement": ""})
    return hits


# --- colon_reveal (semantic) --------------------------------------------
_COLON_REVEAL_RE = re.compile(r"^(.{1,60}?):\s+(\S.*)$")
_COLON_LABEL_WORDS = {"note", "example", "examples", "warning", "caution", "steps",
                       "requirement", "requirements", "following", "summary", "tip", "important",
                       "needed", "required", "include", "includes", "contains", "options",
                       "source", "date", "incident", "help", "legend", "given"}
# "Step 2:", "Method 2:", "Step one:" -- a numbered/ordinal step or method
# label, not a dramatic reveal. Live-verified false-positive class (see
# _MD_BOLD_LEAD_MARKERS below) found by stopslop.py scan against this
# project's own docs/, not a synthetic fixture.
_NUMBERED_LABEL_RE = re.compile(
    r"^[A-Za-z]+\s+(?:\d+(?:\.\d+)*|one|two|three|four|five|six|seven|eight|nine|ten)$",
    re.IGNORECASE)
# Leading bullet/dash markers to strip before checking for a markdown-bold
# lead -- deliberately excludes "*" itself, since that's the very character
# the bold-lead check below is looking for.
_MD_BOLD_LEAD_MARKERS = "-—•\t "


def check_colon_reveal(sentence):
    m = _COLON_REVEAL_RE.match(sentence.strip())
    if not m:
        return []
    before, _after = m.groups()
    before = before.strip()
    # A markdown-bold label ("**Manufacturing processes**:", the same
    # construct slopwatch's own bold_bullet_lead check already names) is a
    # structural glossary/spec-entry lead, not a buildup-then-reveal --
    # even one prefixed with a bullet/dash ("-- **(c)**:") or where the
    # colon itself falls inside the bold span ("**3.2 Use only these
    # forms/tenses:").
    if before.lstrip(_MD_BOLD_LEAD_MARKERS).startswith("**"):
        return []
    if _NUMBERED_LABEL_RE.match(before):
        return []
    words_before = before.split()
    if not (1 <= len(words_before) <= 6):
        return []
    last_word = words_before[-1].lower().strip(".,;:")
    if last_word in _COLON_LABEL_WORDS:
        return []  # a genuine label/list intro, not a dramatic reveal
    return [{"phrase": before + ":", "rule": "slopwatch.colon_reveal", "auto_fix": False,
              "note": "buildup-then-reveal construction -- state it as a plain sentence instead"}]


# --- weasel_attribution (semantic) ---------------------------------------
WEASEL_PHRASES = ["studies show", "experts agree", "research suggests", "many believe"]


def check_weasel_attribution(sentence, extra=()):
    phrases = list(WEASEL_PHRASES) + list(extra)
    if not phrases:
        return []
    pattern = re.compile(r"\b(" + "|".join(re.escape(p) for p in phrases) + r")\b", re.IGNORECASE)
    return [{"phrase": m.group(1), "rule": "slopwatch.weasel_attribution", "auto_fix": False,
              "note": "unnamed authority -- name the actual source, or cut the claim"}
            for m in pattern.finditer(sentence)]


# --- binary_contrast (semantic, adjacent-sentence-pair) -------------------
_NEGATIVE_IS_RE = re.compile(r"^(it'?s|it is|this is|that is) not\b", re.IGNORECASE)
_AFFIRMATIVE_IS_RE = re.compile(r"^(it'?s|it is|this is|that is)\b", re.IGNORECASE)


def check_binary_contrast(sentences):
    hits = []
    for i in range(len(sentences) - 1):
        a, b = sentences[i].strip(), sentences[i + 1].strip()
        # B must open affirmatively AND carry no "not" anywhere in it --
        # not just outside the exact "it is not" prefix. Found live:
        # "This is not a bug. It is also not fixed yet." -- B doesn't match
        # the negative-prefix regex (there's "also" between "is" and
        # "not"), so it fell through to "affirmative" and was wrongly
        # flagged as a binary-contrast reveal even though B is still
        # negative in spirit.
        if (_NEGATIVE_IS_RE.match(a) and _AFFIRMATIVE_IS_RE.match(b)
                and not re.search(r"\bnot\b", b, re.IGNORECASE)):
            hits.append({"phrase": a, "rule": "slopwatch.binary_contrast", "auto_fix": False,
                          "note": "'not X, it's Y' pattern across two sentences -- state Y directly",
                          "text": a + " " + b})
    return hits


# --- em_dash_cluster (semantic, document-level) ---------------------------
# The three entity forms below also count toward the em-dash cluster total --
# an em dash written as `&mdash;` is still an em dash, and counting only the
# plain character would let entity-encoding sidestep the threshold entirely.
_ENTITY_EM_DASH_RE = re.compile(r"&mdash;|&#0*8212;|&#[xX]0*2014;")


def check_em_dash_cluster(text):
    """Reports the raw count unconditionally -- whether that count is
    enough to actually TRIGGER this check (and whether triggering it
    denies the write) is this check's own configured {threshold, action}
    now, applied centrally in blocking_semantic_flags, the same as every
    other check. `occurrences` carries the count so a document with 6 em
    dashes weighs six times what one with 1 does against the threshold,
    not the same -- see core.flags.flag_weight."""
    count = text.count("—") + len(_ENTITY_EM_DASH_RE.findall(text))
    if count == 0:
        return []
    return [{"count": count, "occurrences": count, "rule": "slopwatch.em_dash_cluster",
              "auto_fix": False, "note": f"{count} em dash(es) in this document"}]


# --- entity_encoded_punctuation (mechanical) -- ported from deslopper (MIT) -
_ENTITY_SECTION_RE = re.compile(r"&sect;|&#0*167;|&#[xX]0*[aA]7;")
_ENTITY_MIDDOT_RE = re.compile(
    r"&middot;|&centerdot;|&CenterDot;|&bull;|&bullet;|"
    r"&#0*183;|&#0*8226;|&#[xX]0*[bB]7;|&#[xX]0*2022;")


def check_entity_encoded_punctuation(sentence):
    hits = []
    for m in _ENTITY_EM_DASH_RE.finditer(sentence):
        hits.append({"phrase": m.group(0), "rule": "slopwatch.entity_encoded_punctuation",
                      "auto_fix": True,
                      "note": "em dash written as an HTML entity -- write the character plainly"})
    for m in _ENTITY_SECTION_RE.finditer(sentence):
        hits.append({"phrase": m.group(0), "rule": "slopwatch.entity_encoded_punctuation",
                      "auto_fix": True,
                      "note": "section sign written as an HTML entity -- write 'section'"})
    for m in _ENTITY_MIDDOT_RE.finditer(sentence):
        hits.append({"phrase": m.group(0), "rule": "slopwatch.entity_encoded_punctuation",
                      "auto_fix": True,
                      "note": "middle dot or bullet written as an HTML entity -- "
                              "join the items with a comma or plain words"})
    return hits


# --- bold_bullet_lead / id_label_lead (semantic) -- ported from deslopper ---
# Both operate on a full list-item line (marker included), not a tokenized
# sentence, since they need to see the marker itself -- called directly from
# the list_item branch of lint_and_gate's block loop, not the per-sentence loop.
_BOLD_BULLET_RE = re.compile(r"^(\s*(?:[-*+]|\d+\.)\s+)(\*\*|__)(.+?)\2(.*)$")
_BOLD_TERMINAL_RE = re.compile(r"[.:?!]$")
_NON_SPACE_RE = re.compile(r"\S")


def check_bold_bullet_lead(list_item_line):
    m = _BOLD_BULLET_RE.match(list_item_line)
    if not m:
        return []
    _marker, _delim, bold_text, rest = m.groups()
    if _BOLD_TERMINAL_RE.search(bold_text):
        return []  # a bold run ending in punctuation reads as a real sentence, not a tag
    if not _NON_SPACE_RE.search(rest):
        return []
    return [{"phrase": bold_text, "rule": "slopwatch.bold_bullet_lead", "auto_fix": False,
              "note": "bolded bullet lead -- reserve bold for a rare callout, not a per-item label"}]


_ID_LABEL_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+)(\*\*|__)?([A-Z]{1,4}-?\d{1,2}(?:\.\d{1,2})?)(.*)$")
# What has to follow an id label for it to read as a tag on the item rather
# than the subject of the sentence: an optional separator, then item text
# that opens capitalized.
_ID_LABEL_TAIL_RE = re.compile(r"[:).]?\s+(?:[-–—]\s*)?[*_\"']?[A-Z]")


def check_id_label_lead(list_item_line):
    m = _ID_LABEL_RE.match(list_item_line)
    if not m:
        return []
    _marker, bold, label, rest = m.groups()
    if bold:
        if not rest.startswith(bold):
            return []  # a bold run that doesn't close on the label names a real thing, not a tag
        rest = rest[len(bold):]
    if _ID_LABEL_TAIL_RE.match(rest):
        return [{"phrase": label, "rule": "slopwatch.id_label_lead", "auto_fix": False,
                  "note": "id-tagged list item -- number the list plainly instead"}]
    return []


# --- not_just_x_but_y (semantic) -- ported from deslopper (MIT) ------------
_NOT_JUST_BUT_RE = re.compile(r"\bnot just\b[^.?!]{0,60}?\bbut\b", re.IGNORECASE)


def check_not_just_but(sentence):
    m = _NOT_JUST_BUT_RE.search(sentence)
    if not m:
        return []
    return [{"phrase": m.group(0), "rule": "slopwatch.not_just_x_but_y", "auto_fix": False,
              "note": "\"not just X but Y\" padding -- make the point once"}]


# --- vague_intensifier (semantic) -- ported from deslopper (MIT) -----------
VAGUE_INTENSIFIERS = {"very", "really", "quite", "significantly"}
_VAGUE_INTENSIFIER_RE = re.compile(r"\b(" + "|".join(VAGUE_INTENSIFIERS) + r")\b", re.IGNORECASE)


def check_vague_intensifier(sentence):
    return [{"word": m.group(1), "rule": "slopwatch.vague_intensifier", "auto_fix": False,
              "note": "vague intensifier with no number behind it -- say how much, or cut it"}
            for m in _VAGUE_INTENSIFIER_RE.finditer(sentence)]


# --- emoji_in_prose (mechanical) -- ported from deslopper (MIT) ------------
_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF☀-➿✅✔☑✓⭐✨]")


def check_emoji(sentence):
    return [{"phrase": m.group(0), "rule": "slopwatch.emoji_in_prose", "auto_fix": True,
              "note": "emoji or decorative checkmark in body text"}
            for m in _EMOJI_RE.finditer(sentence)]


# --- marketing_adjective / filler_verb (semantic) -- ported from deslopper -
MARKETING_ADJECTIVES = {"seamless", "robust", "powerful", "cutting-edge", "comprehensive",
                         "vibrant", "elegant", "intuitive", "game-changing"}


def check_marketing_adjective(sentence, extra=()):
    words = MARKETING_ADJECTIVES | set(extra)
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE)
    return [{"word": m.group(1), "rule": "slopwatch.marketing_adjective", "auto_fix": False,
              "note": "marketing adjective -- say what is actually true instead"}
            for m in pattern.finditer(sentence)]


FILLER_VERB_PATTERNS = ["surfaces", "leverages?", "enables?", "powers", "facilitates?",
                         "utili[sz]es?", "fosters?", "drives", "unlocks?", "delivers?",
                         "streamlines?", "empowers?", "showcases?"]
# "delve" alone is a plain, approved verb ("delve into the archive" is fine
# English) -- only the "delve into/deeper" collocation reads as filler,
# matching deslopper's own case-sensitive exception for this one word.
_FILLER_VERB_DELVE_RE = re.compile(r"\bdelves?\b(?=\s+(?:into|deeper))", re.IGNORECASE)


def check_filler_verb(sentence, extra=()):
    # extra terms are literal words/phrases (re.escape'd), unlike the
    # built-in patterns above which bake in their own pluralization --
    # a project registering "showcase" doesn't need to know regex.
    patterns = list(FILLER_VERB_PATTERNS) + [re.escape(t) for t in extra]
    filler_re = re.compile(r"\b(" + "|".join(patterns) + r")\b", re.IGNORECASE)
    hits = [{"word": m.group(1), "rule": "slopwatch.filler_verb", "auto_fix": False,
              "note": "filler verb -- use a plain verb, or cut"}
            for m in filler_re.finditer(sentence)]
    hits.extend({"word": m.group(0), "rule": "slopwatch.filler_verb", "auto_fix": False,
                  "note": "filler verb -- use a plain verb, or cut"}
                for m in _FILLER_VERB_DELVE_RE.finditer(sentence))
    return hits


# --- marketing_cliche / solicit_criticism (semantic) -- ported from --------
# piyushbhattadforapps/pseo-quality-gate (MIT)
MARKETING_CLICHES = ["amazing", "breathtaking", "stunning", "must-visit", "must visit",
                      "must-see", "must see", "perfect for everyone", "hidden gem",
                      "top destination", "ultimate guide", "complete guide", "world-class",
                      "world class", "in this article we will", "in this guide we will",
                      "let's dive in", "without further ado", "look no further",
                      "you've come to the right place", "we've got you covered"]


# --- identifier_in_prose (semantic) ----------------------------------------
# snake_case in prose is an internal name shown to a reader who was never
# told it exists -- the register drift a manual UI audit kept catching by
# eye (a threshold rendered as block_flag_count_threshold beside a
# sentence written in plain words). An identifier belongs in prose only
# as marked code, and inline code is stripped before checks run, so the
# fix IS the escape hatch: backtick it.
_IDENTIFIER_RE = re.compile(r"\b_{0,2}[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+_{0,2}\b")


def check_identifier_in_prose(sentence):
    return [{"word": m.group(0), "rule": "slopwatch.identifier_in_prose",
              "auto_fix": False,
              "note": "internal identifier in prose -- name it in words, "
                      "or mark it as code"}
            for m in _IDENTIFIER_RE.finditer(sentence)]


# --- terminology (semantic) -- one word, one meaning -----------------------
# ASD-STE100's cardinal principle, finally implemented as a RULE rather
# than only shipped as a dictionary: a project names its canonical terms
# by banning their synonyms. Each term on the `terminology` list is a
# BANNED synonym; its note says what to write instead, and travels into
# the flag so a deny states the fix, not only the fault. The built-in
# list is EMPTY on purpose -- a lexicon is project-specific by nature
# (this repo bans "shipped" in favor of "built-in"; yours won't) -- so
# the check is inert until a project registers words or attaches a pack.


def check_terminology(sentence, lexicon=None):
    if not lexicon:
        return []
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in
                           sorted(lexicon, key=len, reverse=True)) + r")\b",
        re.IGNORECASE)
    hits = []
    for m in pattern.finditer(sentence):
        note = (lexicon.get(m.group(1).lower()) or {}).get("note") or ""
        hits.append({"word": m.group(1), "rule": "slopwatch.terminology",
                      "auto_fix": False,
                      "note": note or "banned by this project's lexicon -- "
                                       "one word, one meaning"})
    return hits


# Every check that's fundamentally "match text against a list of words or
# phrases", declared as a TERM LIST -- the one shared shape every ruleset
# now uses (see core/terms.py). All five are DENY lists: the terms are the
# thing being flagged, the opposite polarity from ste100's project
# vocabulary, which is an ALLOW list. Both are term lists; polarity is a
# field, not a different concept with its own name and its own API.
#
# accepts_packs is True even though no pack targets these today. A pack
# declares which (ruleset, list) it feeds, so a corporate banned-phrase
# pack aimed at ("slopwatch", "marketing_cliche") would work with no code
# change here -- leaving the door open costs nothing and is the difference
# between a real abstraction and one shaped around its first user.
# Word lists for two structural checks. Up here with the other
# list-shaped constants because TERM_LISTS below reads them, and a
# project extends both through the Vocabulary page -- this is the
# layer that decays as models change, so it is meant to be edited.
COPULA_DODGES = ["serves as", "stands as", "functions as", "acts as",
                  "boasts", "features a", "marks a", "represents a",
                  "emerged as", "positioned as"]


SECTION_TEMPLATES = ["despite its success", "despite these challenges",
                     "challenges and future", "future prospects",
                     "in conclusion", "looking ahead", "the road ahead",
                     "key takeaways", "final thoughts", "in summary"]


TERM_LISTS = {
    "weasel_attribution": {
        "content_kind": "phrase",
        # Which CHECK this list feeds. Declared, not inferred from the
        # id: ste100's three lists all feed one check, so any UI that
        # paired them by name would show that check as having no
        # vocabulary at all. A list naming its check is fine (both are
        # internal to this ruleset); a PACK naming its consumer was not,
        # because a pack is shared content -- see core/glossary_packs.
        "feeds": "weasel_attribution",
        "label": "Weasel attributions",
        "description": "Vague appeals to authority with no named source.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": WEASEL_PHRASES,
    },
    "marketing_adjective": {
        "content_kind": "word",
        "feeds": "marketing_adjective",
        "label": "Marketing adjectives",
        "description": "Promotional adjectives that assert quality instead of showing it.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": MARKETING_ADJECTIVES,
    },
    "filler_verb": {
        "content_kind": "pattern",
        "feeds": "filler_verb",
        "label": "Filler verbs",
        "description": "Verb phrases that add length without adding meaning.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": FILLER_VERB_PATTERNS,
    },
    "marketing_cliche": {
        "content_kind": "phrase",
        "feeds": "marketing_cliche",
        "label": "Marketing cliches",
        "description": "Stock phrases that signal generated copy.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": MARKETING_CLICHES,
    },
    "stock_adverb": {
        "content_kind": "word",
        "feeds": "stock_adverb",
        "label": "Stock adverbs",
        "description": "Filler adverbs safe to delete outright (auto-fixed).",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": STOCK_ADVERBS,
    },
    "copula_avoidance": {
        "content_kind": "phrase",
        "feeds": "copula_avoidance",
        "label": "Copula dodges",
        "description": "Phrases used where \"is\" would do: serves as, "
                        "boasts, functions as. Extend it as new ones appear "
                        "-- this layer is the one that decays as models "
                        "change, so it is meant to be edited.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": COPULA_DODGES,
    },
    "section_template": {
        "content_kind": "phrase",
        "feeds": "section_template",
        "label": "Stock section skeletons",
        "description": "Section openings that signal a template rather than "
                        "a point: \"Despite its success\", \"Looking ahead\".",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": SECTION_TEMPLATES,
    },
    "terminology": {
        "content_kind": "word",
        "feeds": "terminology",
        "label": "Project lexicon",
        "description": "Banned synonyms of this project's canonical terms "
                        "-- one word, one meaning. A term's note names the "
                        "word to use instead.",
        "polarity": "deny", "accepts_packs": True,
        # Empty on purpose: a lexicon is project-specific by nature.
        "built_ins": (),
    },
}


def check_marketing_cliche(sentence, extra=()):
    phrases = list(MARKETING_CLICHES) + list(extra)
    pattern = re.compile(r"\b(" + "|".join(re.escape(p) for p in phrases) + r")\b", re.IGNORECASE)
    return [{"phrase": m.group(1), "rule": "slopwatch.marketing_cliche", "auto_fix": False,
              "note": "marketing cliche -- say the specific thing instead"}
            for m in pattern.finditer(sentence)]


_SOLICIT_CRITICISM_RES = [
    re.compile(r"\broast it\b", re.IGNORECASE),
    re.compile(r"\btell me what\W*s wrong\b", re.IGNORECASE),
    re.compile(r"\bhappy to hear what\W*s off\b", re.IGNORECASE),
    re.compile(r"\blet me know how it could be improved\b", re.IGNORECASE),
    re.compile(r"\bwould love your feedback on this\b", re.IGNORECASE),
]


def check_solicit_criticism(sentence):
    hits = []
    for rx in _SOLICIT_CRITICISM_RES:
        m = rx.search(sentence)
        if m:
            hits.append({"phrase": m.group(0), "rule": "slopwatch.solicit_criticism",
                          "auto_fix": False, "note": "fake-humility feedback solicitation -- cut it"})
    return hits


# --- unearned_profundity / dramatic_fragmentation (semantic) --------------
# Own words: reimplementations of a documented CONCEPT (see module
# docstring), not ports of code or text from either source.
UNEARNED_PROFUNDITY_PHRASES = ["something shifted", "everything changed",
                                "nothing would ever be the same",
                                "but here's the thing", "and then it hit me"]
_UNEARNED_PROFUNDITY_RE = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in UNEARNED_PROFUNDITY_PHRASES) + r")\.?$",
    re.IGNORECASE)


def check_unearned_profundity(sentence):
    stripped = sentence.strip()
    if _UNEARNED_PROFUNDITY_RE.match(stripped):
        return [{"phrase": stripped, "rule": "slopwatch.unearned_profundity", "auto_fix": False,
                  "note": "dramatic turning-point sentence with nothing concrete behind it -- "
                          "name the actual event, or cut it"}]
    return []


DRAMATIC_FRAGMENTS = ["that's it", "that's the whole thing", "that's the whole point",
                       "that's the whole story", "full stop", "simple as that"]
_DRAMATIC_FRAGMENT_RE = re.compile(
    r"^(?:" + "|".join(re.escape(p) for p in DRAMATIC_FRAGMENTS) + r")\.?$", re.IGNORECASE)


def check_dramatic_fragmentation(sentence):
    stripped = sentence.strip()
    if _DRAMATIC_FRAGMENT_RE.match(stripped):
        return [{"phrase": stripped, "rule": "slopwatch.dramatic_fragmentation", "auto_fix": False,
                  "note": "dramatic one-line fragment -- cut it, the preceding "
                          "sentence already made the point"}]
    return []


# --- canned_question_answer / negative_listing (semantic, adjacent-sentence)
# Own words, same status as above -- operate on the full sentence list like
# check_binary_contrast does.
_SHORT_QUESTION_RE = re.compile(r"^\S+(?:\s+\S+){0,4}\?$")
_CANNED_ANSWER_OPENER_RE = re.compile(r"^(it|this|the|that|why|because)\b", re.IGNORECASE)


def check_canned_question_answer(sentences):
    hits = []
    for i in range(len(sentences) - 1):
        a, b = sentences[i].strip(), sentences[i + 1].strip()
        if _SHORT_QUESTION_RE.match(a) and _CANNED_ANSWER_OPENER_RE.match(b):
            hits.append({"phrase": a, "rule": "slopwatch.canned_question_answer", "auto_fix": False,
                          "note": "rhetorical question with a canned answer -- "
                                  "collapse into one direct statement",
                          "text": a + " " + b})
    return hits


_NEGATIVE_LEAD_RE = re.compile(r"^not\b", re.IGNORECASE)


def check_negative_listing(sentences):
    hits = []
    i = 0
    while i < len(sentences) - 1:
        a, b = sentences[i].strip(), sentences[i + 1].strip()
        if _NEGATIVE_LEAD_RE.match(a) and _NEGATIVE_LEAD_RE.match(b):
            hits.append({"phrase": a, "rule": "slopwatch.negative_listing", "auto_fix": False,
                          "note": "\"Not X. Not Y.\" listing -- state the point once",
                          "text": a + " " + b})
            i += 2
            continue
        i += 1
    return hits


_DEDUP_EXCLUDE_KINDS = {"em_dash_cluster"}  # document-level, one flag total -- nothing to collapse


# Every check's declared identity -- see core/checks.py. Every check
# defaults to threshold=1/action="warn" (fires, and is visible, on its
# first occurrence, but never denies alone) except em_dash_cluster,
# which denies alone once 4 or more em dashes appear in one document.
# bold_bullet_lead/id_label_lead operate on the raw list-item line
# (marker included), not a tokenized sentence -- LINE is the closest
# fit until a future run-loop unification adds a dedicated unit for that.

# --- Structural tells -----------------------------------------------------
# Added from Wikipedia's "Signs of AI writing" (see NOTICE), which is the
# community-maintained catalogue of what editors actually flag, and from
# the observation that survives every lexical scrub: you can swap every
# banned word and the text still reads as generated, because the paragraph
# shape, the sentence rhythm and the rhetorical moves are the tell. This
# project measured that directly -- a gated arm reached ZERO flags on 11
# enforced checks while the 11 held-out checks did not move -- so these
# aim at the residue rather than adding more word lists.

_RULE_OF_THREE_RE = re.compile(
    r"\b(\w+ing)\b,\s+(\w+ing)\b,?\s+and\s+(\w+ing)\b", re.I)
_TRIPLE_ADJ_RE = re.compile(
    r"\b(\w+),\s+(\w+),\s+and\s+(\w+)\b(?=\s|[.,;:])")


def check_rule_of_three(sentence):
    """Three parallel items in a series, the shape Wikipedia calls the
    rule of three. A human writes triads sometimes; a model reaches for
    one whenever it needs to sound complete, which is why density matters
    more than any single instance."""
    m = _RULE_OF_THREE_RE.search(sentence)
    if not m:
        return []
    return [{"phrase": m.group(0)[:60], "rule": "slopwatch.rule_of_three",
              "auto_fix": False,
              "note": "three parallel -ing items -- cut to the one that carries "
                      "information, or make them separate claims"}]


def check_copula_avoidance(sentence, extra=()):
    """"X serves as a Y" where "X is a Y" was available. Wikipedia lists
    this under syntax rather than vocabulary: the model systematically
    avoids the copula, which inflates register without adding meaning."""
    low = sentence.lower()
    for phrase in list(COPULA_DODGES) + list(extra):
        if phrase in low:
            return [{"phrase": phrase, "rule": "slopwatch.copula_avoidance",
                      "auto_fix": False,
                      "note": "says \"is\" the long way round -- use the plain verb"}]
    return []


_PARTICIPIAL_TAIL_RE = re.compile(
    r",\s+(highlighting|underscoring|emphasizing|showcasing|reflecting|"
    r"demonstrating|illustrating|signaling|marking|ensuring|allowing|"
    r"enabling|providing|offering|making it|solidifying|cementing)\b", re.I)


def check_participial_tail(sentence):
    """A comment clause bolted to the end of a sentence, offering
    significance instead of information: "..., underscoring the
    importance of X". Wikipedia files this under superficial analysis."""
    m = _PARTICIPIAL_TAIL_RE.search(sentence)
    if not m:
        return []
    return [{"phrase": m.group(0).strip()[:50],
              "rule": "slopwatch.participial_tail", "auto_fix": False,
              "note": "a significance clause bolted to the end -- delete it, or "
                      "make it a claim with something behind it"}]


def check_section_template(sentence, extra=()):
    """The stock section skeleton: a challenges paragraph, then a
    forward-looking close. Wikipedia names it as one of the most
    reliable article-level tells."""
    low = sentence.lower().lstrip("#* -")
    for phrase in list(SECTION_TEMPLATES) + list(extra):
        if low.startswith(phrase) or f" {phrase}" in low:
            return [{"phrase": phrase, "rule": "slopwatch.section_template",
                      "auto_fix": False,
                      "note": "stock section skeleton -- say the specific thing "
                              "this section is for, or drop the section"}]
    return []


_BOLD_SPAN_RE = re.compile(r"\*\*[^*\n]{1,80}\*\*")


def check_bold_density(text):
    """Bold used as emphasis throughout the body, not for the rare
    callout. Counted per document because one bold span says nothing and
    fifteen is a fingerprint."""
    count = len(_BOLD_SPAN_RE.findall(text))
    if count == 0:
        return []
    return [{"count": count, "occurrences": count,
              "rule": "slopwatch.bold_density", "auto_fix": False,
              "note": f"{count} bold span(s) in this document -- reserve bold for "
                      f"a rare callout"}]


_THEMATIC_BREAK_RE = re.compile(r"^\s*(?:---+|\*\*\*+|___+)\s*$", re.M)


def check_thematic_break(text):
    """Horizontal rules dropped between sections as visual filler.
    Excludes a YAML front-matter fence, which is structural."""
    body = text
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end != -1:
            body = body[end + 4:]
    count = len(_THEMATIC_BREAK_RE.findall(body))
    if count == 0:
        return []
    return [{"count": count, "occurrences": count,
              "rule": "slopwatch.thematic_break", "auto_fix": False,
              "note": f"{count} horizontal rule(s) -- headings already separate "
                      f"sections"}]


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
_SMALL_WORDS = {"a", "an", "the", "and", "or", "but", "for", "of", "in", "on",
                "to", "with", "at", "by", "from", "as", "is", "it"}


def check_title_case_heading(text):
    """Headings Capitalised Like This. Wikipedia lists title case as a
    styling anomaly; it is also the default a model reaches for."""
    for _level, heading in _HEADING_RE.findall(text):
        words = [w for w in re.findall(r"[A-Za-z][\w'-]*", heading)]
        if len(words) < 3:
            continue
        candidates = [w for w in words[1:] if w.lower() not in _SMALL_WORDS]
        if len(candidates) < 2:
            continue
        if all(w[0].isupper() and not w.isupper() for w in candidates):
            return [{"phrase": heading[:60],
                      "rule": "slopwatch.title_case_heading", "auto_fix": False,
                      "note": "title case heading -- use sentence case"}]
    return []


_AI_REMNANT_RE = re.compile(
    r"oaicite|\[cite:\s*\d+\]|grok_card|contentReference|"
    r"as an ai language model|i cannot browse|my knowledge cutoff|"
    r"as of my last update|\[INSERT [A-Z ]+\]|\bTODO: (?:fill|add) (?:in|the)\b",
    re.I)


def check_ai_markup_remnant(text):
    """Scaffolding that leaked from the generator itself: citation stubs,
    tool markup, refusal boilerplate, unfilled placeholders. Unlike every
    other check here this one has no false-positive story worth arguing
    -- the text is simply not finished."""
    m = _AI_REMNANT_RE.search(text)
    if not m:
        return []
    return [{"phrase": m.group(0)[:50], "rule": "slopwatch.ai_markup_remnant",
              "auto_fix": False,
              "note": "generator scaffolding left in the text -- this was never "
                      "finished or read"}]


def check_paragraph_uniformity(text):
    """Paragraphs all the same size. The most purely structural tell in
    this ruleset: human prose varies its paragraph length with what each
    one has to do, and generated prose tends to a uniform block. Reports
    only when there are enough paragraphs for the number to mean
    something, and when they are long enough that uniformity is not just
    an artifact of a short list."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    paras = [p for p in paras
             if not p.lstrip().startswith(("#", "-", "*", ">", "|", "```"))]
    lengths = [len(p.split()) for p in paras]
    lengths = [n for n in lengths if n >= 20]
    if len(lengths) < 4:
        return []
    mean = sum(lengths) / len(lengths)
    if mean <= 0:
        return []
    spread = statistics.stdev(lengths) / mean
    if spread >= 0.35:
        return []
    return [{"phrase": f"{len(lengths)} paragraphs, spread {spread:.2f}",
              "rule": "slopwatch.paragraph_uniformity", "auto_fix": False,
              "note": f"{len(lengths)} body paragraphs nearly identical in length "
                      f"-- vary them with what each one actually has to do"}]


CHECKS_TABLE = {
    "filler_opener": _checks.Check(
        id="filler_opener", unit=_checks.Unit.SENTENCE, fn=check_filler_opener,
        catches="Throat-clearing openers: \"needless to say\", \"at the end of the day\"",
        instead="state the point directly from the first sentence"),
    "stock_adverb": _checks.Check(
        id="stock_adverb", unit=_checks.Unit.SENTENCE, fn=check_stock_adverb,
        catches="Standalone filler adverbs: undoubtedly, arguably, notably, importantly, ultimately",
        instead="most add nothing; cut them unless one is carrying real emphasis",
        terms_list="stock_adverb", classify="mechanical"),
    "colon_reveal": _checks.Check(
        id="colon_reveal", unit=_checks.Unit.SENTENCE, fn=check_colon_reveal,
        catches="Short buildup, then a reveal: \"The best part: it learns.\"",
        instead="state it as a plain sentence"),
    "binary_contrast": _checks.Check(
        id="binary_contrast", unit=_checks.Unit.SENTENCES, fn=check_binary_contrast,
        catches="The \"it's not X, it's Y\" construction",
        instead="just state Y"),
    # Warns, and every other check in this ruleset warns with it. That is
    # the rule for slopwatch, not an exception for this check: everything
    # here detects a TELL, a surface correlate of empty writing, never
    # emptiness itself. Text that avoids all 22 constructions and says
    # nothing still passes. Blocking on a correlate hands a model a tight
    # loop to iterate against until the checker goes quiet, which selects
    # for text that is equally vacuous and clean -- the proxy gets
    # optimized, the writing does not improve. A warning carries the same
    # information to a person who can judge it, without the loop.
    # codewatch's swallowed_exception blocks precisely because a bare
    # except-then-pass is a DEFECT rather than a tell: it is wrong on its
    # own terms, whatever the surrounding prose reads like.
    "rule_of_three": _checks.Check(
        id="rule_of_three", unit=_checks.Unit.SENTENCE, fn=check_rule_of_three,
        catches="Three parallel -ing items in a series",
        instead="keep the one that carries information"),
    "copula_avoidance": _checks.Check(
        id="copula_avoidance", unit=_checks.Unit.SENTENCE, fn=check_copula_avoidance,
        catches="Saying \"is\" the long way: serves as, boasts, functions as",
        instead="use the plain verb"),
    "participial_tail": _checks.Check(
        id="participial_tail", unit=_checks.Unit.SENTENCE, fn=check_participial_tail,
        catches="A significance clause bolted to a sentence: \", underscoring the...\"",
        instead="delete it, or make it a claim with something behind it"),
    "section_template": _checks.Check(
        id="section_template", unit=_checks.Unit.SENTENCE, fn=check_section_template,
        catches="Stock section skeleton: \"Despite its success\", \"Looking ahead\"",
        instead="name the specific thing the section is for"),
    "bold_density": _checks.Check(
        id="bold_density", unit=_checks.Unit.DOCUMENT, fn=check_bold_density,
        catches="Bold used as body emphasis throughout",
        instead="reserve bold for a rare callout",
        default_threshold=8, default_action="warn", dedup=False),
    "thematic_break": _checks.Check(
        id="thematic_break", unit=_checks.Unit.DOCUMENT, fn=check_thematic_break,
        catches="Horizontal rules dropped between sections",
        instead="headings already separate sections",
        default_threshold=2, default_action="warn", dedup=False),
    "title_case_heading": _checks.Check(
        id="title_case_heading", unit=_checks.Unit.DOCUMENT, fn=check_title_case_heading,
        catches="Headings Capitalised Like This",
        instead="sentence case"),
    "ai_markup_remnant": _checks.Check(
        id="ai_markup_remnant", unit=_checks.Unit.DOCUMENT, fn=check_ai_markup_remnant,
        catches="Generator scaffolding left in: oaicite, [cite: 1], placeholders",
        instead="finish the text and read it"),
    "paragraph_uniformity": _checks.Check(
        id="paragraph_uniformity", unit=_checks.Unit.DOCUMENT, fn=check_paragraph_uniformity,
        catches="Body paragraphs nearly identical in length",
        instead="vary them with what each paragraph has to do"),
    "em_dash_cluster": _checks.Check(
        id="em_dash_cluster", unit=_checks.Unit.DOCUMENT, fn=check_em_dash_cluster,
        catches="Em dashes clustering in one document",
        instead="most drafts need 0-2; use commas, periods or parentheses for the rest",
        default_threshold=4, default_action="warn", dedup=False),
    "weasel_attribution": _checks.Check(
        id="weasel_attribution", unit=_checks.Unit.SENTENCE, fn=check_weasel_attribution,
        catches="Unnamed authority: \"studies show\", \"experts agree\"",
        instead="name the actual source, or cut the claim",
        terms_list="weasel_attribution"),
    "entity_encoded_punctuation": _checks.Check(
        id="entity_encoded_punctuation", unit=_checks.Unit.SENTENCE, fn=check_entity_encoded_punctuation,
        catches="An em dash, section sign or middle dot written as an HTML entity",
        instead="write the plain character", classify="mechanical"),
    "bold_bullet_lead": _checks.Check(
        id="bold_bullet_lead", unit=_checks.Unit.LINE, fn=check_bold_bullet_lead,
        catches="A bolded word opening a list item as a per-item tag",
        instead="reserve bold for a rare callout"),
    "id_label_lead": _checks.Check(
        id="id_label_lead", unit=_checks.Unit.LINE, fn=check_id_label_lead,
        catches="Fake ID tags opening list items: \"R-1.\", \"US-01\"",
        instead="number the list plainly"),
    "not_just_x_but_y": _checks.Check(
        id="not_just_x_but_y", unit=_checks.Unit.SENTENCE, fn=check_not_just_but,
        catches="The \"not just X but Y\" construction",
        instead="make the point once"),
    "vague_intensifier": _checks.Check(
        id="vague_intensifier", unit=_checks.Unit.SENTENCE, fn=check_vague_intensifier,
        catches="Vague intensifiers with no number behind them: very, really, quite, significantly",
        instead="say how much, or cut the word"),
    "emoji_in_prose": _checks.Check(
        id="emoji_in_prose", unit=_checks.Unit.SENTENCE, fn=check_emoji,
        catches="Emoji or decorative checkmarks in body text",
        instead="cut them", classify="mechanical"),
    "marketing_adjective": _checks.Check(
        id="marketing_adjective", unit=_checks.Unit.SENTENCE, fn=check_marketing_adjective,
        catches="Marketing adjectives: seamless, robust, cutting-edge",
        instead="say what is actually true",
        terms_list="marketing_adjective"),
    "filler_verb": _checks.Check(
        id="filler_verb", unit=_checks.Unit.SENTENCE, fn=check_filler_verb,
        catches="Filler verbs: leverages, facilitates, unlocks",
        instead="use a plain verb, or cut the sentence",
        terms_list="filler_verb"),
    "marketing_cliche": _checks.Check(
        id="marketing_cliche", unit=_checks.Unit.SENTENCE, fn=check_marketing_cliche,
        catches="Marketing cliches: \"hidden gem\", \"let's dive in\"",
        instead="say the specific thing",
        terms_list="marketing_cliche"),
    "solicit_criticism": _checks.Check(
        id="solicit_criticism", unit=_checks.Unit.SENTENCE, fn=check_solicit_criticism,
        catches="Fake-humility feedback requests: \"would love your feedback on this\"",
        instead="cut them"),
    "unearned_profundity": _checks.Check(
        id="unearned_profundity", unit=_checks.Unit.SENTENCE, fn=check_unearned_profundity,
        catches="Dramatic turning points with nothing concrete behind them: \"Everything changed.\"",
        instead="name the actual event, or cut it"),
    "dramatic_fragmentation": _checks.Check(
        id="dramatic_fragmentation", unit=_checks.Unit.SENTENCE, fn=check_dramatic_fragmentation,
        catches="One-line dramatic fragments: \"That's it. That's the whole thing.\"",
        instead="cut them, the preceding sentence already made the point"),
    "canned_question_answer": _checks.Check(
        id="canned_question_answer", unit=_checks.Unit.SENTENCES, fn=check_canned_question_answer,
        catches="A short rhetorical question with a canned answer",
        instead="collapse into one direct statement"),
    "negative_listing": _checks.Check(
        id="negative_listing", unit=_checks.Unit.SENTENCES, fn=check_negative_listing,
        catches="The \"Not X. Not Y.\" listing construction",
        instead="state the point once"),
    "terminology": _checks.Check(
        id="terminology", unit=_checks.Unit.SENTENCE, fn=check_terminology,
        catches="A banned synonym of one of this project's canonical terms, per its declared lexicon",
        instead="one word, one meaning: use the canonical term the word's own note names",
        terms_list="terminology", terms_arg="lexicon", terms_shape="with_notes"),
    "identifier_in_prose": _checks.Check(
        id="identifier_in_prose", unit=_checks.Unit.SENTENCE, fn=check_identifier_in_prose,
        catches="A snake_case identifier written as plain prose",
        instead="name it in words, or mark it as inline code"),
}

# Derived, not hand-typed -- kept as a plain module attribute since
# test_lint.py and other callers reference it directly as the set of this
# ruleset's check ids.
ALL_CHECK_IDS = frozenset(CHECKS_TABLE)


def _lint_and_gate_legacy(text, context=None, file_path=None):
    """The original hand-written per-check dispatch loop, kept permanently
    as the differential-test baseline for lint_and_gate's generic-dispatch
    replacement below -- see rulesets/codewatch/test_lint.py's
    DispatcherMigrationTests for the pattern this mirrors. Not a dead copy:
    TestSlopwatchDispatcherMigration runs both against a real corpus and
    asserts byte-identical output."""
    sentences = []
    mechanical = []
    semantic = []

    # Fetched once per call, not once per sentence -- same "read fresh but
    # don't re-read per sentence" discipline _enabled_check_ids()/
    # apply_mechanical_fixes() already use.
    extra_stock_adverbs = _custom_terms("stock_adverb", file_path)
    extra_weasel = _custom_terms("weasel_attribution", file_path)
    extra_marketing_adjective = _custom_terms("marketing_adjective", file_path)
    extra_filler_verb = _custom_terms("filler_verb", file_path)
    extra_marketing_cliche = _custom_terms("marketing_cliche", file_path)
    lexicon = _lexicon_terms(file_path)

    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            continue
        elif block_type == "header":
            block_text = HEADER_RE.sub("", content).strip()
        elif block_type == "list_item":
            m = LIST_ITEM_RE.match(content)
            block_text = m.group(2) if m else content
            # bold_bullet_lead/id_label_lead need the marker itself, so they
            # run against the raw line here rather than the per-sentence loop.
            for v in check_bold_bullet_lead(content):
                semantic.append({"kind": "bold_bullet_lead", "label": _label(v), "detail": v, "text": content})
            for v in check_id_label_lead(content):
                semantic.append({"kind": "id_label_lead", "label": _label(v), "detail": v, "text": content})
        else:  # paragraph
            block_text = content
        block_text = re.sub(r"`[^`\n]+`", " ", block_text)  # inline code untouchable
        sentences.extend(tokenize_sentences(block_text))

    for s in sentences:
        for v in check_filler_opener(s):
            semantic.append({"kind": "filler_opener", "label": _label(v), "detail": v, "text": s})
        for v in check_stock_adverb(s, extra_stock_adverbs):
            mechanical.append({"kind": "stock_adverb", "label": _label(v), "detail": v, "text": s})
        for v in check_colon_reveal(s):
            semantic.append({"kind": "colon_reveal", "label": _label(v), "detail": v, "text": s})
        for v in check_weasel_attribution(s, extra_weasel):
            semantic.append({"kind": "weasel_attribution", "label": _label(v), "detail": v, "text": s})
        for v in check_entity_encoded_punctuation(s):
            mechanical.append({"kind": "entity_encoded_punctuation", "label": _label(v), "detail": v, "text": s})
        for v in check_not_just_but(s):
            semantic.append({"kind": "not_just_x_but_y", "label": _label(v), "detail": v, "text": s})
        for v in check_vague_intensifier(s):
            semantic.append({"kind": "vague_intensifier", "label": _label(v), "detail": v, "text": s})
        for v in check_emoji(s):
            mechanical.append({"kind": "emoji_in_prose", "label": _label(v), "detail": v, "text": s})
        for v in check_marketing_adjective(s, extra_marketing_adjective):
            semantic.append({"kind": "marketing_adjective", "label": _label(v), "detail": v, "text": s})
        for v in check_filler_verb(s, extra_filler_verb):
            semantic.append({"kind": "filler_verb", "label": _label(v), "detail": v, "text": s})
        for v in check_marketing_cliche(s, extra_marketing_cliche):
            semantic.append({"kind": "marketing_cliche", "label": _label(v), "detail": v, "text": s})
        for v in check_solicit_criticism(s):
            semantic.append({"kind": "solicit_criticism", "label": _label(v), "detail": v, "text": s})
        for v in check_unearned_profundity(s):
            semantic.append({"kind": "unearned_profundity", "label": _label(v), "detail": v, "text": s})
        for v in check_dramatic_fragmentation(s):
            semantic.append({"kind": "dramatic_fragmentation", "label": _label(v), "detail": v, "text": s})
        for v in check_terminology(s, lexicon):
            semantic.append({"kind": "terminology", "label": _label(v), "detail": v, "text": s})
        for v in check_identifier_in_prose(s):
            semantic.append({"kind": "identifier_in_prose", "label": _label(v), "detail": v, "text": s})

    for v in check_binary_contrast(sentences):
        semantic.append({"kind": "binary_contrast", "label": _label(v), "detail": v, "text": v.get("text")})
    for v in check_canned_question_answer(sentences):
        semantic.append({"kind": "canned_question_answer", "label": _label(v), "detail": v, "text": v.get("text")})
    for v in check_negative_listing(sentences):
        semantic.append({"kind": "negative_listing", "label": _label(v), "detail": v, "text": v.get("text")})

    for v in check_em_dash_cluster(text):
        semantic.append({"kind": "em_dash_cluster", "label": None, "detail": v, "text": None})

    # Every check above runs unconditionally (they're cheap regex/string
    # ops); a disabled check's own flags are dropped here in one place
    # rather than guarding all 20 call sites individually.
    enabled = _enabled_check_ids(file_path)
    mechanical = [f for f in mechanical if f["kind"] in enabled]
    semantic = [f for f in semantic if f["kind"] in enabled]

    mechanical = dedup_flags(mechanical, exclude_kinds=_DEDUP_EXCLUDE_KINDS)
    semantic = dedup_flags(semantic, exclude_kinds=_DEDUP_EXCLUDE_KINDS)

    status = "clean" if not mechanical and not semantic else (
        "semantic_flags" if semantic else "mechanical_violations")

    return {
        "status": status,
        "sentence_count": len(sentences),
        "mechanical_violations": mechanical,
        "semantic_flags": semantic,
    }


def lint_and_gate(text, context=None, file_path=None):
    """Generic-dispatch replacement for _lint_and_gate_legacy above, via
    core.checks.run_checks. CHECKS_TABLE's own declaration order was
    already arranged to match the legacy loop's call order (see the
    comment above CHECKS_TABLE) -- bold_bullet_lead/id_label_lead run
    against list_item_lines (Unit.LINE), the rest against sentences
    (Unit.SENTENCE/SENTENCES) or the whole text (Unit.DOCUMENT); no new
    Unit variant was needed."""
    sentences = []
    list_item_lines = []

    extra_stock_adverbs = _custom_terms("stock_adverb", file_path)
    extra_weasel = _custom_terms("weasel_attribution", file_path)
    extra_marketing_adjective = _custom_terms("marketing_adjective", file_path)
    extra_filler_verb = _custom_terms("filler_verb", file_path)
    extra_marketing_cliche = _custom_terms("marketing_cliche", file_path)
    lexicon = _lexicon_terms(file_path)

    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            continue
        elif block_type == "header":
            block_text = HEADER_RE.sub("", content).strip()
        elif block_type == "list_item":
            m = LIST_ITEM_RE.match(content)
            block_text = m.group(2) if m else content
            list_item_lines.append(content)
        else:  # paragraph
            block_text = content
        block_text = re.sub(r"`[^`\n]+`", " ", block_text)  # inline code untouchable
        sentences.extend(tokenize_sentences(block_text))

    project_root = _paths.find_project_root(__file__)
    # A custom check bound to a vocabulary list via that list's own
    # `feeds` -- see core.custom_checks.extra_by_check_for_custom. Only
    # ever contributes entries for CUSTOM check ids (never one of the
    # literal keys above), so this can never shadow a built-in's own
    # hand-resolved extra.
    custom_extra = _custom_checks.extra_by_check_for_custom(
        project_root, "slopwatch", set(_custom_checks.custom_check_ids(project_root, "slopwatch")),
        _config.effective_term_lists(TERM_LISTS, "slopwatch", project_root), file_path)

    mechanical, semantic = _checks.run_checks(
        effective_checks_table(),
        lines=list_item_lines,
        sentences=sentences,
        text=text,
        extra_by_check={
            "stock_adverb": extra_stock_adverbs,
            "weasel_attribution": extra_weasel,
            "marketing_adjective": extra_marketing_adjective,
            "filler_verb": extra_filler_verb,
            "marketing_cliche": extra_marketing_cliche,
            "copula_avoidance": _custom_terms("copula_avoidance", file_path),
            "section_template": _custom_terms("section_template", file_path),
            "terminology": lexicon,
            **custom_extra,
        },
    )

    # Every check above runs unconditionally (they're cheap regex/string
    # ops); a disabled check's own flags are dropped here in one place
    # rather than guarding all 20 call sites individually.
    enabled = _enabled_check_ids(file_path)
    mechanical = [f for f in mechanical if f["kind"] in enabled]
    semantic = [f for f in semantic if f["kind"] in enabled]

    mechanical = dedup_flags(mechanical, exclude_kinds=_DEDUP_EXCLUDE_KINDS)
    semantic = dedup_flags(semantic, exclude_kinds=_DEDUP_EXCLUDE_KINDS)

    status = "clean" if not mechanical and not semantic else (
        "semantic_flags" if semantic else "mechanical_violations")

    return {
        "status": status,
        "sentence_count": len(sentences),
        "mechanical_violations": mechanical,
        "semantic_flags": semantic,
    }


def blocking_semantic_flags(semantic_flags, file_path=None):
    """A different POLICY from ste100's exclusion-list approach -- see the
    module docstring. Each check's own occurrence-weight is compared
    against its OWN threshold (project-overridable via "check_config" in
    stopslop.config.json), and a check that reaches its threshold denies
    the write on its own if its action is "block" -- never, if "warn".
    A document can carry any number of triggered "warn" checks and still
    pass; that is the point of per-check granularity replacing one shared
    density number nobody could tune per check. See
    core.checks.blocking_semantic_flags for the shared mechanism."""
    project_root = _paths.find_project_root(__file__)
    return _checks.blocking_semantic_flags(effective_checks_table(), project_root, "slopwatch", semantic_flags, file_path)


def fix_sentence(sentence, enabled=None, extra_stock_adverbs=None):
    if enabled is None:
        enabled = _enabled_check_ids()
    if extra_stock_adverbs is None:
        extra_stock_adverbs = _custom_terms("stock_adverb")
    protected = []
    def _protect(m):
        protected.append(m.group(0))
        return f"\x00{len(protected) - 1}\x00"
    s = re.sub(r"`[^`\n]+`", _protect, sentence)

    # Each substitution below belongs to a specific, individually-toggleable
    # check -- a disabled check must not silently keep rewriting text its
    # own flag no longer appears for.
    if "stock_adverb" in enabled:
        words = STOCK_ADVERBS | set(extra_stock_adverbs)
        s = re.sub(r"(,\s*)?\b(" + "|".join(re.escape(w) for w in words) + r")\b(,\s*|\s+)?",
                    " ", s, flags=re.IGNORECASE)
    if "entity_encoded_punctuation" in enabled:
        s = _ENTITY_EM_DASH_RE.sub("—", s)
        s = _ENTITY_SECTION_RE.sub("section", s)
        s = _ENTITY_MIDDOT_RE.sub(",", s)
    if "emoji_in_prose" in enabled:
        s = _EMOJI_RE.sub("", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = re.sub(r"\s+([.,!?])", r"\1", s)
    if s:
        s = s[0].upper() + s[1:]  # deleting a sentence-initial adverb can leave a lowercase start

    def _restore(m):
        return protected[int(m.group(1))]
    s = re.sub(r"\x00(\d+)\x00", _restore, s)
    return s


def _fix_paragraph(text, enabled, extra_stock_adverbs):
    return " ".join(fix_sentence(s, enabled, extra_stock_adverbs) for s in tokenize_sentences(text))


def apply_mechanical_fixes(text, file_path=None):
    """Only call this when status == 'mechanical_violations' (no semantic
    flags) -- same rule as every other ruleset's fixer. Block-aware via
    split_into_blocks, mirroring rulesets/ste100/lint.py's approach."""
    enabled = _enabled_check_ids(file_path)  # once per call, not per sentence
    extra_stock_adverbs = _custom_terms("stock_adverb", file_path)  # same: once per call
    out = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            out.append(content)
        elif block_type == "header":
            out.append(fix_sentence(content, enabled, extra_stock_adverbs))
        elif block_type == "list_item":
            marker, item_text = LIST_ITEM_RE.match(content).groups()
            out.append(marker + (_fix_paragraph(item_text, enabled, extra_stock_adverbs)
                                  if item_text.strip() else item_text))
        else:
            out.append(_fix_paragraph(content, enabled, extra_stock_adverbs))
    return "\n".join(out)
