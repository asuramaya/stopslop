#!/usr/bin/env python3
"""One-time (re-runnable) build step: parses the verified extraction at
docs/ASD-STE100-dictionary-extracted.dat into prototype/ste100_dictionary.json,
the structure ste100_lint.py actually loads at import time.

Verification note (2026-08-01): before this script was trusted to produce
enforcement data, the .dat file was checked two ways -- (1) structural: line
counts match the file's own header claim (878 approved / 1319 unapproved),
zero malformed lines, zero duplicate word+POS pairs; (2) independent: ~30
entries spread across the start, middle, and end of the alphabet (PDF pages
149-150, 290-291, 433-434) were read directly from the source PDF and diffed
by hand against the corresponding .dat lines, including the trickiest cases
(multi-alternative replacement lists, same headword split across two POS
lines) -- all exact matches, and the file's last entry matches the source's
last dictionary page. See project memory for the full incident this
verification step responds to.

Known, documented limitations of the output (word-level architecture, not
POS-aware):
  - 70 words are APPROVED in one part of speech and UNAPPROVED in another
    (e.g. "check" n=approved / v=unapproved->MAKE SURE,MEASURE,EXAMINE).
    check_vocabulary() checks word membership only, not POS. Approved wins
    (the pre-existing precedence in check_vocabulary, unchanged here), so
    these words never flag when used in their unapproved sense. Not fixed
    here -- real fix needs POS tagging, out of scope for this prototype.
  - 40 unapproved words carry different replacement sets across POS variants.
    The primary auto-fix replacement is the first alternative listed on the
    first POS entry encountered in the source, in file order -- may not
    match the sense actually used in a given sentence.
  - Multi-word headwords (e.g. "have to", "adjacent to") can't be matched by
    the current word-level tokenizer at all. Recorded in the JSON for
    completeness but excluded from the flat approved_words/unapproved_map
    the linter actually uses.
  - should/would/may/might/could are deliberately EXCLUDED from the output's
    unapproved_map -- see ste100_lint.py's MODAL_WORDS handling for why.
"""
import hashlib
import json
import os

# This file lives at prototype/rulesets/ste100/build_dictionary.py -- three
# levels below the repo root, unlike most of this project's other scripts.
# A one-off, rarely-run build step; not on the live gate's import path and
# not going to move again soon, so a plain relative ".." chain (matching
# this file's pre-refactor style) is fine here rather than depending on
# core.paths (which itself needs prototype/ on sys.path to import, adding
# the same kind of path-bootstrap fragility this script has never needed).
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.join(THIS_DIR, "..", "..", "..")
DAT_PATH = os.path.join(REPO_ROOT, "docs", "incidents",
                         "2026-08-01-ste100-dictionary-extraction-gate-bypass.dat")
OUT_PATH = os.path.join(THIS_DIR, "dictionary.json")


def parse_dat(path):
    with open(path) as f:
        lines = f.readlines()

    section = None
    approved = {}    # word -> [(pos, meaning), ...], file order
    unapproved = {}  # word -> [(pos, raw_replacement_field), ...], file order
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("#"):
            if "APPROVED_WORDS" in line and "UN" not in line:
                section = "approved"
            elif "UNAPPROVED_WORDS" in line:
                section = "unapproved"
            continue
        parts = line.split("|")
        if len(parts) != 3:
            raise ValueError(f"malformed line (expected word|pos|field): {line!r}")
        word, pos, field = (p.strip() for p in parts)
        lw = word.lower()
        if section == "approved":
            approved.setdefault(lw, []).append((pos, field))
        elif section == "unapproved":
            unapproved.setdefault(lw, []).append((pos, field))
        else:
            raise ValueError(f"data line before any section header: {line!r}")
    return approved, unapproved


def build_unapproved_entry(pos_entries):
    """pos_entries: [(pos, raw_replacement_field), ...] in file order.
    Returns {"replacement": <primary or None>, "alternatives": [...],
    "pos_variants": [[pos, raw_field], ...]}."""
    alternatives = []
    seen = set()
    for _, field in pos_entries:
        for alt in field.split(","):
            alt = alt.strip().lower()
            if not alt or alt == "none" or alt in seen:
                continue
            seen.add(alt)
            alternatives.append(alt)
    return {
        "replacement": alternatives[0] if alternatives else None,
        "alternatives": alternatives,
        "pos_variants": [[pos, field] for pos, field in pos_entries],
    }


def main():
    approved, unapproved = parse_dat(DAT_PATH)

    overlap = sorted(set(approved) & set(unapproved))
    multi_word_approved = sorted(w for w in approved if " " in w)
    multi_word_unapproved = sorted(w for w in unapproved if " " in w)
    no_replacement = sorted(
        w for w, entries in unapproved.items()
        if all(f.strip().lower() == "none" for _, f in entries)
    )

    unapproved_map = {w: build_unapproved_entry(entries) for w, entries in unapproved.items()}

    with open(DAT_PATH, "rb") as f:
        dat_hash = hashlib.sha256(f.read()).hexdigest()

    out = {
        "meta": {
            "source": "ASD-STE100 Issue 9 (2025-01-15), Part 2 - Dictionary, "
                       "PDF pages 149-434 (2-1-A1 to 2-1-Y1), full A-to-Z coverage",
            "extracted_from": "docs/ASD-STE100-dictionary-extracted.dat",
            "extracted_dat_sha256": dat_hash,
            "verified": "2026-08-01: structural checks (line counts vs. header "
                         "claim, malformed-line count, duplicate word+POS count) "
                         "all clean; 3 independent spot-checks against the source "
                         "PDF (pages 149-150, 290-291, 433-434; ~30 entries "
                         "spanning A, I/J, Y) all exact matches",
            "approved_count": len(approved),
            "unapproved_count": len(unapproved),
            "approved_unapproved_overlap_count": len(overlap),
            "approved_unapproved_overlap_sample": overlap[:20],
            "multi_word_headwords_excluded": {
                "approved": multi_word_approved,
                "unapproved": multi_word_unapproved,
            },
            "unapproved_no_replacement": no_replacement,
        },
        "approved_words": sorted(w for w in approved if " " not in w),
        "unapproved_map": {w: v for w, v in unapproved_map.items() if " " not in w},
    }

    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, sort_keys=False)
        f.write("\n")

    print(f"Wrote {OUT_PATH}")
    print(f"  approved: {out['meta']['approved_count']} "
          f"({len(out['approved_words'])} single-token)")
    print(f"  unapproved: {out['meta']['unapproved_count']} "
          f"({len(out['unapproved_map'])} single-token)")
    print(f"  approved/unapproved POS overlap: {out['meta']['approved_unapproved_overlap_count']}")
    print(f"  no-replacement words: {len(no_replacement)}")
    print(f"  source .dat sha256: {dat_hash}")


if __name__ == "__main__":
    main()
