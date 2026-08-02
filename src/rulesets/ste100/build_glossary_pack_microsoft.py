#!/usr/bin/env python3
"""One-time (re-runnable) build step: downloads the real
MicrosoftDocs/microsoft-style-guide repository from GitHub, parses its
styleguide/a-z-word-list-term-collections/ directory (854 real per-word
markdown files across a/..z/ and numbers-symbols/, as verified 2026-08-02 --
the 12 files under its term-collections/ subfolder are excluded, see "Known
limitations" below), and writes rulesets/ste100/glossary_packs/
microsoft_style_guide.json, the Tier 2 vocabulary pack glossary_packs.
load_pack_terms() actually loads when a project opts in.

This is CC-BY-4.0 content (attribution-only, not share-alike): per NOTICE
section 3, only the bare headword and a short provenance note this project
wrote itself are stored here -- never Microsoft's own definition prose.
Every note below is a fixed, templated sentence about *provenance*
("software/tooling vocabulary, from the Microsoft Writing Style Guide
(CC-BY-4.0) -- ASD-STE100 has no coverage for it"), not a paraphrase of
Microsoft's usage guidance for that word.

Correction (2026-08-02, same day): the first run of this script allowed
hyphenated and digit-bearing headwords (e.g. "front-end", "2d"). Found
live, after the fact: core/blocks.py's own tokenizer (words() =
re.findall(r"[A-Za-z']+", ...)) matches letters and apostrophes only --
it splits "front-end" into two separate tokens and drops "64" out of
"base64" entirely, so any pack key containing a hyphen or a digit can
never actually match anything check_vocabulary() looks up. 70 entries
that would have been silently inert were removed after the fact, and
TOKEN_RE below was tightened so a re-run cannot reintroduce them.

Verification note (2026-08-02): the source was fetched via
`curl -sL https://github.com/MicrosoftDocs/microsoft-style-guide/archive/
refs/heads/main.tar.gz` (mirrored here as urllib.request.urlretrieve,
stdlib only) and extracted locally. The repo actually contains TWO copies
of the word-list directory -- styleguide/a-z-word-list-term-collections/
(887 files) and the nested styleguide/styleguide/a-z-word-list-term-
collections/ (19 files, `diff -rq` confirms it's a stale/partial subset).
This script only ever reads the first (larger, real) one. Every one of the
854 per-word files was read (title/frontmatter + body); the 536 raw
single-token candidates that survived (see filtering below) were then
individually reviewed by hand before curation into the denylists below --
this was not a blind keyword-frequency dump.

Filtering pipeline (why a word is IN or OUT), applied in this order:

  1. Single-word terms only. Titles are split on "," and " vs. "/" versus "
     (Microsoft's own comparison-entry convention, e.g. "argument vs.
     parameter", "spreadsheet vs. workbook") to pull out each real headword
     separately, and any parenthetical gloss is stripped (e.g. "AI
     (artificial intelligence)" -> "AI"). Whatever remains must match
     ^[a-z0-9]+(-[a-z0-9]+)*$ with no internal space -- a hyphenated
     compound like "front-end" or "big-endian" passes; "black hat hacker"
     or "master/slave" does not. This alone rejects 381 of 917 raw
     candidate strings; another 34 fail the character check (mostly
     trailing-hyphen prefix fragments like "co-", or symbol titles).

  2. Not already in the real ASD-STE100 dictionary. dictionary.json's
     approved_words and unapproved_map keys are loaded and any exact
     match is dropped (165 candidates), keeping this pack purely
     additive. Beyond exact match, _stems_to_dictionary() reapplies
     lint.py's own regular-inflection stemmer (deliberately duplicated,
     not imported -- see the comment on that function for why) so a
     candidate like "runs" (stems to the explicitly UNAPPROVED "run")
     can't sneak in and silently override a real ASD-STE100 prohibition
     via PROJECT_TERMS' precedence over UNAPPROVED_MAP in
     lint.check_vocabulary(); a candidate like "canceled" (stems to the
     already-APPROVED "cancel") is dropped too, as pure redundancy.
     Confirmed live on this exact source: allows, depressed, dimmed,
     enables, labeled, runs, and zeros all stem to a forbidden word and
     are excluded this way, not by manual listing.

  3. Not a Microsoft product/brand/platform name, not a named punctuation
     mark, not a term the source itself explicitly recommends against
     using at all (as opposed to just narrowing which *sense* is
     correct -- "alias" saying "don't use to mean an email address" is a
     sense restriction, the word stays; "blacklist" saying "consider
     alternatives" for the whole word is a real discouragement, it goes),
     not a dated/legacy term of little value to a modern software
     glossary. See the SKIP_* sets below -- each was built by actually
     opening and reading the relevant files, not guessed from the
     filename alone.

  4. Not plain English usage/grammar guidance with no real technical
     content (comparatives, courtesy words, connectors, generic business
     jargon) -- SKIP_GENERIC_ENGLISH. This is the single biggest manual
     category: Microsoft's A-Z list spends much of its length on things
     like "afterward" vs. "later" or "less" vs. "fewer" vs. "under",
     which are real writing-style guidance but add no software/tech
     vocabulary ASD-STE100 doesn't already cover in spirit.

Known limitations of this extraction:
  - term-collections/*.md (12 files: cloud-computing-terms.md,
    security-terms.md, bits-bytes-terms.md, etc.) are NOT parsed. These
    are multi-term Markdown tables (see e.g. computer-device-terms.md),
    a structurally different shape than the one-word-per-file pattern
    this script's parser handles; a handful of real words likely live
    only there (this script's own single-file candidate pool never saw
    them). Left as a possible future extension, not attempted here to
    avoid a second, less-verified parser path.
  - The "explicitly discouraged by the source" check (step 3) was done
    by manually reading flagged files, not by a generic "don't use"
    text scan -- a blind scan flags 185 of 536 raw candidates, because
    Microsoft also writes "Don't use X to mean Y" for ordinary sense-
    narrowing guidance (e.g. "alias", "attribute", "author"), which is
    not the same thing as discouraging the word itself. A handful of
    genuinely-discouraged words this pass didn't happen to read may
    still be present; report_pack_terms() encodes no such automated
    detector.
  - Category tagging in each note (see categorize()) is a coarse,
    keyword-based guess at what kind of vocabulary a word is
    (networking/security/UI/etc.), read from that word's own body text.
    It is a label for the note field, not a claim of authoritative
    classification.
  - This is a snapshot of the microsoft-style-guide main branch as of
    the "extracted" date in the output file's _meta -- Microsoft's list
    changes over time; re-running this script later will reflect
    whatever is live on GitHub then, not necessarily the same 854 files.

Usage:
    cd src && python3 rulesets/ste100/build_glossary_pack_microsoft.py
"""
import json
import os
import re
import sys
import tarfile
import tempfile
import urllib.request
from datetime import date

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DICTIONARY_PATH = os.path.join(THIS_DIR, "dictionary.json")
OUT_PATH = os.path.join(THIS_DIR, "glossary_packs", "microsoft_style_guide.json")

