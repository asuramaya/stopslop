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


def remedies_for(module, check_id):
    """Which actions resolve a flag of this kind, derived from the ruleset's
    own declarations rather than a hardcoded table.

    A term list names the check it feeds and its polarity, which is enough
    to say whether a false positive is fixed by ALLOWING a word or by
    un-flagging one. Every check can also be switched off, project-wide or
    for one path.

    This exists because the gate told an agent what was wrong and never what
    to do about it: a deny listed its flags, and at the retry cap said "ask
    the user". An agent blocked on a legitimate domain word had add_term
    sitting right there with no pointer to it. The surface where you learn
    you are blocked was disconnected from the surface that unblocks you."""
    out = []
    ruleset_id = getattr(module, "RULESET_ID", "?")
    for list_id, spec in sorted(getattr(module, "TERM_LISTS", {}).items()):
        if spec.get("feeds") != check_id:
            continue
        if spec.get("polarity") == "allow":
            if spec.get("accepts_additions", True):
                out.append(f"add_term('{list_id}', '<word>') on {ruleset_id} "
                            f"-- an allow list: stops a legitimate word being flagged")
        else:
            out.append(f"remove_term('{list_id}', '<word>') on {ruleset_id} "
                        f"-- a deny list: stops one word being flagged")
    out.append(f"set_checks({{'{check_id}': false}}) on {ruleset_id}, or "
               f"\"disable\": [\"{check_id}\"] on this path's routing rule")
    return out
