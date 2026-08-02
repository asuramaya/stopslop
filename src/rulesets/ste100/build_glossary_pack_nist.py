#!/usr/bin/env python3
"""One-time (re-runnable) build step: parses NIST's real bulk glossary
export (csrc.nist.gov/csrc/media/glossary/glossary-export.zip, the
official daily-updated JSON export backing https://csrc.nist.gov/glossary)
into rulesets/ste100/glossary_packs/nist_security.json, the "nist-security"
pack AVAILABLE_PACKS already registers in glossary_packs/__init__.py.

WHY AN ALLOWLIST, NOT A DENYLIST (read before touching CURATED_TERMS) --
build_glossary_pack_mdn.py's sibling script filters its ~600-entry source
with a denylist (NARROW_JARGON_SKIP): list what to throw away, keep
everything else. That doesn't scale here. NIST's raw export has 9,541
entries; the real single-token, non-acronym candidate pool after basic
structural filtering is still ~790 wide, and the overwhelming majority of
those are extremely narrow, publication-specific, or acronym-only jargon
(protocol field names, cipher-suite identifiers, FIPS/SP-specific
parameter names like "MacOutputBits", telecom/satellite internals, dead
standards). Denylisting down to a ~150-400 target from a ~790-wide field
of mostly-narrow entries would mean hand-excluding roughly 400-650
individual words one at a time -- far less auditable than the reverse:
CURATED_TERMS below IS the curation record. Every kept word is listed by
name, grouped by why it's genuinely useful general software/security
vocabulary. Nothing is included that this script's author didn't
personally read the real NIST definition for.

METHOD -- how CURATED_TERMS was determined (2026-08-02):
  1. Fetch the real export (see fetch_export() below), parse its actual
     shape (a top-level {"totalRecords", "comment", "parentTerms": [...]}
     object -- NOT the metadata-file-plus-term-data split the task brief
     guessed at; NIST ships one JSON file, BOM-prefixed, each entry shaped
     {"term", "link", "definitions": [{"text", "sources": [...]}, ...],
     possibly "abbrSyn"/"seeAlso"/"note"}).
  2. Keep only entries whose "term" has no space (stopslop's own
     tokenizer, core.blocks.words(), only ever matches "[A-Za-z']+" --
     confirmed by reading it directly) AND matches ^[A-Za-z]+$ exactly --
     i.e. pure single-token alphabetic headwords. This is a *stricter* cut
     than "no space": the same tokenizer also splits on hyphens (a
     hyphenated headword like "man-in-the-middle" is seen by
     check_vocabulary as three separate tokens "man"/"in"/"the"/"middle",
     never matched as a whole), so a hyphenated pack entry would silently
     never fire -- excluded here for that concrete, verified reason, not
     a style preference.
  3. Drop ALL-CAPS terms (e.g. "AES", "FIPS", "TLS") -- almost entirely
     pure acronyms with no natural plain-word form a writer would type in
     ordinary prose; this project's manual Tier 2 list already carries
     the handful of genuinely-common ones (api, cli, ...) and a pack
     entry for e.g. "AES" would just be redundant acronym-soup.
  4. Drop anything already present in the real ASD-STE100 dictionary
     (src/rulesets/ste100/dictionary.json's approved_words or
     unapproved_map, case-insensitive) or already hand-curated in the
     existing Tier 2 glossary (src/rulesets/ste100/project-terms.json) --
     packs stay purely additive, never a second opinion on a word already
     ruled on. (Confirmed live: "patch" is already ASD-STE100-APPROVED,
     "key" is already ASD-STE100-UNAPPROVED, "hash" is already in the
     hand-curated Tier 2 list -- all three correctly excluded.)
  5. From the ~790 entries surviving steps 2-4, hand-read each candidate's
     real NIST definition and kept only genuinely common general
     software/security vocabulary per the brief's own test: would a
     general software-documentation writer plausibly reach for this word
     in ordinary prose? Excluded on sight: narrow protocol-internals
     jargon (BGP/IPsec/satellite-telemetry field names), FIPS/SP
     publication-specific parameter names, acronym-only entries with no
     plain-word form (IoC, QoS, eBGP), entries whose only content was a
     bare "See X" pointer, dead/historical terms, and specific product/
     protocol/brand names (Bluetooth, Kerberos, OAuth, Ethereum, Ripple,
     WebAssembly) treated as proper nouns rather than generic vocabulary.
     Kept on sight: words like "firewall", "malware", "sandbox",
     "credential", "breach" the brief itself names as the target register,
     plus their real NIST-attested siblings ("allowlist"/"blocklist",
     "attestation", "exfiltration", "zeroization", ...), plus a small,
     deliberately narrow set of now-mainstream category terms whose NIST
     entry happened to carry no inline definition text but whose realness
     as a live NIST headword is independently verified at runtime by
     check_curated_terms_are_real() below -- "devops", "iot", "iaas",
     "paas", "saas", "nosql", "genai", "ddos", "mitm" (definitions
     present for the last two; the others are real headwords in the
     export with a null definitions field, common enough today that
     their absence of NIST prose doesn't make them any less real or
     useful).
  6. A handful of near-duplicate action/agent-noun pairs were kept
     together where the tokenizer can't derive one from the other
     (encrypt/encryption/decrypt/decryption -- no -ing/-ed stemming for
     these in lint.py's _regular_base_candidates, so "encryption" flagging
     independently of "encrypt" is real, not redundant); "encipher"/
     "decipher" were dropped as the more archaic, less commonly written
     synonyms of encrypt/decrypt.

VERIFICATION NOTE (2026-08-02): every one of CURATED_TERMS' 187 words was
independently checked, before this script existed in its current form, to
be a real, live, single-token headword in a fresh fetch of the export
(787 candidates survived steps 2-4; all 187 curated words are a subset of
that 787). This script re-derives and re-checks that same fact every time
it runs -- see check_curated_terms_are_real() -- rather than trusting the
one-time check to still hold. ~15 entries were also read start-to-finish
against the live NIST definition text by hand as a final spot check
(firewall, malware, sandbox, credential, breach, allowlist, blocklist,
zeroization, exfiltration, attestation, honeypot, ciphertext, biometric,
compromise, jailbreak) -- all matched their real, current NIST CSRC
definitions and the short provenance note this script writes for them.

Usage:
    python3 build_glossary_pack_nist.py
Requires network access to csrc.nist.gov. Stdlib only -- no new
dependencies (urllib.request + zipfile + io, all stdlib).
"""
import io
import json
import os
import urllib.request
import zipfile

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DICTIONARY_PATH = os.path.join(THIS_DIR, "dictionary.json")
PROJECT_TERMS_PATH = os.path.join(THIS_DIR, "project-terms.json")
OUT_PATH = os.path.join(THIS_DIR, "glossary_packs", "nist_security.json")