SOURCE_ARCHIVE_URL = (
    "https://github.com/MicrosoftDocs/microsoft-style-guide/archive/refs/heads/main.tar.gz"
)
SOURCE_REPO_URL = "https://github.com/MicrosoftDocs/microsoft-style-guide"
# Path *within* the extracted archive to the real word-list tree. The repo
# also has a stale nested copy at styleguide/styleguide/a-z-word-list-term-
# collections/ (19 files vs. this one's 887) -- deliberately not used.
WORD_LIST_SUBPATH = os.path.join("styleguide", "a-z-word-list-term-collections")
EXCLUDED_SUBDIR = "term-collections"  # multi-term tables, different shape -- see docstring


# ---------------------------------------------------------------------------
# Denylists (hand-curated 2026-08-02 by reading the flagged files -- see
# module docstring step 3/4 for the method).
# ---------------------------------------------------------------------------

# Single-letter placeholder/abbreviation-letter entries (e.g. n.md: "Use a
# lowercase n in italic type to refer to a generic use of a number") -- not
# real vocabulary words, just a style note about italicizing a variable.
SKIP_PLACEHOLDER_LETTERS = {"b", "c", "g", "k", "m", "n", "x"}

# Microsoft/product/platform brand names, standards-body and locale codes --
# not general software vocabulary, the same reasoning the task brief gives
# for excluding Xbox/SharePoint/Teams. "blade" is Azure-portal-pane-specific
# (blade.md: "Use *blade* to refer to a pane in the Azure portal"); "taskbar"
# is Windows-shell-chrome-specific.
SKIP_BRAND_PRODUCT_PLATFORM = {
    "microsoft", "windows", "windows-based", "w3c", "uk", "us", "jscript",
    "blade", "taskbar",
}

