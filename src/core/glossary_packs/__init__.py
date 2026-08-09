"""Registry of optional bulk vocabulary packs -- bulk, pre-curated glossary
content pulled from real, license-checked external sources, each shipped
as its own JSON file in this directory. Lives in core/, not inside any one
ruleset's own package: a pack is "approved-vocabulary content a project
can opt into," not an ste100-specific concept -- ste100's Tier-2 glossary
is simply the first (and so far only) real consumer, the same way core/
config.py's other generic project-config helpers (disabled_checks,
check_config, custom wordlist terms) aren't owned by whichever ruleset
happens to use them. Moved here from rulesets/ste100/glossary_packs/
during this session's modularity-consistency pass -- git history is
preserved (a rename, not a delete+recreate).

Disabled by default for every pack (see core.config.enabled_glossary_packs):
a pack existing in code must never change behavior for an unconfigured
clone, the exact invariant the ruleset registry itself already guarantees
for routing. A user opts a pack in per project, via stopslop.config.json's
"glossary_packs" key, the same way a ruleset gets routed to a glob pattern
-- packs are to the glossary what rulesets are to the gate: modular, and
off until named in config.

Each pack file has the shape:
    {
      "_meta": {"name": ..., "source": ..., "license": ..., "extracted": ...},
      "terms": {"word": {"note": "..."}, ...}
    }

See rulesets/ste100/build_glossary_pack_*.py for how each pack's terms.json
was produced from its real upstream source -- re-runnable, not hand-typed,
the same verified-not-just-trusted precedent build_dictionary.py already
set for the real ASD-STE100 dictionary itself. The build scripts stay in
rulesets/ste100/: their curation logic (excluding words the real ASD-STE100
dictionary already covers) is genuinely ste100-specific, even though the
packs they produce are not.
"""
import json
import os

_PACKS_DIR = os.path.dirname(os.path.abspath(__file__))

# License is informational here (surfaced to the user before they enable a
# pack) -- the actual legal treatment (attribution-only vs share-alike vs
# public domain) is documented in NOTICE, not re-derived from this string.
#
# A pack entry names its SOURCE and nothing else. There is deliberately no
# field here saying which ruleset or which term list a pack feeds.
#
# There used to be: every entry carried target=("ste100", "project_terms").
# That was the same ancestry these files were moved out of ste100's own
# directory to escape, surviving one level up. The MDN Web Docs glossary is
# not ASD-STE100 content; it is a body of words that ste100 HAPPENS to read
# as an allow list. Naming the consumer inside the pack made the pack
# author responsible for knowing who would read it -- coupling pointing the
# wrong way -- and made three reasonable things impossible: one pack
# feeding two rulesets, one pack feeding two lists, and a pack read at the
# opposite POLARITY (a future jargon-flagging ruleset would want exactly
# these words as a deny list).
#
# The binding now lives in stopslop.config.json, on the routing rule,
# beside the glob and the ruleset -- see core.config.packs_for_path. A pack
# is inert content; aiming it at a list is a project decision, made where
# every other path-scoped decision is already made.
# Each pack declares its CONTENT KIND, and each term list declares what kind
# it can read (core/terms.py's pack_kind_admissible). This is the structural
# half of the promise made when a pack's `target` field was removed: killing
# "this pack is FOR ste100" was right, because a pack is a body of words with
# no opinion about who reads it -- but it replaced nominal coupling with
# nothing, and the attach control would happily offer MDN's 262 domain nouns
# to slopwatch.filler_verb, whose entries are REGEX PATTERNS ("enables?",
# "leverages?"). A warning is not a type system. A kind says what the content
# IS, without naming a consumer, so one pack still feeds many rulesets, at
# either polarity, while the nonsense becomes unrepresentable.
AVAILABLE_PACKS = {
    "microsoft-style-guide": {
        "content_kind": "word",
        "name": "Microsoft Writing Style Guide word list",
        "source": "https://github.com/MicrosoftDocs/microsoft-style-guide",
        "license": "CC-BY-4.0",
    },
    "mdn-glossary": {
        "content_kind": "word",
        "name": "MDN Web Docs Glossary",
        "source": "https://github.com/mdn/content",
        "license": "CC-BY-SA-2.5",
    },
    "nist-security": {
        "content_kind": "word",
        "name": "NIST CSRC Glossary",
        "source": "https://csrc.nist.gov/glossary",
        "license": "public domain (US government work)",
    },
}


class UnknownPackError(Exception):
    pass


def _pack_path(pack_id):
    return os.path.join(_PACKS_DIR, pack_id.replace("-", "_") + ".json")


def load_pack_terms(pack_id):
    """{"word": {"note": ...}, ...} for one pack, or {} if the pack is
    registered but its data file hasn't been built yet -- never raises for
    a missing file, only for a pack_id nothing in AVAILABLE_PACKS knows
    about, matching UnknownRulesetError's own loud-on-typo shape."""
    if pack_id not in AVAILABLE_PACKS:
        raise UnknownPackError(
            f"no glossary pack registered as {pack_id!r} -- known: {sorted(AVAILABLE_PACKS)}")
    path = _pack_path(pack_id)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f).get("terms", {})


def pack_meta(pack_id):
    """AVAILABLE_PACKS' own entry, plus the real term count and the pack
    file's own _meta block (extraction date etc.) if the file exists."""
    if pack_id not in AVAILABLE_PACKS:
        raise UnknownPackError(
            f"no glossary pack registered as {pack_id!r} -- known: {sorted(AVAILABLE_PACKS)}")
    meta = dict(AVAILABLE_PACKS[pack_id])
    path = _pack_path(pack_id)
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        meta["term_count"] = len(data.get("terms", {}))
        meta.update(data.get("_meta", {}))
    else:
        meta["term_count"] = 0
    return meta


def list_packs():
    return {pack_id: pack_meta(pack_id) for pack_id in sorted(AVAILABLE_PACKS)}