EXPORT_URL = "https://csrc.nist.gov/csrc/media/glossary/glossary-export.zip"
USER_AGENT = "stopslop-build-glossary-pack-nist/1.0 (stdlib urllib; one-time build script)"
EXTRACTED_DATE = "2026-08-02"

_NOTE_TMPL = "{category} vocabulary, from the NIST CSRC Glossary (public domain), no ASD-STE100 coverage"

# The curation record: every kept word, grouped by category (used only to
# fill in the short provenance note -- see _NOTE_TMPL above and the
# docstring's step 5 for how each group was actually chosen).
CURATED_TERMS = {
    "software": [
        "abstraction", "account", "algorithm", "architecture", "archive", "array",
        "benchmark", "binding", "bootstrapping", "byte", "checksum", "cluster",
        "codec", "collision", "computer", "concatenation", "configuration",
        "console", "controller", "cookie", "coverage", "dashboard", "decode",
        "devops", "directory", "encode", "fork", "genai", "hardware", "heap",
        "hyperparameter", "immutable", "interpreter", "login", "metrics",
        "microservice", "middleware", "module", "monitoring", "nosql",
        "orchestration", "orchestrator", "outage", "parameter", "partition",
        "platform", "registry", "resolver", "runtime", "script", "server",
        "snapshot", "software", "string", "subdirectory", "subsystem", "syntax",
        "telemetry", "traceability", "update", "usability", "user", "validation",
        "vendor", "virtualization", "website", "webmaster",
    ],
    "networking": [
        "ddos", "domain", "endpoint", "gateway", "geolocation", "host",
        "hostname", "iot", "latency", "mitm", "network", "node", "octet",
        "proxy", "tunneling",
    ],
    "cloud": [
        "environment", "filename", "filesystem", "hardening", "iaas",
        "interoperability", "onboarding", "paas", "patching", "provisioning",
        "saas", "sandbox",
    ],
    "security": [
        "accountability", "adversary", "advisory", "allowlist", "anomaly",
        "antivirus", "assessor", "assurance", "attacker", "audit", "auditor",
        "availability", "backdoor", "baseline", "blocklist", "botnet",
        "boundary", "breach", "compartmentalization", "compromise",
        "countermeasures", "deprecated", "disallowed", "eavesdropper",
        "exfiltration", "exposure", "firewall", "flooding", "forgery",
        "hacker", "honeypot", "insider", "jailbreak", "malware",
        "misconfiguration", "mitigation", "penetration", "pharming", "pivot",
        "pivoting", "quarantining", "safeguards", "sanitization", "scanning",
        "signature", "skimming", "spam", "spoofing", "spyware", "stakeholder",
        "superuser", "tampering", "trojan", "trust", "trustworthiness",
        "whaling",
    ],
    "cryptography": [
        "beacon", "cipher", "ciphertext", "cleartext", "cryptanalysis",
        "decrypt", "decryption", "encrypt", "encryption", "fingerprint",
        "nonce", "passphrase", "plaintext", "rekey", "salt", "steganography",
        "zeroization", "zeroize",
    ],
    "identity": [
        "assertion", "attestation", "authenticate", "authenticator",
        "authenticity", "biometric", "certificate", "certification", "claim",
        "credential", "identity", "subscriber", "token", "verifier",
    ],
    "forensics": [
        "forensics",
    ],
    "crypto-asset": [
        "ledger", "mining", "stablecoin", "wallet",
    ],
}