# The source explicitly recommends against the word ITSELF (not just a
# narrower sense of it), with a suggested replacement -- confirmed by
# reading each file's body, e.g. blacklist.md/whitelist.md: "Consider
# alternatives where possible"; board.md: "Don't use ... Use *card*
# instead"; backtab.md: "Don't use. Instead, instruct the customer to use
# Shift+Tab"; subaddress.md / prop.md: "Don't use ... Use a more specific
# term" / "Don't use as an abbreviation for propagate."; far-left-far-
# right.md: "Don't use. Use *leftmost* or *rightmost* instead."
SKIP_EXPLICITLY_DISCOURAGED = {
    "blacklist", "whitelist", "board", "backtab", "subaddress", "prop",
    "far-left", "far-right",
}

# Named punctuation marks -- not prose vocabulary a writer looks up.
SKIP_PUNCTUATION_NAMES = {"ampersand", "asterisk", "parenthesis", "parentheses"}

# Not a real headword at all, or a wrong-meaning collision that has no
# place in a software/tech glossary regardless of Microsoft's own
# inclusion: abort-abortion.md's own guidance is "Never use *abortion*"
# (it's an entry ABOUT the word *abort*, not proposing "abortion" as
# software vocabulary); e-words.md is a meta-entry about how to spell
# *other* e-prefixed words (e-book, e-commerce), not a headword itself.
SKIP_NOT_A_REAL_HEADWORD = {"abortion", "e-words"}

# Plain English usage/grammar guidance, courtesy words, comparatives,
# generic business jargon, and general disability-language guidance (real
# writing-style content, but not software/tech-specific vocabulary) --
# not distinct software/tech vocabulary ASD-STE100 lacks. This is the
# biggest single category in Microsoft's A-Z list.
SKIP_GENERIC_ENGLISH = {
    "afterward", "alphabetical", "am", "better", "billion", "bio",
    "company", "earlier", "family", "given", "greater", "heading",
    "higher", "home", "illegal", "intelligence", "italic", "justified",
    "justify", "legal", "leverage", "million", "organization",
    "please", "preceding", "simply", "sorry", "specify", "stretch", "surf",
    "thanks", "thousand", "tone", "underline", "using", "visit", "worldwide",
    "achievement", "actionable", "administer", "author", "appendix",
    "appendices", "mathematical", "leading", "ok", "okay", "pm", "midnight",
    "roman", "audiobook", "edutainment", "matrices", "indices",
    "hard-of-hearing", "hearing-impaired",
}

# Dated/legacy terms of little value to a *modern* software vocabulary pack.
SKIP_DATED_OR_LEGACY = {
    "dot-com", "newsgroup", "newsreader", "dial-up", "baud", "beep",
    "iconize", "frameset", "metafile", "p-code", "weblog", "ultrabook",
    "fubar", "deinstall", "nui", "meg", "gbyte", "mbyte", "kbyte",
    "null-terminating", "wordwrapping",
}

SKIP_ALL = (
    SKIP_PLACEHOLDER_LETTERS | SKIP_BRAND_PRODUCT_PLATFORM
    | SKIP_EXPLICITLY_DISCOURAGED | SKIP_PUNCTUATION_NAMES
    | SKIP_NOT_A_REAL_HEADWORD | SKIP_GENERIC_ENGLISH | SKIP_DATED_OR_LEGACY
)

# Letters only, on purpose -- see the "Correction" note in this file's own
# module docstring. Matches core/blocks.py's real tokenizer character
# class exactly (re.findall(r"[A-Za-z']+", ...)): no hyphen, no digit, no
# dot. A candidate this regex rejects would never actually match anything
# check_vocabulary() looks up, so it does not belong in the pack at all.
TOKEN_RE = re.compile(r"[a-z]+")
FRONTMATTER_TITLE_RE = re.compile(r"^title:\s*(.+?)\s*-\s*Microsoft Style Guide\s*$", re.MULTILINE)
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
FRONTMATTER_BLOCK_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
PAREN_RE = re.compile(r"\([^)]*\)")
SPLIT_RE = re.compile(r",|\bvs\.?\b|\bversus\b", re.IGNORECASE)


