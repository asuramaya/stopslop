"""Vocabulary page: every word in every list, searchable; any single
list, browsable with add/remove/restore. Mirrors dashboard.py's own
vocabulary_page()/_word_matches()/_term_list_block() split -- search is
the primary verb, the per-list browser below it covers curation.
"""
from fastapi import APIRouter, Request

import rulesets
from core import config as core_config, glossary_packs, terms as core_terms

from webui.deps import REPO_ROOT, fragment_response, render, templates

router = APIRouter()


def _pack_rows():
    rows = [dict(meta, id=pack_id) for pack_id, meta in glossary_packs.list_packs().items()]
    return sorted(rows, key=lambda m: m["name"])


def _effective_lists(module):
    return core_config.effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                             module.RULESET_ID, REPO_ROOT)


def _list_entries():
    """[(module, list_id, spec), ...] across every ruleset that declares
    term lists, sorted the same way configure.py's own selector was --
    a project's own custom_term_lists declarations included, since a
    custom list is exactly as browsable as a built-in one."""
    return [(m, lid, spec) for m in rulesets.list_rulesets()
            for lid, spec in sorted(_effective_lists(m).items())]


def _custom_list_ids(ruleset_id):
    return set(core_config.custom_term_lists(REPO_ROOT, ruleset_id))


def _list_block(ruleset_id, list_id):
    module = rulesets.get_ruleset(ruleset_id)
    spec = _effective_lists(module)[list_id]
    layers = core_terms.resolve(spec, REPO_ROOT, module.RULESET_ID, list_id)
    suppressed = core_terms.suppressed_terms(REPO_ROOT, module.RULESET_ID, list_id)

    rows = []
    for term in sorted(layers["effective"]):
        if term in layers["project"]:
            source = "yours"
        elif term in layers["packs"]:
            source = layers["packs"][term].get("pack", "pack")
        else:
            source = "built-in"
        rows.append({"term": term, "source": source,
                      "note": layers["effective"][term].get("note", "") or ""})

    packs_feeding = [(g, p.get(list_id)) for g, r, p in core_config.rule_packs(REPO_ROOT)
                     if r == ruleset_id and p and p.get(list_id)]

    return {
        "ruleset_id": ruleset_id, "list_id": list_id, "spec": spec,
        "polarity": spec.get("polarity"), "accepts_additions": spec.get("accepts_additions", True),
        "rows": rows, "suppressed": sorted(suppressed),
        "packs_feeding": packs_feeding,
        "is_custom": list_id in _custom_list_ids(ruleset_id),
    }


def _section_context(entries, ruleset_id=None, list_id=None):
    """Context for fragments/vocabulary_section.html -- the picker
    <select> plus the selected list's block, always rendered together so
    a list add/remove refreshes both in one swap (the picker's own
    option set changes exactly when the block it points at might no
    longer exist). Falls back to the first available list when the
    requested one is missing or unset, same fallback vocabulary_page()
    itself uses."""
    ruleset_ids = [m.RULESET_ID for m in rulesets.list_rulesets()
                   if "terms" in getattr(m, "CAPABILITIES", frozenset())]
    if ruleset_id is None or list_id is None or not any(
            m.RULESET_ID == ruleset_id and lid == list_id for m, lid, _s in entries):
        if not entries:
            return {"entries": entries, "ruleset_id": None, "list_id": None,
                    "block": None, "ruleset_ids": ruleset_ids,
                    "selected_spec": None, "selected_is_custom": False}
        module, list_id, _spec = entries[0]
        ruleset_id = module.RULESET_ID
    custom = core_config.custom_term_lists(REPO_ROOT, ruleset_id).get(list_id)
    return {"entries": entries, "ruleset_id": ruleset_id, "list_id": list_id,
            "block": _list_block(ruleset_id, list_id), "ruleset_ids": ruleset_ids,
            "selected_spec": custom, "selected_is_custom": custom is not None}


@router.get("/vocabulary/packs")
def packs_fragment(request: Request):
    return templates.TemplateResponse(request, "fragments/pack_list.html", {"packs": _pack_rows()})


