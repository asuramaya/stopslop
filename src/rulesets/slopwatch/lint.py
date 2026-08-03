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

from core.blocks import (
    tokenize_sentences, split_into_blocks,
    HEADER_RE, LIST_ITEM_RE,
)
from core.flags import dedup_flags, default_label as _label
from core import config as _core_config, paths as _paths, terms as _terms

# Every "kind" string this ruleset's checks can produce -- the modularity
# surface rulesets/slopwatch/__init__.py's list_checks()/set_enabled_checks()
# expose. A user can turn any of these off individually via
# stopslop.config.json's "disabled_checks" key; everything runs by default.
ALL_CHECK_IDS = frozenset({
    "filler_opener", "stock_adverb", "colon_reveal", "weasel_attribution",
    "entity_encoded_punctuation", "not_just_x_but_y", "vague_intensifier",
    "emoji_in_prose", "marketing_adjective", "filler_verb", "marketing_cliche",
    "solicit_criticism", "unearned_profundity", "dramatic_fragmentation",
    "bold_bullet_lead", "id_label_lead", "binary_contrast",
    "canned_question_answer", "negative_listing", "em_dash_cluster",
})


def _enabled_check_ids():
    """Every check that should actually run right now: ALL_CHECK_IDS minus
    whatever stopslop.config.json's "disabled_checks" names for this
    ruleset. Read fresh every call, not cached -- these are a handful of
    short strings, cheap enough that a stale in-memory copy (the exact bug
    class PROJECT_TERMS caching required an explicit-invalidation dance to
    avoid, see rulesets/ste100/lint.py) buys nothing here."""
    try:
        project_root = _paths.find_project_root(__file__)
        disabled = set(_core_config.disabled_checks(project_root, "slopwatch"))
    except Exception:
        return set(ALL_CHECK_IDS)
    return ALL_CHECK_IDS - disabled


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


DEFAULT_OPTIONS = {
    "em_dash_threshold": 3,
    "block_flag_count_threshold": 4,
}


def _options():
    """DEFAULT_OPTIONS with any valid override from stopslop.config.json's
    "options" key layered on top. An override with the wrong type, or an
    unresolvable project root (e.g. a lint call against free text with no
    real project on disk), silently falls back to the default rather than
    breaking the gate -- same never-break-the-gate posture as
    _enabled_check_ids()."""
    opts = dict(DEFAULT_OPTIONS)
    try:
        project_root = _paths.find_project_root(__file__)
        overrides = _core_config.ruleset_options(project_root, "slopwatch")
    except Exception:
        return opts
    for key, value in overrides.items():
        if key in opts and isinstance(value, type(opts[key])):
            opts[key] = value
    return opts

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
    threshold = _options()["em_dash_threshold"]
    count = text.count("—") + len(_ENTITY_EM_DASH_RE.findall(text))
    if count > threshold:
        return [{"count": count, "rule": "slopwatch.em_dash_cluster", "auto_fix": False,
                  "note": f"{count} em dashes in this document -- most drafts need "
                          f"{threshold} or fewer; use commas, periods, or parentheses for the rest"}]
    return []


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


# Every check that's fundamentally "match text against a list of words or
# phrases", declared as a TERM LIST -- the one shared shape every ruleset
# now uses (see core/terms.py). All five are DENY lists: the terms are the
# thing being flagged, the opposite polarity from ste100's project
# vocabulary, which is an ALLOW list. Both are term lists; polarity is a
# field, not a different concept with a different name and a different API,
# which is what it used to be.
#
# accepts_packs is True even though no pack targets these today. A pack
# declares which (ruleset, list) it feeds, so a corporate banned-phrase
# pack aimed at ("slopwatch", "marketing_cliche") would work with no code
# change here -- leaving the door open costs nothing and is the difference
# between a real abstraction and one shaped around its first user.
TERM_LISTS = {
    "weasel_attribution": {
        "label": "Weasel attributions",
        "description": "Vague appeals to authority with no named source.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": WEASEL_PHRASES,
    },
    "marketing_adjective": {
        "label": "Marketing adjectives",
        "description": "Promotional adjectives that assert quality instead of showing it.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": MARKETING_ADJECTIVES,
    },
    "filler_verb": {
        "label": "Filler verbs",
        "description": "Verb phrases that add length without adding meaning.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": FILLER_VERB_PATTERNS,
    },
    "marketing_cliche": {
        "label": "Marketing cliches",
        "description": "Stock phrases that signal generated copy.",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": MARKETING_CLICHES,
    },
    "stock_adverb": {
        "label": "Stock adverbs",
        "description": "Filler adverbs safe to delete outright (auto-fixed).",
        "polarity": "deny", "accepts_packs": True,
        "built_ins": STOCK_ADVERBS,
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


def lint_and_gate(text, context=None, file_path=None):
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
    enabled = _enabled_check_ids()
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


def blocking_semantic_flags(semantic_flags):
    """A different POLICY from ste100's exclusion-list approach -- see the
    module docstring. Individual flags never block alone; a write is
    denied only when the text reads as densely formulaic: an em-dash
    cluster fires on its own, or the configured flag-count threshold is
    reached (4 by default, see DEFAULT_OPTIONS)."""
    if any(f["kind"] == "em_dash_cluster" for f in semantic_flags):
        return semantic_flags
    if len(semantic_flags) >= _options()["block_flag_count_threshold"]:
        return semantic_flags
    return []


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
    enabled = _enabled_check_ids()  # read once per call, not once per sentence
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
