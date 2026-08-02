"""Ruleset-agnostic flag deduplication.

A flag is {"kind": str, "label": str | None, "detail": dict, "text": str |
None}. "label" is the ruleset's own choice of what identifies one flag from
another of the same kind (e.g. the specific word, phrase, or modal involved)
-- computed once at construction time by the ruleset, opaque to this module.
Flags with no meaningful label (e.g. a bare semicolon violation, which has
nothing to key on beyond "this sentence had a semicolon") are never
deduplicated, on the same principle as `exclude_kinds`: collapsing them
would lose exactly the information needed to find and fix each one.
"""


def default_label(detail):
    """The identity a check's detail dict carries for display and dedup --
    whichever of "word"/"phrase"/"modal" it has, in that order, or None if
    none apply. A shared convention every ruleset's checks can reach for
    instead of each defining its own copy of this exact fallback chain."""
    return detail.get("word") or detail.get("phrase") or detail.get("modal")


def dedup_flags(flags, exclude_kinds=frozenset()):
    """Collapse repeated occurrences of the exact same (kind, label) into
    one flag with an 'occurrences' count added to its detail dict, keeping
    the first instance's 'text' as the example. `exclude_kinds` are kinds
    with no meaningful per-occurrence identity even when dedup DOES apply
    globally -- e.g. a document-level check that only ever emits one flag,
    or a per-sentence check (like a sentence-length violation) where every
    hit shares the same rule id and collapsing them would hide which
    sentences actually need fixing. Each ruleset passes its own set."""
    groups = {}
    order = []
    for f in flags:
        label = f.get("label")
        if f["kind"] in exclude_kinds or not label:
            key = ("__no_dedup__", id(f))
        else:
            key = (f["kind"], label.lower())
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