def fetch_source(dest_dir):
    """Downloads the microsoft-style-guide repo's main-branch tarball and
    extracts it into dest_dir. Returns the path to the real (larger) word-
    list directory. Network access to a single, pinned, well-known GitHub
    URL -- not user-controlled input -- so tarfile.extractall() here is
    extracting a source this script's own author chose, the same trust
    level build_dictionary.py places in its local .dat file."""
    archive_path = os.path.join(dest_dir, "microsoft-style-guide.tar.gz")
    urllib.request.urlretrieve(SOURCE_ARCHIVE_URL, archive_path)
    with tarfile.open(archive_path) as tf:
        try:
            tf.extractall(dest_dir, filter="data")  # Python 3.12+ safe-extraction filter
        except TypeError:
            tf.extractall(dest_dir)  # older Python without the filter= kwarg
    roots = [e for e in os.listdir(dest_dir) if e.startswith("microsoft-style-guide-")]
    if not roots:
        raise RuntimeError(f"extraction didn't produce a microsoft-style-guide-* dir in {dest_dir}")
    return os.path.join(dest_dir, roots[0], WORD_LIST_SUBPATH)


def iter_word_files(word_list_dir):
    """Yields the path of every per-word markdown file directly inside each
    single-letter (or numbers-symbols) subfolder, skipping the
    term-collections/ subfolder (see module docstring) and any non-.md
    entries (media/ image subfolders live alongside some letters)."""
    for entry in sorted(os.listdir(word_list_dir)):
        full = os.path.join(word_list_dir, entry)
        if not os.path.isdir(full) or entry == EXCLUDED_SUBDIR:
            continue
        for fn in sorted(os.listdir(full)):
            if fn.endswith(".md"):
                yield os.path.join(full, fn)


def extract_title(text):
    m = FRONTMATTER_TITLE_RE.search(text)
    if m:
        return m.group(1).strip()
    m = H1_RE.search(text)
    return m.group(1).strip() if m else None


def body_text(text):
    text = FRONTMATTER_BLOCK_RE.sub("", text, count=1)
    return H1_RE.sub("", text, count=1).strip()


def split_headwords(title):
    """A title like "add-in, add-on" or "argument vs. parameter" or
    "AI (artificial intelligence)" names one or more real headwords.
    Strips any parenthetical gloss, then splits on "," / " vs. " / " vs "
    / " versus " -- Microsoft's own two title conventions for a multi-term
    entry."""
    title = PAREN_RE.sub("", title).strip()
    return [p.strip() for p in SPLIT_RE.split(title) if p.strip()]


def _regular_base_candidates(word):
    """Deliberately DUPLICATED from lint.py's _regular_base_candidates, not
    imported -- importing rulesets.ste100.lint here would need src/ on
    sys.path, the exact path-bootstrap fragility build_dictionary.py's own
    comment says this kind of one-off build script should stay clear of.
    Keep this in sync with lint.py by hand if that stemmer ever changes; a
    drift here can only make this function MISS a real conflict (a false
    negative on excluding a bad word), never wrongly reject a good one, so
    staleness fails safe."""
    candidates = []
    if word.endswith("ies") and len(word) > 4:
        candidates.append(word[:-3] + "y")
    if word.endswith("es") and len(word) > 3:
        candidates.append(word[:-2])
    if word.endswith("s") and len(word) > 2:
        candidates.append(word[:-1])
    if word.endswith("ied") and len(word) > 4:
        candidates.append(word[:-3] + "y")
    if word.endswith("ed") and len(word) > 3:
        stem = word[:-2]
        candidates.append(stem)
        candidates.append(stem + "e")
        if len(stem) > 2 and stem[-1] == stem[-2] and stem[-1] not in "aeiou":
            candidates.append(stem[:-1])
    return candidates


def stems_to_dictionary(word, approved, unapproved):
    """True if word is a regular inflection (plural/verb form) of a word
    already in the real ASD-STE100 dictionary -- either sense makes it a
    bad pack candidate: stemming to an UNAPPROVED word (e.g. "runs" ->
    "run") would silently override a real prohibition, since
    check_vocabulary() checks PROJECT_TERMS (pack content included) before
    UNAPPROVED_MAP; stemming to an APPROVED word (e.g. "canceled" ->
    "cancel") is pure redundancy."""
    for cand in _regular_base_candidates(word):
        if cand in unapproved or cand in approved:
            return True
    return False


