"""One primitive for every named collection of words a ruleset checks against.

Before this module there were two parallel mechanisms with different names,
different storage keys, different APIs and different capability flags, for
what is structurally the same thing:

  * ste100's "glossary" -- register_term/unregister_term/list_terms, plus a
    separate un-registered pair of pack functions nothing in the registry
    knew about.
  * slopwatch's and codewatch's "wordlists" -- add_wordlist_term/
    remove_wordlist_term/list_wordlists.

They looked like different concepts only because of POLARITY. ste100's list
is an ALLOW list (words the ASD-STE100 standard forbids that this project
permits anyway); slopwatch's and codewatch's are DENY lists (words that are
fine English but that the ruleset flags). "Glossary" became the name for
allow and "wordlist" the name for deny purely because ste100 was written
first -- an accident of ancestry, not a real distinction. The proof it was
never real: codewatch obviously wants an allow list ("`data` and `handler`
are fine in this repo") and structurally could not have one, because
allow-shaped storage was spelled "glossary" and glossary was ste100's word.

So: one concept, a TERM LIST, declared by the ruleset that owns it, with an
explicit `polarity` field and three layers resolved in a fixed precedence:

    built_in  ->  packs  ->  project

`built_in` is whatever the ruleset ships in code or a data file. `packs` is
opt-in bulk content (see core/glossary_packs/). `project` is what a human
deliberately registered. Later layers win on conflict: a human registration
is the most deliberate and most recent act, so it beats a pack, which beats
a built-in.

Two properties this module exists to guarantee:

1. **Packs are resolved per PATH, not per ruleset.** A pack is domain
   content -- NIST security vocabulary is right for `docs/security/` and
   wrong for `blog/`. Domain is a property of the text, not of the ruleset
   and not of the project. Binding packs to a ruleset id (the old
   "glossary_packs": {"ste100": [...]} key) forced the pack list to be the
   union of every domain in the repo, because one ruleset handles all prose.
   Packs now live on the same first-match-wins routing rule that already
   resolves which ruleset gates a path, so one matched rule fully explains
   why a word passed in a given file. That explainability is the property
   worth protecting, and it is exactly what a machine-global -> project ->
   ruleset config CASCADE would have destroyed; this project deliberately
   does not have one.

   The rule also names WHICH LIST each pack feeds. A pack carries no
   opinion about that -- the MDN Web Docs glossary is not ste100 content,
   it is a body of words ste100 happens to read as an allow list. See
   core/glossary_packs/__init__.py for why naming the consumer inside the
   pack was the same ancestry problem one level up.

2. **A pack cannot override the prohibitions of the ruleset reading it.** A
   ruleset may declare `pack_admissible` on a list: a predicate deciding
   whether bulk-imported content is allowed to introduce a given term. The
   three built-in packs collide with ASD-STE100's forbidden list
   exactly zero times -- but only because their build scripts hand-exclude
   words the dictionary already covers. That made the invariant a property
   of how those three files happened to be produced, not of the model. Once
   packs are first-class and extensible, a fourth pack containing `utilize`
   would silently un-forbid a word the standard explicitly replaces: a gate
   that quietly stops gating. Rejections are reported, not swallowed, so the
   UI can surface them. A PROJECT registration can still override a
   prohibition (with `force` and a stated reason) because that is a
   deliberate human act; a bulk import never is.
"""
import json
import os

from core import config as _config

ALLOW = "allow"
DENY = "deny"

TERMS_KEY = "terms"
_LEGACY_TERMS_KEY = "wordlists"
_LEGACY_PACKS_KEY = "glossary_packs"


class UnknownTermListError(Exception):
    """A list_id the owning ruleset never declared in TERM_LISTS."""


# Which (project_root, config_file) pairs this process has already checked
# for legacy keys. The migration is idempotent, so re-running it is only a
# waste, never a correctness problem -- but every read path funnels through
# here, and a stat+parse per lookup on a live gate is not free. One check
# per process per config file, done lazily so no entry point (gate, CLI,
# MCP server, dashboard) has to remember to trigger it explicitly.
_migration_checked = set()


