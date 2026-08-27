"""Routing page: the editable first-match-wins rules table. The one page
where a PATH is genuinely the subject -- rule order decides everything
and used to be invisible-but-for-row-position in a Streamlit data_editor
with no reorder gesture at all. Real move-up/move-down buttons here make
the thing that actually decides behavior a thing you can actually do.
"""
import os

from fastapi import APIRouter, Request

import rulesets
from core import config as core_config, custom_rulesets as core_custom_rulesets
from core import glossary_packs, terms as core_terms

from webui.deps import REPO_ROOT, error_banner, fragment_response, render, templates

router = APIRouter()


def _pack_count(rule):
    return sum(len(v) for v in (rule.get("packs") or {}).values())


def _rows():
    return [{"glob": r["glob"], "ruleset": r.get("ruleset") or "",
              "packs": _pack_count(r), "index": i}
             for i, r in enumerate(core_config.load_rules(REPO_ROOT))]


def _save(rules):
    """`rules` is the full ordered list of {"glob", "ruleset"} dicts --
    save_rules() itself inherits each glob's existing packs/disable/
    embedded_prose, so callers here never need to carry those forward
    by hand."""
    incoming = [{"glob": r["glob"], "ruleset": r["ruleset"] or None} for r in rules]
    core_config.save_rules(REPO_ROOT, incoming, rulesets)


def _known_checks_for_rule(rule):
    known = {}
    for ruleset_id in {rule.get("ruleset"), rule.get("embedded_prose")} - {None}:
        module = rulesets.get_ruleset(ruleset_id)
        if "checks" in module.CAPABILITIES:
            for check_id in module.list_checks():
                known[check_id] = ruleset_id
    return known


def _focus_context(index):
    rules = core_config.load_rules(REPO_ROOT)
    if index is None or not (0 <= index < len(rules)) or not rules[index].get("ruleset"):
        return None
    rule = rules[index]
    module = rulesets.get_ruleset(rule["ruleset"])
    lists = core_config.effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                              module.RULESET_ID, REPO_ROOT)
    pack_lists = sorted(lid for lid, spec in lists.items() if spec.get("accepts_packs"))
    known_checks = _known_checks_for_rule(rule)
    return {
        "index": index, "rule": rule, "pack_lists": pack_lists,
        "lists": lists, "known_checks": known_checks,
        "available_packs": glossary_packs.AVAILABLE_PACKS,
    }


def _ruleset_ids():
    return [m.RULESET_ID for m in rulesets.list_rulesets()]


def _ruleset_rows():
    return [{"id": m.RULESET_ID, "name": m.RULESET_NAME,
              "is_custom": rulesets.is_custom_ruleset(m.RULESET_ID)}
            for m in rulesets.list_rulesets()]


@router.get("/routing")
def routing_page(request: Request):
    return render(request, "routing.html", "routing", {
        "rows": _rows(), "ruleset_ids": _ruleset_ids(), "focus": None,
        "ruleset_rows": _ruleset_rows(), "ruleset_errors": rulesets.custom_ruleset_errors(),
    })


@router.get("/routing/table")
def routing_table_fragment(request: Request):
    return templates.TemplateResponse(
        request, "fragments/routing_table.html", {"rows": _rows(), "ruleset_ids": _ruleset_ids()})


def _table_response(request, error=None):
    return fragment_response(request, "fragments/routing_table.html",
                              {"rows": _rows(), "ruleset_ids": _ruleset_ids()}, error=error)


