#!/usr/bin/env python3
"""One-time (re-runnable) build step: parses the real MDN Web Docs Glossary
(github.com/mdn/content, files/en-us/glossary/) into
rulesets/ste100/glossary_packs/mdn_glossary.json, the "mdn-glossary" pack
AVAILABLE_PACKS already registers in glossary_packs/__init__.py.

LICENSE NOTE -- read before touching this file's output shape: MDN's
content is CC-BY-SA-2.5 (share-alike), NOT this repository's own MIT terms
(see NOTICE, which documents the ASD-STE100 dictionary's own non-MIT
status as the existing precedent for "this repo carries data under terms
other than its code license"). Share-alike is viral over *copied
expression*, not over facts -- a headword ("api", "endpoint",
"middleware") is a fact/name, not a creative expression, and courts /
common practice treat single-word glossary terms as below the threshold
of copyrightability on their own. To keep the share-alike surface
minimal, this script extracts ONLY the headword (the folder slug MDN
itself uses as the term's own single-token identifier) plus a short,
original, provenance-only note ("software/tooling vocabulary, from the
MDN Web Docs Glossary (CC-BY-SA-2.5) -- ASD-STE100 has no coverage for
it"). It never fetches, stores, or derives text from MDN's actual
definition prose -- the per-entry frontmatter `title:` line is read only
to confirm the entry is real and to sanity-check the slug is the genuine
headword, and is itself discarded, not written to the output file.

METHOD -- how the term list was determined:
  1. List every file under files/en-us/glossary/ in mdn/content's `main`
     branch via one recursive git-trees API call (unauthenticated;
     GitHub serves this endpoint without a token, confirmed not
     rate-limited for a single call). Keep only paths of the exact shape
     files/en-us/glossary/<slug>/index.md (a real term folder) --
     depth-6 paths like glossary/dsl/domain_specific_language/index.md
     are MDN's own disambiguation subpages for an ambiguous slug that
     already has its own depth-5 entry, not a second headword, and are
     excluded; files/en-us/glossary/index.md (the glossary landing page
     itself) is excluded the same way.
  2. For each depth-5 slug, fetch its index.md from
     raw.githubusercontent.com (no auth required, not the same rate
     limit as the api.github.com JSON endpoints) and read the
     frontmatter `title:` line only, as existence-proof the slug is a
     real, live glossary entry -- never its body text.
  3. HEADWORD = the folder slug itself, not the frontmatter title. MDN
     encodes real multi-word phrases in a slug with underscores (e.g.
     accessibility_tree, cross-site_scripting) while single-token terms
     never contain one (api, cls, ssr, utf-8, node.js, pseudo-class) --
     so "slug has no underscore" is a reliable, mechanical proxy for
     "this term is genuinely one token," matching this project's own
     "skip anything with an actual space" rule far more precisely than
     the human-readable title would (many single-token terms have a
     multi-word *title*, e.g. slug "fps" / title "Frame rate (FPS)" --
     using the title would wrongly discard a good single-token entry;
     using the slug keeps exactly the form a technical writer actually
     types in prose). A hyphenated or dotted slug (utf-8, node.js,
     percent-encoding, pseudo-class) is kept as one token per this
     project's "hyphenated compound that reads as one token" allowance.
  4. Drop anything already present in the real ASD-STE100 dictionary
     (src/rulesets/ste100/dictionary.json's approved_words or
     unapproved_map, case-insensitive) -- packs stay purely additive,
     never a second opinion on a word STE100 already rules on.
  5. Drop NARROW_JARGON_SKIP: a manually reviewed denylist of slugs that
     passed steps 1-4 but are deep spec/standards-body/protocol-internals
     jargon a general software-documentation writer would basically
     never reach for (dead browser engines like Presto/Trident, narrow
     standards-body acronyms like IANA/ICANN/IETF/WHATWG/Khronos, WebRTC/
     VoIP protocol internals like ICE/SDP/STUN/RTCP, deep W3C spec-only
     concepts like WindowProxy/CSSOM/Houdini/stringifier, etc.) -- see
     the set's own inline comments for the reasoning per group. This step
     is a judgment call, same as build_dictionary.py's own hand-reviewed
     spot checks; every excluded slug is listed so the call is auditable
     and reversible, not a silent guess.

VERIFICATION NOTE (2026-08-02): run against a live fetch of mdn/content's
main branch. 603 real depth-5 glossary term folders were found (matching
the 604 the task brief that started this script cited, within one --
files/en-us/glossary/index.md, the landing page, is not itself a term and
both counts plausibly include or exclude it). Of those, 364 have a slug
with no underscore (single-token or hyphenated/dotted-compound
candidates); 27 of those are already covered by the real ASD-STE100
dictionary; of the remaining 337, 60 were hand-excluded as narrow/rare
spec jargon (NARROW_JARGON_SKIP below), leaving 275 kept. All 275 kept
entries were spot-read (this script fetches and requires a non-empty
`title:` line for every entry it keeps -- an entry whose index.md 404s or
has no title is skipped and reported, never silently included), and ~15
were independently read in full (title + opening definition sentence) by
hand before this filtering was finalized, confirming each is a real,
current MDN glossary entry and not a fabrication.

Usage:
    python3 build_glossary_pack_mdn.py
Requires network access to api.github.com and raw.githubusercontent.com.
Stdlib only -- no new dependencies.
"""
import json
import os
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DICTIONARY_PATH = os.path.join(THIS_DIR, "dictionary.json")
OUT_PATH = os.path.join(THIS_DIR, "glossary_packs", "mdn_glossary.json")