def _ensure_migrated(project_root, config_file=None):
    key = (project_root, config_file)
    if key in _migration_checked:
        return
    _migration_checked.add(key)
    try:
        migrate_legacy_keys(project_root, config_file=config_file)
    except Exception as ignored:
        # Deliberately swallowed: this runs on the read path of a LIVE
        # GATE. A config file that can't be rewritten (read-only checkout,
        # a race with another writer) must degrade to "legacy keys stay
        # where they are and still resolve" -- never to a crashed write
        # hook. The same never-break-the-gate posture history.log_event
        # and lint's own pack resolution already take.
        pass


# --- storage: the project layer ---------------------------------------

def project_terms(project_root, ruleset_id, list_id, config_file=None):
    """The terms a human deliberately registered for one (ruleset, list),
    as {"term": {"note": ..., ...}}. Empty with no config file or no entry
    -- the same no-config-file-changes-nothing invariant every other knob
    in core/config.py already gives."""
    _ensure_migrated(project_root, config_file)
    path = config_file or _config.config_path(project_root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return data.get(TERMS_KEY, {}).get(ruleset_id, {}).get(list_id, {})


def save_project_terms(project_root, ruleset_id, list_id, terms, config_file=None):
    """Write the project layer for one (ruleset, list), preserving every
    other top-level key already in the file -- same clobber-avoidance shape
    as core/config.py's other save_* helpers."""
    _ensure_migrated(project_root, config_file)
    path = config_file or _config.config_path(project_root)
    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    data.setdefault(TERMS_KEY, {}).setdefault(ruleset_id, {})[list_id] = terms
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# --- one-time migration off the pre-unification keys -------------------

def migrate_legacy_keys(project_root, config_file=None):
    """Rename the pre-unification project-terms key:

        "wordlists": {rs: {list: {...}}}  ->  "terms": {rs: {list: {...}}}

    Best-effort and idempotent, matching the never-break-the-gate pattern
    used for every other migration in this project: any failure leaves the
    original key untouched rather than raising into a live gate call.
    Returns True if the file was rewritten.

    The PACK half of the old config lives in migrate_legacy_packs below,
    not here -- reshaping it needs to know which term list the packs feed,
    and this function has no way to know that."""
    path = config_file or _config.config_path(project_root)
    if not os.path.exists(path):
        return False
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    changed = False

    if _LEGACY_TERMS_KEY in data:
        legacy = data.pop(_LEGACY_TERMS_KEY)
        merged = data.setdefault(TERMS_KEY, {})
        for ruleset_id, lists in legacy.items():
            for list_id, terms in lists.items():
                # An already-migrated list wins: never clobber newer content
                # with the stale copy the old key still happens to hold.
                merged.setdefault(ruleset_id, {}).setdefault(list_id, terms)
        changed = True

    if not changed:
        return False
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except OSError:
        return False
    return True


def migrate_legacy_packs(project_root, ruleset_id, list_id, config_file=None):
    """Reshape the two pre-unification pack layouts onto the routing rules:

        "glossary_packs": {rs: [pack_id]}          (ruleset-keyed, top level)
        rule["packs"]: [pack_id]                    (per-rule, but list-blind)
                    ->  rule["packs"]: {list_id: [pack_id]}

    Called from _pack_layer, not from _ensure_migrated, because it needs a
    list id and only the resolving caller has one. That is not a
    workaround: the whole point of the reshape is that a pack has no
    opinion about which list it feeds, so the binding cannot be derived
    from the pack or from the ruleset -- it has to come from whoever is
    asking. The first pack-accepting list of a ruleset to ask inherits that
    ruleset's old packs, which reproduces the old behaviour exactly, since
    "glossary_packs" only ever fed one list.

    Best-effort and idempotent, same never-break-the-gate posture as
    migrate_legacy_keys."""
    path = config_file or _config.config_path(project_root)
    if not os.path.exists(path):
        return False
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    legacy_top = (data.get(_LEGACY_PACKS_KEY) or {}).get(ruleset_id, [])
    rules = [dict(r) for r in data.get("rulesets", _config.DEFAULT_RULES)]
    changed = False

    for rule in rules:
        if rule.get("ruleset") != ruleset_id:
            continue
        packs = rule.get("packs")
        if isinstance(packs, list):          # per-rule but list-blind
            rule["packs"] = {list_id: list(packs)}
            changed = True
        elif packs is None and legacy_top:   # ruleset-keyed, top level
            rule["packs"] = {list_id: list(legacy_top)}
            changed = True

    if _LEGACY_PACKS_KEY in data:
        remaining = {k: v for k, v in data[_LEGACY_PACKS_KEY].items()
                      if k != ruleset_id}
        if remaining:
            data[_LEGACY_PACKS_KEY] = remaining
        else:
            data.pop(_LEGACY_PACKS_KEY)
        changed = True

    if not changed:
        return False
    data["rulesets"] = rules
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except OSError:
        return False
    return True


# --- layered resolution ------------------------------------------------

def _built_in_layer(spec):
    """Whatever the ruleset ships for this list.

    `built_ins` may be a plain collection of terms, or a MAPPING of term ->
    metadata. The mapping form exists because some built-in vocabulary
    carries data the checks use -- ASD-STE100's forbidden words each name
    an approved replacement -- and a layer that could only hold bare
    strings was the reason that dictionary sat outside the term-list model
    entirely, invisible to every view built on it."""
    raw = spec.get("built_ins", ())
    if isinstance(raw, dict):
        return {t: (dict(m) if isinstance(m, dict) else {"note": str(m)})
                for t, m in raw.items()}
    return {t: {} for t in raw}


def suppressed_terms(project_root, ruleset_id, list_id, config_file=None):
    """Just the tombstones for one list, as a set.

    Deliberately cheaper than resolve(): a live gate needs to know what a
    project has removed from a built-in list, and building the whole layered
    view to find out would mean materialising every built-in on every
    write. This reads one small mapping that is almost always empty."""
    stored = project_terms(project_root, ruleset_id, list_id, config_file=config_file)
    return frozenset(t for t, m in stored.items() if m.get("removed"))


def pack_kind_admissible(list_spec, pack_meta):
    """Can this list read this pack's content? (bool, reason).

    A list holding REGEX PATTERNS cannot read a bag of plain words as if
    they were patterns, and a list matched as multi-word PHRASES gets
    nothing useful from single nouns. Neither side names the other: the
    pack says what it is, the list says what it reads, and the mismatch
    becomes unrepresentable rather than merely discouraged.

    A list may widen itself with `accepts_kinds`; the default is exactly
    its own content_kind, which is the conservative reading."""
    wanted = tuple(list_spec.get("accepts_kinds")
                   or (list_spec.get("content_kind"),))
    kind = pack_meta.get("content_kind")
    if kind is None or None in wanted:
        # Undeclared on either side: allow, and say so. Refusing here would
        # break every pack and list written before kinds existed.
        return True, "content kind undeclared on one side -- not checked"
    if kind in wanted:
        return True, ""
    return False, (f"this list holds {'/'.join(wanted)} entries and the pack "
                   f"holds {kind} entries")


def _pack_layer(spec, project_root, ruleset_id, list_id, file_path, config_file):
    """Pack content for one list, scoped to the routing rule that matches
    `file_path`, with the list's own `pack_admissible` guard applied.
    Returns (accepted, rejected).

    Which packs feed this list comes from the CONFIG, not from the packs --
    a pack is inert content with no opinion about who reads it. Never
    raises: a missing pack file or an unresolvable path yields empty layers
    rather than breaking a live gate, the same principle
    core.history.log_event's own OSError handling uses."""
    if not spec.get("accepts_packs"):
        return {}, {}
    from core import glossary_packs

    accepted, rejected = {}, {}
    admissible = spec.get("pack_admissible")
    try:
        migrate_legacy_packs(project_root, ruleset_id, list_id, config_file=config_file)
        pack_ids = _config.packs_for_path(project_root, file_path, list_id=list_id,
                                           config_file=config_file)
    except Exception:
        return {}, {}
    for pack_id in pack_ids:
        try:
            terms = glossary_packs.load_pack_terms(pack_id)
            meta = glossary_packs.AVAILABLE_PACKS.get(pack_id, {})
        except Exception:
            continue        # an unknown or unbuilt pack contributes nothing
        # A binding written before kinds existed, or by hand-editing the
        # config, still resolves through here. Drop it rather than feed a
        # list content it cannot read, and record why.
        ok, why = pack_kind_admissible(spec, meta)
        if not ok:
            rejected[f"(whole pack {pack_id})"] = why
            continue
        for term, entry in terms.items():
            if admissible is not None and not admissible(term):
                rejected[term] = pack_id
                continue
            accepted[term] = dict(entry, pack=pack_id)
    return accepted, rejected


def resolve(spec, project_root, ruleset_id, list_id, file_path=None, config_file=None):
    """The full layered view of one term list for one path.

    Returns {"built_in", "packs", "project", "suppressed", "rejected",
    "effective"} -- every layer kept separately so a caller can explain
    WHERE a term came from, not just that it is present. `effective` is
    what a check should actually match against.

    The stack is a union MINUS a subtraction. Without the subtraction a
    list could only ever grow: a built-in was unreachable (its words live
    in a Python literal inside the ruleset) and a pack was all-or-nothing,
    so the only way to escape one wrong word was to disable a whole check
    or detach a whole pack. A project may now suppress any single term from
    any layer, recorded as a tombstone in the project layer -- the same
    place additions live, since "I decided this word does not belong here"
    is the same kind of act as "I decided this one does."""
    _ensure_migrated(project_root, config_file)
    built_in = _built_in_layer(spec)
    packs, rejected = _pack_layer(
        spec, project_root, ruleset_id, list_id, file_path, config_file)
    stored = project_terms(project_root, ruleset_id, list_id, config_file=config_file)
    project = {t: m for t, m in stored.items() if not m.get("removed")}
    tombstones = {t: m for t, m in stored.items() if m.get("removed")}

    effective = {}
    effective.update(built_in)
    effective.update(packs)
    effective.update(project)

    suppressed = {}
    for term in tombstones:
        origin = ("a pack" if term in packs else
                   "built-in" if term in built_in else "nothing")
        if effective.pop(term, None) is not None:
            suppressed[term] = origin
        else:
            # A tombstone for a term no layer supplies any more (the pack was
            # detached, the ruleset dropped the built-in). Harmless, but
            # reported so it can be cleaned up rather than lingering unseen.
            suppressed[term] = "nothing"

    return {"built_in": built_in, "packs": packs, "project": project,
            "suppressed": suppressed, "rejected": rejected,
            "effective": effective}


def effective_terms(spec, project_root, ruleset_id, list_id, file_path=None, config_file=None):
    """Just the merged term -> metadata mapping a check matches against.
    Convenience wrapper over resolve() for the hot path, which never needs
    the per-layer breakdown."""
    return resolve(spec, project_root, ruleset_id, list_id,
                   file_path=file_path, config_file=config_file)["effective"]


# --- the capability surface rulesets delegate to -----------------------

def _require_known(term_lists, list_id):
    if list_id not in term_lists:
        raise UnknownTermListError(
            f"unknown term list {list_id!r} -- known: {sorted(term_lists)}")


def list_term_lists(ruleset_id, term_lists, project_root, file_path=None, config_file=None):
    """A JSON-serialisable view of every term list this ruleset owns: its
    label, polarity, per-layer counts, the project's own terms in full, and
    any pack terms the list's guard refused. This is what the dashboard's
    Vocabulary tab and `stopslop.py terms` both render."""
    out = {}
    for list_id, spec in sorted(term_lists.items()):
        layers = resolve(spec, project_root, ruleset_id, list_id,
                          file_path=file_path, config_file=config_file)
        out[list_id] = {
            "label": spec.get("label", list_id),
            "description": spec.get("description", ""),
            "polarity": spec.get("polarity", DENY),
            "accepts_packs": bool(spec.get("accepts_packs")),
            "built_in_count": len(layers["built_in"]),
            "pack_count": len(layers["packs"]),
            "project_count": len(layers["project"]),
            "effective_count": len(layers["effective"]),
            "suppressed_count": len(layers["suppressed"]),
            "project_terms": layers["project"],
            "pack_terms": sorted(layers["packs"]),
            "suppressed": layers["suppressed"],
            "rejected": layers["rejected"],
        }
    return out


def add_term(ruleset_id, term_lists, project_root, list_id, term, note="",
             force=False, validator=None, config_file=None):
    """Register one term into a list's project layer.

    Single-term and deliberate on purpose -- the same "one word at a time,
    on the record" shape ste100's register_term has always had, now shared
    by every ruleset. `validator` is the ruleset's optional hook for lists
    that have a real external standard to check against: it returns
    (result_or_None, extra_metadata). A non-None result short-circuits
    (already approved, or refused pending `force`); extra metadata is
    stored alongside the note, which is how "this registration knowingly
    overrides a prohibition" stays visible on the record afterwards."""
    _require_known(term_lists, list_id)
    term = term.strip().lower()
    if not term:
        return {"ok": False, "status": "refused", "message": "term cannot be empty"}

    terms = project_terms(project_root, ruleset_id, list_id, config_file=config_file)
    if terms.get(term, {}).get("removed"):
        # Adding back something previously suppressed just lifts the
        # tombstone -- it does not create a project term that shadows the
        # built-in or pack the word actually came from.
        #
        # This runs BEFORE the accepts_additions gate and before the
        # validator, on purpose. A restore is not an addition: the word was
        # already in the list and this project took it out. Gating it as an
        # addition made a closed list a one-way door -- suppress a
        # dictionary word and it could never come back -- which quietly
        # broke the restorability the whole subtraction model promises.
        del terms[term]
        save_project_terms(project_root, ruleset_id, list_id, terms,
                            config_file=config_file)
        return {"ok": True, "status": "restored",
                "message": f"restored '{term}' to {list_id}"}

    # A list may be CLOSED to genuinely NEW words while staying open to
    # suppression and restore. ste100's approved_words and unapproved_words
    # are the published ASD-STE100 dictionary: "the standard also approves
    # X" is a claim a project cannot make, and project_terms exists to say
    # it locally instead. Removing stays legal -- "we do not accept this
    # dictionary word here" is real curation.
    #
    # Refused, not raised: an unopenable list is a normal answer to a normal
    # request, and every other refusal on this path returns the same shape.
    # ste100 previously enforced this by raising UnknownTermListError from
    # its own wrapper, which was two untruths at once -- the list is
    # perfectly known, and the caller had done nothing wrong.
    if not term_lists[list_id].get("accepts_additions", True):
        return {"ok": False, "status": "refused",
                "message": f"'{list_id}' does not take new words -- it is "
                            f"published reference data, not a project list. "
                            f"Words can still be removed from it, and "
                            f"anything removed can be restored."}

    extra = {}
    if validator is not None:
        verdict, extra = validator(term, force)
        if verdict is not None:
            return verdict
    if term in terms:
        return {"ok": True, "status": "no-op",
                "message": f"'{term}' is already registered in {list_id} "
                            f"({terms[term].get('note') or 'no note'})"}
    terms[term] = dict(extra, note=note)
    save_project_terms(project_root, ruleset_id, list_id, terms, config_file=config_file)
    return {"ok": True, "status": "registered",
            "message": f"registered '{term}' in {list_id}", "metadata": extra}


def remove_term(ruleset_id, term_lists, project_root, list_id, term,
                 file_path=None, config_file=None):
    """Take one term out of a list, whatever layer it came from.

    Removing a term the project itself added simply deletes it. Removing a
    built-in or a pack term cannot delete anything -- those words live in a
    ruleset's source file or a built-in JSON pack -- so it records a
    tombstone in the project layer instead, which resolve() subtracts. That
    is the difference between a list that can only grow and one a person
    can actually curate."""
    _require_known(term_lists, list_id)
    term = term.strip().lower()
    stored = project_terms(project_root, ruleset_id, list_id, config_file=config_file)

    if term in stored and not stored[term].get("removed"):
        del stored[term]
        save_project_terms(project_root, ruleset_id, list_id, stored,
                            config_file=config_file)
        return {"ok": True, "status": "removed",
                "message": f"removed '{term}' from {list_id}"}

    if stored.get(term, {}).get("removed"):
        return {"ok": True, "status": "no-op",
                "message": f"'{term}' is already suppressed in {list_id}"}

    layers = resolve(term_lists[list_id], project_root, ruleset_id, list_id,
                      file_path=file_path, config_file=config_file)
    if term not in layers["effective"]:
        return {"ok": True, "status": "no-op",
                "message": f"'{term}' is not in {list_id}"}

    origin = "a pack" if term in layers["packs"] else "the ruleset's built-ins"
    stored[term] = {"note": f"suppressed from {origin}", "removed": True}
    save_project_terms(project_root, ruleset_id, list_id, stored,
                        config_file=config_file)
    return {"ok": True, "status": "suppressed",
            "message": f"suppressed '{term}' in {list_id} (came from {origin})"}


def term_index(registry, project_root, file_path=None, config_file=None):
    """Every term in the project, flattened into one list of rows.

    This is the shape the vocabulary UI actually wants: one searchable,
    filterable table tagged by ruleset, list, source and polarity -- rather
    than the same three-section block (counts, packs, your terms) repeated
    per ruleset, with the built-in and pack words never shown at all. A
    number saying "716 from packs" is not an answer to "why did this word
    pass"; the word has to be findable.

    `registry` is passed in rather than imported, the same way
    core.config.resolve_ruleset takes it -- core stays free of any
    dependency on the ruleset registry."""
    rows = []
    for module in registry.list_rulesets():
        if "terms" not in getattr(module, "CAPABILITIES", frozenset()):
            continue
        lists = _config.effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                              module.RULESET_ID, project_root, config_file)
        for list_id, spec in sorted(lists.items()):
            layers = resolve(spec, project_root, module.RULESET_ID, list_id,
                              file_path=file_path, config_file=config_file)
            polarity = spec.get("polarity", DENY)
            for term in sorted(layers["effective"]):
                meta = layers["effective"][term]
                if term in layers["project"]:
                    source = "yours"
                elif term in layers["packs"]:
                    source = layers["packs"][term].get("pack", "pack")
                else:
                    source = "built-in"
                rows.append({
                    "term": term,
                    "ruleset": module.RULESET_ID,
                    "list": list_id,
                    "source": source,
                    "polarity": polarity,
                    "note": meta.get("note", "") or "",
                })
    return rows


def suppressed_index(registry, project_root, file_path=None, config_file=None):
    """Every term a project has suppressed, so a removal stays visible and
    reversible instead of looking like the word was never there."""
    rows = []
    for module in registry.list_rulesets():
        if "terms" not in getattr(module, "CAPABILITIES", frozenset()):
            continue
        lists = _config.effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                              module.RULESET_ID, project_root, config_file)
        for list_id, spec in sorted(lists.items()):
            layers = resolve(spec, project_root, module.RULESET_ID, list_id,
                              file_path=file_path, config_file=config_file)
            for term, origin in sorted(layers["suppressed"].items()):
                rows.append({"term": term, "ruleset": module.RULESET_ID,
                              "list": list_id, "was from": origin})
    return rows
