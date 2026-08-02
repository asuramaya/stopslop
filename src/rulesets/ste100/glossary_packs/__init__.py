"""Registry of ste100's optional vocabulary packs -- bulk, pre-curated
Tier 2 glossary content pulled from real, license-checked external
sources, each shipped as its own JSON file in this directory. Disabled
by default for every pack (see core.config.enabled_glossary_packs): a
pack existing in code must never change behavior for an unconfigured
clone, the exact invariant the ruleset registry itself already
guarantees for routing. A user opts a pack in per project, via
stopslop.config.json's "glossary_packs" key, the same way a ruleset
gets routed to a glob pattern -- packs are to the glossary what
rulesets are to the gate: modular, and off until named in config.

Each pack file has the shape:
    {
      "_meta": {"name": ..., "source": ..., "license": ..., "extracted": ...},
      "terms": {"word": {"note": "..."}, ...}
    }

See build_glossary_pack_*.py for how each pack's terms.json was produced
from its real upstream source -- re-runnable, not hand-typed, the same
verified-not-just-trusted precedent build_dictionary.py already set for
the real ASD-STE100 dictionary itself.
"""
import json
import os

_PACKS_DIR = os.path.dirname(os.path.abspath(__file__))

# License is informational here (surfaced to the user before they enable a
# pack) -- the actual legal treatment (attribution-only vs share-alike vs
# public domain) is documented in NOTICE, not re-derived from this string.
AVAILABLE_PACKS = {
    "microsoft-style-guide": {
        "name": "Microsoft Writing Style Guide word list",
        "source": "https://github.com/MicrosoftDocs/microsoft-style-guide",
        "license": "CC-BY-4.0",
    },
    "mdn-glossary": {
        "name": "MDN Web Docs Glossary",
        "source": "https://github.com/mdn/content",
        "license": "CC-BY-SA-2.5",
    },
    "nist-security": {
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