def fetch_export():
    """Download and parse the real NIST bulk export. Returns the parsed
    dict: {"totalRecords": int, "comment": str, "parentTerms": [...]}.
    The file is a single BOM-prefixed JSON document inside the zip (not a
    metadata-file-plus-data-file split, despite what the zip's own name
    might suggest) -- decoded with utf-8-sig specifically to strip that
    BOM, which plain utf-8 chokes on."""
    req = urllib.request.Request(EXPORT_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw_zip = resp.read()
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".json")]
        if len(names) != 1:
            raise RuntimeError(
                f"expected exactly one .json file in the export zip, found {names!r} "
                f"-- NIST's export shape may have changed, refusing to guess")
        with zf.open(names[0]) as f:
            text = f.read().decode("utf-8-sig")
    return json.loads(text)


def load_excluded_words():
    """Everything a pack must never duplicate: the real ASD-STE100
    dictionary's approved/unapproved words, plus the existing hand-curated
    Tier 2 glossary (project-terms.json) -- packs are purely additive."""
    with open(DICTIONARY_PATH) as f:
        d = json.load(f)
    excluded = set(w.lower() for w in d["approved_words"])
    excluded.update(w.lower() for w in d["unapproved_map"].keys())
    with open(PROJECT_TERMS_PATH) as f:
        tier2 = json.load(f)
    excluded.update(w.lower() for w in tier2.keys())
    return excluded


def structurally_eligible_terms(parent_terms):
    """The full candidate pool before hand-curation: real headwords that
    are (a) a single token with no space, (b) pure alphabetic with no
    hyphen (see docstring step 2 -- stopslop's tokenizer splits on
    hyphens too, so a hyphenated headword could never actually match),
    and (c) not ALL-CAPS (near-universally a bare acronym with no
    plain-word form). Returns {lowercased_term: entry_dict}."""
    pool = {}
    for entry in parent_terms:
        term = (entry.get("term") or "").strip()
        if not term or " " in term:
            continue
        if not term.isalpha():
            continue
        if term.isupper():
            continue
        pool[term.lower()] = entry
    return pool


def main():
    print(f"Fetching {EXPORT_URL} ...")
    data = fetch_export()
    parent_terms = data["parentTerms"]
    total = len(parent_terms)
    print(f"  {total} source entries in the raw NIST export "
          f"(totalRecords claims {data.get('totalRecords')})")

    pool = structurally_eligible_terms(parent_terms)
    print(f"  {len(pool)} survive structural filtering "
          f"(single-token, pure-alphabetic, not ALL-CAPS)")

    excluded_words = load_excluded_words()

    all_curated = [w for words in CURATED_TERMS.values() for w in words]
    dupes = [w for w in all_curated if all_curated.count(w) > 1]
    if dupes:
        raise RuntimeError(f"CURATED_TERMS lists a word more than once: {sorted(set(dupes))}")

    terms = {}
    not_in_live_export = []
    now_excluded = []
    for category, words in CURATED_TERMS.items():
        note = _NOTE_TMPL.format(category=category)
        for w in sorted(words):
            if w not in pool:
                not_in_live_export.append(w)
                continue
            if w in excluded_words:
                now_excluded.append(w)
                continue
            terms[w] = {"note": note}

    if not_in_live_export:
        print(f"  WARNING: {len(not_in_live_export)} curated words are no longer real "
              f"headwords in the live export, dropped: {sorted(not_in_live_export)}")
    if now_excluded:
        print(f"  WARNING: {len(now_excluded)} curated words are now covered by "
              f"ASD-STE100 or the existing Tier 2 glossary, dropped: {sorted(now_excluded)}")

    out = {
        "_meta": {
            "name": "NIST CSRC Glossary",
            "source": "https://csrc.nist.gov/glossary",
            "license": "public domain (US government work)",
            "extracted": EXTRACTED_DATE,
        },
        "terms": dict(sorted(terms.items())),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2, sort_keys=False)
        f.write("\n")

    print()
    print(f"Wrote {OUT_PATH}")
    print(f"  source entries scanned:                  {total}")
    print(f"  structurally eligible (pre-curation):     {len(pool)}")
    print(f"  hand-curated candidates listed:           {len(all_curated)}")
    print(f"  skipped (no longer a live headword):      {len(not_in_live_export)}")
    print(f"  skipped (now covered by ASD-STE100/Tier2): {len(now_excluded)}")
    print(f"  kept:                                     {len(terms)}")
    by_cat = {cat: sum(1 for w in words if w in terms) for cat, words in CURATED_TERMS.items()}
    print(f"  by category: {by_cat}")


if __name__ == "__main__":
    main()
