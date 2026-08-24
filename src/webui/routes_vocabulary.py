"""Vocabulary page: every word in every list, searchable; any single
list, browsable with add/remove/restore. Mirrors dashboard.py's own
vocabulary_page()/_word_matches()/_term_list_block() split -- search is
the primary verb, the per-list browser below it covers curation.
"""
from fastapi import APIRouter, Request

import rulesets
from core import config as core_config, terms as core_terms

from webui.deps import REPO_ROOT, render, templates

router = APIRouter()


def _list_entries():
    """[(module, list_id, spec), ...] across every ruleset that declares
    term lists, sorted the same way configure.py's own selector was."""
    return [(m, lid, spec) for m in rulesets.list_rulesets()
            for lid, spec in sorted(getattr(m, "TERM_LISTS", {}).items())]


def _list_block(ruleset_id, list_id):
    module = rulesets.get_ruleset(ruleset_id)
    spec = module.TERM_LISTS[list_id]
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
    }


@router.get("/vocabulary")
def vocabulary_page(request: Request):
    entries = _list_entries()
    if not entries:
        return render(request, "vocabulary.html", "vocabulary", {"entries": []})
    module, list_id, _spec = entries[0]
    return render(request, "vocabulary.html", "vocabulary", {
        "entries": entries,
        "ruleset_id": module.RULESET_ID,
        "list_id": list_id,
        "block": _list_block(module.RULESET_ID, list_id),
    })


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
