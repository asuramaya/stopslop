"""Checks page: pick a ruleset, tune each of its checks in place -- the
page the old select+edit fight (st.dataframe selects, st.data_editor
edits, never both) was actually about. Here every row is its own small
form; toggling a checkbox or changing a number posts straight to the
check it belongs to and gets back its own updated row, nothing else.
"""
import os

from fastapi import APIRouter, Form, Request

import rulesets
from core import config as core_config, history, terms as core_terms

from webui.deps import REPO_ROOT, render, templates
from webui.routes_watch import HISTORY_PATH, _relative_time

router = APIRouter()


def _checkable_rulesets():
    return [m.RULESET_ID for m in rulesets.list_rulesets() if "checks" in m.CAPABILITIES]


def _last_fired(ruleset_id):
    """{check_id: ts} of the newest gate event naming each check --
    joined into the table so "which row just fired" needs no page
    switch, same as dashboard.py's own _last_fired()."""
    events = history.read_history_deduped(HISTORY_PATH)
    out = {}
    for e in events:
        if e.get("ruleset") != ruleset_id:
            continue
        ts = e.get("ts", 0)
        for kind in e.get("kinds") or []:
            if ts > out.get(kind, 0):
                out[kind] = ts
    return out


def _rows(ruleset_id):
    module = rulesets.get_ruleset(ruleset_id)
    checks = module.list_checks()
    config = module.list_check_config() if "check_config" in module.CAPABILITIES else {}
    lists = getattr(module, "TERM_LISTS", {})
    fired = _last_fired(ruleset_id)
    rows = []
    for check_id, meta in sorted(checks.items()):
        spec = config.get(check_id, {})
        rows.append({
            "id": check_id,
            "catches": meta["catches"],
            "instead": meta["instead"],
            "enabled": meta["enabled"],
            "threshold": spec.get("threshold"),
            "action": spec.get("action"),
            "params": spec.get("params", {}),
            "lists": [lid for lid, s in lists.items() if s.get("feeds") == check_id],
            "last_fired": _relative_time(fired[check_id]) if check_id in fired else "",
        })
    return module, rows


def _routed_caption(ruleset_id):
    rules = [r for r in core_config.load_rules(REPO_ROOT)
             if ruleset_id in (r.get("ruleset"), r.get("embedded_prose"))]
    globs = [r["glob"] for r in rules if r.get("ruleset") == ruleset_id]
    embedded = [r["glob"] for r in rules if r.get("embedded_prose") == ruleset_id]
    module = rulesets.get_ruleset(ruleset_id)
    own = set(module.list_checks())
    exempt = [(r["glob"], [c for c in r["disable"] if c in own])
              for r in rules if r.get("disable")]
    exempt = [(g, cs) for g, cs in exempt if cs]
    return {"globs": globs, "embedded": embedded, "exempt": exempt}


def _synthetic_path_for_glob(glob):
    return glob.replace("*", "__probe__") if "*" in glob else glob


@router.get("/checks")
def checks_page(request: Request, ruleset: str = ""):
    ids = _checkable_rulesets()
    ruleset_id = ruleset if ruleset in ids else (ids[0] if ids else None)
    if ruleset_id is None:
        return render(request, "checks.html", "checks", {"ruleset_ids": [], "ruleset_id": None})
    module, rows = _rows(ruleset_id)
    return render(request, "checks.html", "checks", {
        "ruleset_ids": ids,
        "ruleset_id": ruleset_id,
        "rows": rows,
        "routed": _routed_caption(ruleset_id),
        "tunable": [r for r in rows if r["params"]],
        "listed": [r for r in rows if r["lists"]],
    })


@router.post("/checks/{ruleset_id}/{check_id}/toggle")
async def toggle_check(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    module.set_checks_enabled({check_id: "enabled" in form})
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return templates.TemplateResponse(request, "fragments/check_row.html", {"row": row, "ruleset_id": ruleset_id})


@router.post("/checks/{ruleset_id}/{check_id}/config")
async def set_check_config(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    threshold = int(form["threshold"]) if form.get("threshold") else None
    action = form.get("action") or None
    module.set_check_config(check_id, threshold=threshold, action=action)
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return templates.TemplateResponse(request, "fragments/check_row.html", {"row": row, "ruleset_id": ruleset_id})


@router.post("/checks/{ruleset_id}/{check_id}/param")
async def set_check_param(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    name = form["name"]
    value = int(form["value"])
    module.set_check_config(check_id, **{name: value})
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return templates.TemplateResponse(request, "fragments/check_params.html", {"row": row, "ruleset_id": ruleset_id})


@router.post("/checks/{ruleset_id}/playground")
async def playground(request: Request, ruleset_id: str, text: str = Form(...)):
    module = rulesets.get_ruleset(ruleset_id)
    stored = core_config.rule_packs(REPO_ROOT)
    glob = next((g for g, r, _p in stored if r == ruleset_id), None)
    full = os.path.join(REPO_ROOT, _synthetic_path_for_glob(glob)) if glob else None

    if not text.strip():
        return templates.TemplateResponse(request, "fragments/playground_result.html", {"empty": True})

    result = module.lint_and_gate(text, file_path=full)
    blocking = module.blocking_semantic_flags(result["semantic_flags"])
    non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
    fixed = module.apply_mechanical_fixes(text, file_path=full) if result["mechanical_violations"] else None

    return templates.TemplateResponse(request, "fragments/playground_result.html", {
        "blocking": blocking, "mechanical": result["mechanical_violations"],
        "non_blocking": non_blocking, "fixed": fixed,
    })