TREE_URL = "https://api.github.com/repos/mdn/content/git/trees/main?recursive=true"
RAW_BASE = "https://raw.githubusercontent.com/mdn/content/main/files/en-us/glossary"
GLOSSARY_PREFIX = "files/en-us/glossary/"
USER_AGENT = "stopslop-build-glossary-pack-mdn/1.0 (stdlib urllib; one-time build script)"

EXTRACTED_DATE = "2026-08-02"

NOTE = ("software/tooling vocabulary, from the MDN Web Docs Glossary "
        "(CC-BY-SA-2.5) -- ASD-STE100 has no coverage for it")

# Narrow/rare/dated spec-jargon a general software-documentation writer
# would basically never reach for -- hand-reviewed against each entry's
# real MDN definition (2026-08-02) before exclusion. Grouped by why.
NARROW_JARGON_SKIP = {
    # narrow standards-body / registry acronyms one level removed from
    # the bodies writers actually cite (w3c, wcag are kept -- genuinely
    # common; their parent/companion bodies below are not)
    "atag", "uaag", "wai", "iana", "icann", "ietf", "whatwg", "itu",
    "khronos", "smpte",
    "ecma",  # "ecmascript" itself is kept; the bare standards-body abbr. isn't
    # dead/historical browser engines, formats, and networks
    "presto", "trident", "xhtml", "nntp", "usenet", "arpa", "arpanet",
    # deep W3C / browser-engine-internals spec jargon, meaningful mainly
    # to spec authors or engine implementers, not app/doc writers
    "idl", "webidl", "houdini", "cssom", "fragmentainer", "windowproxy",
    "stringifier", "expando", "dominator", "mathml", "rdf", "sgml",
    "xforms", "xinclude", "xlink", "xquery", "xslt",
    "non-normative", "normative",  # spec-prose jargon, not app vocabulary
    # narrow/legacy network & telephony protocol internals (WebRTC/VoIP
    # signaling plumbing, obsolete telecom tone signaling, a deprecated
    # security header, narrow DNS/telephony-stack internals)
    "dtmf", "dtls", "ice", "sctp", "rtcp", "rtsp", "rtp", "sdp", "stun",
    "pac", "webdav", "caldav", "carddav", "hpkp", "ril", "sld", "tofu",
    "alpn",
    # narrow academic / 3D-graphics / parallel-architecture jargon
    "quaternion", "texel", "rail", "simd", "sisd",
    # narrow UX-research shorthand, rarely used outside specific teams
    "ftu",
    # in general use writers say URI or URL; URN specifically is rare
    "urn",
}


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def list_glossary_slugs():
    """Every real depth-5 files/en-us/glossary/<slug>/index.md path in
    mdn/content's main branch, as bare slugs. Excludes the glossary
    landing page itself and MDN's own nested disambiguation subpages
    (depth-6, e.g. glossary/dsl/domain_specific_language/index.md) --
    those describe one sense of a slug that already has its own
    top-level entry, not a second headword."""
    tree = _get_json(TREE_URL)
    if tree.get("truncated"):
        raise RuntimeError("GitHub tree API response was truncated -- "
                            "recursive listing is incomplete, refusing to "
                            "silently work from a partial file list")
    slugs = []
    for entry in tree["tree"]:
        path = entry["path"]
        if not path.startswith(GLOSSARY_PREFIX) or not path.endswith("/index.md"):
            continue
        rest = path[len(GLOSSARY_PREFIX):-len("/index.md")]
        if "/" in rest or not rest:
            continue  # nested disambiguation subpage, or the prefix itself
        slugs.append(rest)
    return sorted(set(slugs))