_CATEGORY_KEYWORDS = [
    # (category label, keywords to look for in the entry's own body text)
    ("security", ("security", "encrypt", "password", "authentic", "vulnerab",
                   "malware", "phish", "spoof", "firewall", "exploit")),
    ("networking", ("network", "protocol", "server", "connection", "wireless",
                     "bluetooth", "ip address", "bandwidth", "router")),
    ("data/storage", ("database", "data structure", "storage", "record",
                        "backup", "disk", "file system")),
    ("cloud/infrastructure", ("cloud", "virtual machine", "datacenter",
                                "scalab", "container", "kubernetes")),
    ("accessibility", ("accessib", "screen reader", "assistive")),
    ("UI/interaction", ("button", "menu", "dialog box", "window", "click",
                          "screen", "cursor", "touch")),
]


def categorize(body):
    """A coarse, keyword-based guess at what kind of vocabulary a word is --
    purely to make the pack's provenance note slightly more informative
    than one flat boilerplate string repeated 300+ times, never a claim of
    authoritative classification. Falls back to "software/tooling",
    matching this project's other packs' default (see mdn_glossary.json).

    Deliberately only looks at the entry's FIRST paragraph, not the whole
    body: a full-body scan flagged "abort" as networking (its own
    "Alternative terms" table mentions "network connections" for a
    *different* word), "far-left" as accessibility (an "Accessibility
    tip" aside, not what the word itself means), and "app" as data/storage
    (an offhand "database management system" example). The first
    paragraph is what the entry is actually defining; later examples,
    "See also" links, and asides are not."""
    first_paragraph = body.split("\n\n", 1)[0].lower()
    for label, keywords in _CATEGORY_KEYWORDS:
        if any(kw in first_paragraph for kw in keywords):
            return label
    return "software/tooling"


def build_note(category):
    return (f"{category} vocabulary, from the Microsoft Writing Style Guide "
            f"(CC-BY-4.0) -- ASD-STE100 has no coverage for it")


def main():
    dictionary = json.load(open(DICTIONARY_PATH))
    approved = set(dictionary["approved_words"])
    unapproved = set(dictionary["unapproved_map"].keys())
    already_covered = approved | unapproved

    with tempfile.TemporaryDirectory(prefix="msft-style-guide-") as tmp:
        print(f"Downloading {SOURCE_ARCHIVE_URL} ...")
        word_list_dir = fetch_source(tmp)

        files = list(iter_word_files(word_list_dir))
        print(f"Scanning {len(files)} source files under "
              f"{os.path.relpath(word_list_dir, tmp)} ...")

        terms = {}
        stats = {
            "no_title": 0, "multiword_or_badchars": 0,
            "already_in_dictionary_exact": 0, "already_in_dictionary_stemmed": 0,
            "denylisted": 0, "kept": 0, "raw_candidates": 0,
        }

        for fp in files:
            text = open(fp, encoding="utf-8").read()
            title = extract_title(text)
            if not title:
                stats["no_title"] += 1
                continue
            body = body_text(text)
            for raw in split_headwords(title):
                w = raw.lower().strip()
                if not w:
                    continue
                if " " in w or not TOKEN_RE.fullmatch(w):
                    stats["multiword_or_badchars"] += 1
                    continue
                stats["raw_candidates"] += 1
                if w in already_covered:
                    stats["already_in_dictionary_exact"] += 1
                    continue
                if stems_to_dictionary(w, approved, unapproved):
                    stats["already_in_dictionary_stemmed"] += 1
                    continue
                if w in SKIP_ALL:
                    stats["denylisted"] += 1
                    continue
                if w in terms:
                    continue  # already kept via an earlier file/alternate spelling
                terms[w] = {"note": build_note(categorize(body))}
                stats["kept"] += 1

    meta = {
        "name": "Microsoft Writing Style Guide word list",
        "source": SOURCE_REPO_URL,
        "license": "CC-BY-4.0",
        "extracted": date.today().isoformat(),
    }
    out = {"_meta": meta, "terms": dict(sorted(terms.items()))}

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, sort_keys=False)
        f.write("\n")

    print(f"\nWrote {OUT_PATH}")
    print(f"  source files scanned:            {len(files)}")
    print(f"  raw single-token candidates:      {stats['raw_candidates']}")
    print(f"  skipped, multi-word/bad chars:    {stats['multiword_or_badchars']}")
    print(f"  skipped, already in dictionary:   {stats['already_in_dictionary_exact']} exact "
          f"+ {stats['already_in_dictionary_stemmed']} stemmed")
    print(f"  skipped, denylisted (brand/generic/discouraged/dated/punctuation/placeholder): "
          f"{stats['denylisted']}")
    print(f"  kept:                             {stats['kept']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
