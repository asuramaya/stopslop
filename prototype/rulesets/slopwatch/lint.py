#!/usr/bin/env python3
"""slopwatch: a small, original demo ruleset built to prove stopslop's
plugin contract isn't secretly shaped around ASD-STE100. Where ste100
exists to ERASE individual voice on purpose (one approved word per concept,
no modals, no stylistic variation -- uniform aviation-manual clarity),
slopwatch targets ordinary AI-writing tells (a throat-clearing opener, a
dramatic colon reveal, an unnamed "studies show") while trying to flag
sparingly rather than demand uniformity -- the two rulesets are pointed in
almost opposite directions on purpose.

Six checks, in stopslop's own words and regex logic -- not ported from any
specific published word/pattern list:
  - filler_opener        (semantic)  throat-clearing sentence openers
  - stock_adverb          (mechanical) standalone filler adverbs, safe to delete
  - colon_reveal           (semantic)  short-buildup, punchy-reveal construction
  - binary_contrast         (semantic)  "It's not X. It's Y." across sentences
  - em_dash_cluster           (semantic, document-level)  too many em dashes
  - weasel_attribution         (semantic)  unnamed-authority phrasing

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
_STOCK_ADVERB_RE = re.compile(
    r"(,\s*)?\b(" + "|".join(STOCK_ADVERBS) + r")\b(,\s*|\s+)?", re.IGNORECASE)


def check_stock_adverb(sentence):
    hits = []
    for m in _STOCK_ADVERB_RE.finditer(sentence):
        hits.append({"word": m.group(2), "rule": "slopwatch.stock_adverb",
                      "auto_fix": True, "replacement": ""})
    return hits


# --- colon_reveal (semantic) --------------------------------------------
_COLON_REVEAL_RE = re.compile(r"^(.{1,60}?):\s+(\S.*)$")
_COLON_LABEL_WORDS = {"note", "example", "examples", "warning", "caution", "steps",
                       "requirement", "requirements", "following", "summary", "tip", "important",
                       "needed", "required", "include", "includes", "contains", "options"}


def check_colon_reveal(sentence):
    m = _COLON_REVEAL_RE.match(sentence.strip())
    if not m:
        return []
    before, _after = m.groups()
    words_before = before.split()
    if not (1 <= len(words_before) <= 6):
        return []
    last_word = words_before[-1].lower().strip(".,;:")
    if last_word in _COLON_LABEL_WORDS:
        return []  # a genuine label/list intro, not a dramatic reveal
    return [{"phrase": before.strip() + ":", "rule": "slopwatch.colon_reveal", "auto_fix": False,
              "note": "buildup-then-reveal construction -- state it as a plain sentence instead"}]


# --- weasel_attribution (semantic) ---------------------------------------
WEASEL_PHRASES = ["studies show", "experts agree", "research suggests", "many believe"]
_WEASEL_RE = re.compile(r"\b(" + "|".join(re.escape(p) for p in WEASEL_PHRASES) + r")\b", re.IGNORECASE)


def check_weasel_attribution(sentence):
    return [{"phrase": m.group(1), "rule": "slopwatch.weasel_attribution", "auto_fix": False,
              "note": "unnamed authority -- name the actual source, or cut the claim"}
            for m in _WEASEL_RE.finditer(sentence)]


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
EM_DASH_THRESHOLD = 3


def check_em_dash_cluster(text):
    count = text.count("—")
    if count > EM_DASH_THRESHOLD:
        return [{"count": count, "rule": "slopwatch.em_dash_cluster", "auto_fix": False,
                  "note": f"{count} em dashes in this document -- most drafts need "
                          f"0-2; use commas, periods, or parentheses for the rest"}]
    return []


_DEDUP_EXCLUDE_KINDS = {"em_dash_cluster"}  # document-level, one flag total -- nothing to collapse


def lint_and_gate(text, context=None):
    sentences = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            continue
        elif block_type == "header":
            block_text = HEADER_RE.sub("", content).strip()
        elif block_type == "list_item":
            m = LIST_ITEM_RE.match(content)
            block_text = m.group(2) if m else content
        else:  # paragraph
            block_text = content
        block_text = re.sub(r"`[^`\n]+`", " ", block_text)  # inline code untouchable
        sentences.extend(tokenize_sentences(block_text))

    mechanical = []
    semantic = []

    for s in sentences:
        for v in check_filler_opener(s):
            semantic.append({"kind": "filler_opener", "label": _label(v), "detail": v, "text": s})
        for v in check_stock_adverb(s):
            mechanical.append({"kind": "stock_adverb", "label": _label(v), "detail": v, "text": s})
        for v in check_colon_reveal(s):
            semantic.append({"kind": "colon_reveal", "label": _label(v), "detail": v, "text": s})
        for v in check_weasel_attribution(s):
            semantic.append({"kind": "weasel_attribution", "label": _label(v), "detail": v, "text": s})

    for v in check_binary_contrast(sentences):
        semantic.append({"kind": "binary_contrast", "label": _label(v), "detail": v, "text": v.get("text")})

    for v in check_em_dash_cluster(text):
        semantic.append({"kind": "em_dash_cluster", "label": None, "detail": v, "text": None})

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


BLOCK_FLAG_COUNT_THRESHOLD = 4


def blocking_semantic_flags(semantic_flags):
    """A different POLICY from ste100's exclusion-list approach -- see the
    module docstring. Individual flags never block alone; a write is
    denied only when the text reads as densely formulaic: an em-dash
    cluster fires on its own, or four or more flags of any kind appear
    across the whole document."""
    if any(f["kind"] == "em_dash_cluster" for f in semantic_flags):
        return semantic_flags
    if len(semantic_flags) >= BLOCK_FLAG_COUNT_THRESHOLD:
        return semantic_flags
    return []


def fix_sentence(sentence):
    protected = []
    def _protect(m):
        protected.append(m.group(0))
        return f"\x00{len(protected) - 1}\x00"
    s = re.sub(r"`[^`\n]+`", _protect, sentence)

    s = _STOCK_ADVERB_RE.sub(" ", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = re.sub(r"\s+([.,!?])", r"\1", s)
    if s:
        s = s[0].upper() + s[1:]  # deleting a sentence-initial adverb can leave a lowercase start

    def _restore(m):
        return protected[int(m.group(1))]
    s = re.sub(r"\x00(\d+)\x00", _restore, s)
    return s


def _fix_paragraph(text):
    return " ".join(fix_sentence(s) for s in tokenize_sentences(text))


def apply_mechanical_fixes(text):
    """Only call this when status == 'mechanical_violations' (no semantic
    flags) -- same rule as every other ruleset's fixer. Block-aware via
    split_into_blocks, mirroring rulesets/ste100/lint.py's approach."""
    out = []
    for block_type, content in split_into_blocks(text):
        if block_type in ("fence", "blank"):
            out.append(content)
        elif block_type == "header":
            out.append(fix_sentence(content))
        elif block_type == "list_item":
            marker, item_text = LIST_ITEM_RE.match(content).groups()
            out.append(marker + (_fix_paragraph(item_text) if item_text.strip() else item_text))
        else:
            out.append(_fix_paragraph(content))
    return "\n".join(out)