@router.post("/vocabulary/packs/add")
async def add_pack(request: Request):
    form = await request.form()
    error = None
    try:
        glossary_packs.add_pack(
            pack_id=(form.get("pack_id") or "").strip(),
            name=(form.get("name") or "").strip(),
            source=(form.get("source") or "").strip(),
            license=(form.get("license") or "").strip(),
            content_kind=(form.get("content_kind") or "word").strip(),
            terms=glossary_packs.parse_pack_terms_text(form.get("terms")),
        )
    except ValueError as e:
        error = str(e)
    return fragment_response(request, "fragments/pack_list.html", {"packs": _pack_rows()}, error=error)


# Registered BEFORE /vocabulary/{ruleset_id}/{list_id}/remove on purpose:
# Starlette matches routes in registration order, not by specificity, and
# both are 3 path segments ("packs"/{pack_id}/"remove" vs {ruleset_id}/
# {list_id}/"remove") -- the generic pattern would otherwise swallow this
# one first, binding ruleset_id="packs" and raising UnknownRulesetError.
@router.post("/vocabulary/packs/{pack_id}/remove")
async def remove_pack(request: Request, pack_id: str):
    error = None
    try:
        glossary_packs.remove_pack(pack_id)
    except ValueError as e:
        error = str(e)
    return fragment_response(request, "fragments/pack_list.html", {"packs": _pack_rows()}, error=error)


@router.post("/vocabulary/lists/add")
async def add_list(request: Request):
    form = await request.form()
    ruleset_id = (form.get("ruleset_id") or "").strip()
    list_id = (form.get("list_id") or "").strip().lower()
    error = None
    try:
        module = rulesets.get_ruleset(ruleset_id)
        core_config.add_custom_term_list(
            REPO_ROOT, ruleset_id, list_id, getattr(module, "TERM_LISTS", {}),
            label=form.get("label"),
            polarity=form.get("polarity") if form.get("polarity") in ("allow", "deny") else "deny",
            accepts_additions=form.get("accepts_additions") == "on",
            accepts_packs=form.get("accepts_packs") == "on",
            content_kind=form.get("content_kind") or "word",
        )
    except rulesets.UnknownRulesetError as e:
        error = str(e)
        list_id = None
    except ValueError as e:
        error = str(e)
    entries = _list_entries()
    ctx = _section_context(entries, ruleset_id, list_id)
    return fragment_response(request, "fragments/vocabulary_section.html", ctx, error=error)


@router.post("/vocabulary/lists/{ruleset_id}/{list_id}/update")
async def update_list(request: Request, ruleset_id: str, list_id: str):
    """Change a custom list's own spec: label, polarity, and what it
    accepts. The id is not editable -- every term already registered
    under this list is filed under that id, so changing it would strand
    them, and a fresh id plus a re-add is the honest way to do that.

    Refused for a built-in list, whose spec lives in its ruleset's own
    TERM_LISTS in source. A `feeds` binding set by the Checks page is
    carried through untouched: it belongs to the check-to-list wiring,
    not to anything on this form.
    """
    error = None
    existing = core_config.custom_term_lists(REPO_ROOT, ruleset_id).get(list_id)
    if existing is None:
        error = (f"no custom list {list_id!r} on {ruleset_id!r} to edit -- "
                  "a built-in list's spec lives in its ruleset's source")
    else:
        form = await request.form()
        spec = dict(existing)
        spec["label"] = (form.get("label") or "").strip() or list_id
        if form.get("polarity") in ("allow", "deny"):
            spec["polarity"] = form.get("polarity")
        spec["accepts_additions"] = form.get("accepts_additions") == "on"
        spec["accepts_packs"] = form.get("accepts_packs") == "on"
        spec["content_kind"] = (form.get("content_kind") or "").strip() or "word"
        core_config.save_custom_term_list(REPO_ROOT, ruleset_id, list_id, spec)
    entries = _list_entries()
    ctx = _section_context(entries, ruleset_id, list_id)
    return fragment_response(request, "fragments/vocabulary_section.html", ctx, error=error)


