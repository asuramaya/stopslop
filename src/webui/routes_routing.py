"""Routing page: the editable first-match-wins rules table. The one page
where a PATH is genuinely the subject -- rule order decides everything
and used to be invisible-but-for-row-position in a Streamlit data_editor
with no reorder gesture at all. Real move-up/move-down buttons here make
the thing that actually decides behavior a thing you can actually do.
"""
import os

from fastapi import APIRouter, Request

import rulesets
from core import config as core_config, glossary_packs, terms as core_terms

from webui.deps import REPO_ROOT, render, templates

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
    lists = getattr(module, "TERM_LISTS", {})
    pack_lists = sorted(lid for lid, spec in lists.items() if spec.get("accepts_packs"))
    known_checks = _known_checks_for_rule(rule)
    return {
        "index": index, "rule": rule, "pack_lists": pack_lists,
        "lists": lists, "known_checks": known_checks,
        "available_packs": glossary_packs.AVAILABLE_PACKS,
    }


def _ruleset_ids():
    return [m.RULESET_ID for m in rulesets.list_rulesets()]


@router.get("/routing")
def routing_page(request: Request):
    return render(request, "routing.html", "routing",
                  {"rows": _rows(), "ruleset_ids": _ruleset_ids(), "focus": None})


@router.get("/routing/table")
def routing_table_fragment(request: Request):
    return templates.TemplateResponse(
        request, "fragments/routing_table.html", {"rows": _rows(), "ruleset_ids": _ruleset_ids()})


@router.post("/routing/{index}/glob")
async def update_glob(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    form = await request.form()
    new_glob = (form.get("glob") or "").strip()
    if new_glob and 0 <= index < len(rules):
        rules[index] = dict(rules[index], glob=new_glob)
        _save(rules)
    return routing_table_fragment(request)


@router.post("/routing/{index}/ruleset")
async def update_ruleset(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    form = await request.form()
    new_ruleset = form.get("ruleset") or None
    if 0 <= index < len(rules):
        rules[index] = dict(rules[index], ruleset=new_ruleset)
        _save(rules)
    return routing_table_fragment(request)


@router.post("/routing/{index}/move")
async def move_rule(request: Request, index: int, direction: str = "up"):
    rules = core_config.load_rules(REPO_ROOT)
    other = index - 1 if direction == "up" else index + 1
    if 0 <= index < len(rules) and 0 <= other < len(rules):
        rules[index], rules[other] = rules[other], rules[index]
        _save(rules)
    return routing_table_fragment(request)


@router.post("/routing/{index}/delete")
async def delete_rule(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    if 0 <= index < len(rules):
        del rules[index]
        _save(rules)
    return routing_table_fragment(request)


@router.post("/routing/add")
async def add_rule(request: Request):
    rules = core_config.load_rules(REPO_ROOT)
    form = await request.form()
    glob = (form.get("glob") or "").strip()
    if glob:
        rules.append({"glob": glob, "ruleset": form.get("ruleset") or None})
        _save(rules)
    return routing_table_fragment(request)


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


@router.post("/routing/{index}/packs")
async def set_packs(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    if not (0 <= index < len(rules)):
        return focus(request, index)
    rule = rules[index]
    module = rulesets.get_ruleset(rule["ruleset"])
    form = await request.form()
    list_id = form.get("list_id")
    pack_ids = form.getlist("pack_ids")
    spec = module.TERM_LISTS.get(list_id, {})
    admissible = lambda pid: core_terms.pack_kind_admissible(
        spec, glossary_packs.AVAILABLE_PACKS.get(pid, {}))
    core_config.set_rule_packs(REPO_ROOT, rule["glob"], list_id, pack_ids,
                                known_packs=glossary_packs.AVAILABLE_PACKS, admissible=admissible)
    return focus(request, index)


@router.post("/routing/{index}/disable")
async def set_disable(request: Request, index: int):
    rules = core_config.load_rules(REPO_ROOT)
    if not (0 <= index < len(rules)):
        return focus(request, index)
    rule = rules[index]
    form = await request.form()
    check_ids = form.getlist("check_ids")
    known = _known_checks_for_rule(rule)
    core_config.set_rule_disable(REPO_ROOT, rule["glob"], check_ids, known_checks=known)
    return focus(request, index)