@router.post("/routing/{index}/glob")
async def update_glob(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    form = await request.form()
    new_glob = (form.get("glob") or "").strip()
    error = None
    if new_glob and 0 <= index < len(rules):
        rules[index] = dict(rules[index], glob=new_glob)
        try:
            _save(rules)
        except ValueError as e:
            error = str(e)
    return _table_response(request, error=error)


@router.post("/routing/{index}/ruleset")
async def update_ruleset(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    form = await request.form()
    new_ruleset = form.get("ruleset") or None
    error = None
    if 0 <= index < len(rules):
        rules[index] = dict(rules[index], ruleset=new_ruleset)
        try:
            _save(rules)
        except ValueError as e:
            error = str(e)
    return _table_response(request, error=error)


@router.post("/routing/{index}/move")
async def move_rule(request: Request, index: int, direction: str = "up"):
    rules = core_config.load_rules(REPO_ROOT)
    other = index - 1 if direction == "up" else index + 1
    error = None
    if 0 <= index < len(rules) and 0 <= other < len(rules):
        rules[index], rules[other] = rules[other], rules[index]
        try:
            _save(rules)
        except ValueError as e:
            error = str(e)
    return _table_response(request, error=error)


@router.post("/routing/{index}/delete")
async def delete_rule(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    error = None
    if 0 <= index < len(rules):
        del rules[index]
        try:
            _save(rules)
        except ValueError as e:
            error = str(e)
    return _table_response(request, error=error)


@router.post("/routing/add")
async def add_rule(request: Request):
    rules = core_config.load_rules(REPO_ROOT)
    form = await request.form()
    glob = (form.get("glob") or "").strip()
    error = None
    if glob:
        rules.append({"glob": glob, "ruleset": form.get("ruleset") or None})
        try:
            _save(rules)
        except ValueError as e:
            error = str(e)
    return _table_response(request, error=error)


@router.get("/routing/probe")
def probe(request: Request, path: str = ""):
    result = None
    if path.strip():
        rule = core_config.matching_rule(os.path.join(REPO_ROOT, path.strip()), REPO_ROOT)
        result = {"path": path.strip(), "rule": rule}
    return templates.TemplateResponse(request, "fragments/routing_probe.html", {"result": result})


@router.get("/routing/focus")
def focus(request: Request, index: int = -1):
    ctx = _focus_context(index) if index >= 0 else None
    return templates.TemplateResponse(request, "fragments/routing_focus.html", {"focus": ctx, "rows": _rows()})


def _focus_response(request, index, error=None):
    ctx = _focus_context(index) if index >= 0 else None
    return fragment_response(request, "fragments/routing_focus.html",
                              {"focus": ctx, "rows": _rows()}, error=error)


@router.post("/routing/{index}/packs")
async def set_packs(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    if not (0 <= index < len(rules)):
        return _focus_response(request, index)
    rule = rules[index]
    module = rulesets.get_ruleset(rule["ruleset"])
    form = await request.form()
    list_id = form.get("list_id")
    pack_ids = form.getlist("pack_ids")
    spec = core_config.effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                             module.RULESET_ID, REPO_ROOT).get(list_id, {})
    admissible = lambda pid: core_terms.pack_kind_admissible(
        spec, glossary_packs.AVAILABLE_PACKS.get(pid, {}))
    error = None
    try:
        core_config.set_rule_packs(REPO_ROOT, rule["glob"], list_id, pack_ids,
                                    known_packs=glossary_packs.AVAILABLE_PACKS, admissible=admissible)
    except ValueError as e:
        error = str(e)
    return _focus_response(request, index, error=error)


@router.post("/routing/{index}/disable")
async def set_disable(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    if not (0 <= index < len(rules)):
        return _focus_response(request, index)
    rule = rules[index]
    form = await request.form()
    check_ids = form.getlist("check_ids")
    known = _known_checks_for_rule(rule)
    error = None
    try:
        core_config.set_rule_disable(REPO_ROOT, rule["glob"], check_ids, known_checks=known)
    except ValueError as e:
        error = str(e)
    return _focus_response(request, index, error=error)


def _ruleset_section_response(request, error=None):
    """Both fragments in one response: ruleset_section.html as the normal
    swap target, plus routing_table.html out-of-band -- adding or
    removing a ruleset changes that table's own ruleset picker too, and
    it would otherwise go stale until the next full page load."""
    from fastapi.responses import HTMLResponse
    body = templates.get_template("fragments/ruleset_section.html").render(
        {"ruleset_rows": _ruleset_rows(), "ruleset_errors": rulesets.custom_ruleset_errors()},
        request=request)
    body += templates.get_template("fragments/routing_table.html").render(
        {"rows": _rows(), "ruleset_ids": _ruleset_ids(), "oob": True}, request=request)
    return HTMLResponse(body + error_banner(error))


@router.post("/routing/rulesets/add")
async def add_ruleset(request: Request):
    form = await request.form()
    error = None
    try:
        existing_ids = {m.RULESET_ID for m in rulesets.list_rulesets()}
        core_custom_rulesets.scaffold_ruleset(
            REPO_ROOT, form.get("ruleset_id", ""), form.get("name", ""), existing_ids)
        rulesets.rescan_custom_rulesets()
    except Exception as e:
        # Broad on purpose, matching routes_checks.py's own add_custom_check
        # -- scaffold_ruleset today only ever raises ValueError/
        # InvalidCustomRulesetError, and rescan_custom_rulesets() never
        # raises at all (see its own docstring), but a narrow catch here
        # is exactly what let a bare FileExistsError escape as a raw 500
        # before it was fixed at the source.
        error = str(e)
    return _ruleset_section_response(request, error=error)


@router.post("/routing/rulesets/{ruleset_id}/remove")
async def remove_ruleset(request: Request, ruleset_id: str):
    error = None
    if not rulesets.is_custom_ruleset(ruleset_id):
        error = f"{ruleset_id!r} is a built-in ruleset -- only a custom ruleset can be removed"
    else:
        referencing = [r["glob"] for r in core_config.load_rules(REPO_ROOT)
                       if ruleset_id in (r.get("ruleset"), r.get("embedded_prose"))]
        if referencing:
            error = (f"{ruleset_id!r} is still routed from " + ", ".join(referencing)
                      + " -- repoint or delete those rules first")
        else:
            rulesets.unregister_ruleset(ruleset_id)
            core_custom_rulesets.remove_ruleset(REPO_ROOT, ruleset_id)
    return _ruleset_section_response(request, error=error)