# Registered BEFORE /vocabulary/{ruleset_id}/{list_id}/remove for the same
# reason the pack routes are: this is a distinct path shape (4 segments,
# "lists" literal first) so it never collides in practice, but matching
# the established precedent here keeps the ordering rule uniform rather
# than "safe until someone reshapes one of these paths later".
@router.post("/vocabulary/lists/{ruleset_id}/{list_id}/remove")
async def remove_list(request: Request, ruleset_id: str, list_id: str):
    error = None
    if not core_config.delete_custom_term_list(REPO_ROOT, ruleset_id, list_id):
        error = f"no custom list {list_id!r} on {ruleset_id!r} to remove"
    entries = _list_entries()
    ctx = _section_context(entries)
    return fragment_response(request, "fragments/vocabulary_section.html", ctx, error=error)


@router.get("/vocabulary")
def vocabulary_page(request: Request):
    entries = _list_entries()
    ctx = _section_context(entries)
    ctx["packs"] = _pack_rows()
    return render(request, "vocabulary.html", "vocabulary", ctx)


@router.get("/vocabulary/list")
def vocabulary_list_fragment(request: Request, rl: str):
    ruleset_id, list_id = rl.split("|", 1)
    return templates.TemplateResponse(
        request, "fragments/vocabulary_list.html",
        {"block": _list_block(ruleset_id, list_id), "ruleset_id": ruleset_id, "list_id": list_id})


@router.get("/vocabulary/search")
def vocabulary_search(request: Request, q: str = ""):
    needle = q.strip().lower()
    if not needle:
        return templates.TemplateResponse(request, "fragments/vocabulary_search.html", {"hits": None})

    rows = core_terms.term_index(rulesets, REPO_ROOT)
    for row in rows:
        row["list_label"] = f"{row['ruleset']}.{row['list']}"
        row["is_suppressed"] = False
    for row in core_terms.suppressed_index(rulesets, REPO_ROOT):
        rows.append({"term": row["term"], "ruleset": row["ruleset"], "list": row["list"],
                      "list_label": f"{row['ruleset']}.{row['list']} (suppressed)",
                      "note": "", "is_suppressed": True})

    hits = [r for r in rows if needle in r["term"].lower() or needle in r.get("note", "").lower()]
    return templates.TemplateResponse(request, "fragments/vocabulary_search.html", {"hits": hits})


@router.post("/vocabulary/{ruleset_id}/{list_id}/add")
async def add_term(request: Request, ruleset_id: str, list_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    term = (form.get("term") or "").strip()
    note = form.get("note") or ""
    force = form.get("force") or False
    refused = None
    if term:
        result = module.add_term(list_id, term, note, force=force)
        if not result.get("ok"):
            refused = {"term": term, "note": note, "message": result.get("message", "")}
    return templates.TemplateResponse(request, "fragments/vocabulary_list.html", {
        "block": _list_block(ruleset_id, list_id), "ruleset_id": ruleset_id,
        "list_id": list_id, "refused": refused,
    })


@router.post("/vocabulary/{ruleset_id}/{list_id}/remove")
async def remove_term(request: Request, ruleset_id: str, list_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    term = (form.get("term") or "").strip()
    if term:
        module.remove_term(list_id, term)
    return templates.TemplateResponse(
        request, "fragments/vocabulary_list.html",
        {"block": _list_block(ruleset_id, list_id), "ruleset_id": ruleset_id, "list_id": list_id})


@router.post("/vocabulary/{ruleset_id}/{list_id}/restore")
async def restore_term(request: Request, ruleset_id: str, list_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    term = (form.get("term") or "").strip()
    if term:
        module.add_term(list_id, term)
    return templates.TemplateResponse(
        request, "fragments/vocabulary_list.html",
        {"block": _list_block(ruleset_id, list_id), "ruleset_id": ruleset_id, "list_id": list_id})