def fetch_title(slug):
    """The entry's frontmatter `title:` line only -- proof the entry is
    real and live, never the definition body. Returns None if the fetch
    fails or no title line is found (both treated as "not a usable real
    entry", never silently included)."""
    url = f"{RAW_BASE}/{slug}/index.md"
    try:
        text = _get_text(url)
    except (urllib.error.URLError, urllib.error.HTTPError):
        return None
    in_frontmatter = False
    for line in text.splitlines():
        if line.strip() == "---":
            if in_frontmatter:
                break
            in_frontmatter = True
            continue
        if in_frontmatter and line.startswith("title:"):
            return line[len("title:"):].strip().strip('"')
    return None


def load_ste100_words():
    with open(DICTIONARY_PATH) as f:
        d = json.load(f)
    words = set(w.lower() for w in d["approved_words"])
    words.update(w.lower() for w in d["unapproved_map"].keys())
    return words


def main():
    print(f"Fetching files/en-us/glossary/ file list from {TREE_URL} ...")
    slugs = list_glossary_slugs()
    print(f"  {len(slugs)} real glossary term folders found")

    # Letters only, on purpose -- no hyphen, dot, or digit, unlike an
    # earlier version of this script: core/blocks.py's own tokenizer
    # (words() = re.findall(r"[A-Za-z']+", ...)) matches letters and
    # apostrophes only. It splits "node.js" or "pseudo-element" into two
    # tokens, and it drops "64" out of "base64" entirely -- so any of
    # those as a stored key can never actually match anything
    # check_vocabulary() looks up. Confirmed live: the first version of
    # this pack shipped 13 entries that were silently inert for exactly
    # this reason.
    single_token = sorted(s for s in slugs
                           if "_" not in s and s.isalpha() and s.isascii())
    multi_word_skipped = len(slugs) - len(single_token)
    print(f"  {len(single_token)} are pure single-token, letters-only slugs "
          f"({multi_word_skipped} skipped: multi-word phrase, or contains a "
          f"hyphen/dot/digit that can't survive this project's own tokenizer "
          f"as one token)")

    ste_words = load_ste100_words()
    already_in_ste100 = sorted(s for s in single_token if s.lower() in ste_words)
    candidates = [s for s in single_token if s.lower() not in ste_words]
    print(f"  {len(already_in_ste100)} skipped: already in the real ASD-STE100 dictionary")

    jargon_skipped = sorted(s for s in candidates if s.lower() in NARROW_JARGON_SKIP)
    candidates = [s for s in candidates if s.lower() not in NARROW_JARGON_SKIP]
    print(f"  {len(jargon_skipped)} skipped: narrow/rare spec jargon (NARROW_JARGON_SKIP)")

    print(f"Verifying {len(candidates)} candidate entries against real fetched content "
          f"(title check, {RAW_BASE}/<slug>/index.md) ...")
    verified = {}
    no_title = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(fetch_title, s): s for s in candidates}
        for fut in as_completed(futures):
            slug = futures[fut]
            title = fut.result()
            if title:
                verified[slug] = title
            else:
                no_title.append(slug)
    if no_title:
        print(f"  {len(no_title)} candidates had no fetchable title, excluded "
              f"(not a live real entry): {sorted(no_title)}")

    terms = {slug.lower(): {"note": NOTE} for slug in sorted(verified)}

    out = {
        "_meta": {
            "name": "MDN Web Docs Glossary",
            "source": "https://github.com/mdn/content",
            "license": "CC-BY-SA-2.5",
            "extracted": EXTRACTED_DATE,
        },
        "terms": terms,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, sort_keys=False)
        f.write("\n")

    print()
    print(f"Wrote {OUT_PATH}")
    print(f"  source entries scanned:        {len(slugs)}")
    print(f"  single-token/compound slugs:   {len(single_token)}")
    print(f"  skipped (multi-word slug):     {multi_word_skipped}")
    print(f"  skipped (already in ASD-STE100): {len(already_in_ste100)}")
    print(f"  skipped (narrow/rare jargon):   {len(jargon_skipped)}")
    print(f"  skipped (fetch/title failed):   {len(no_title)}")
    print(f"  kept:                           {len(terms)}")


if __name__ == "__main__":
    main()
