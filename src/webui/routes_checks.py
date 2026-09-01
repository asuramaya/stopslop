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

from webui.deps import REPO_ROOT, fragment_response, render, templates
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
    configurable = "check_config" in module.CAPABILITIES
    custom_capable = "custom_checks" in module.CAPABILITIES
    custom_ids = set(module.custom_check_ids()) if custom_capable else set()
    checks = module.list_checks()
    config = module.list_check_config() if configurable else {}
    lists = core_config.effective_term_lists(getattr(module, "TERM_LISTS", {}),
                                              module.RULESET_ID, REPO_ROOT)
    fired = _last_fired(ruleset_id)
    rows = []
    for check_id, meta in sorted(checks.items()):
        spec = config.get(check_id, {})
        rows.append({
            "id": check_id,
            "catches": meta["catches"],
            "instead": meta["instead"],
            "unit": meta["unit"],
            "enabled": meta["enabled"],
            "configurable": configurable,
            "is_custom": check_id in custom_ids,
            "threshold": spec.get("threshold"),
            "action": spec.get("action"),
            "params": spec.get("params", {}),
            "lists": [lid for lid, s in lists.items() if s.get("feeds") == check_id],
            "last_fired": _relative_time(fired[check_id]) if check_id in fired else "",
        })
    return module, rows


def _section_context(ruleset_id):
    module, rows = _rows(ruleset_id)
    custom_capable = "custom_checks" in module.CAPABILITIES
    return module, {
        "rows": rows,
        "ruleset_id": ruleset_id,
        "tunable": [r for r in rows if r["params"]],
        "listed": [r for r in rows if r["lists"]],
        "custom_capable": custom_capable,
        "custom_check_units": module.custom_check_units() if custom_capable else [],
        # Only a CUSTOM list's `feeds` is ours to rewrite (a built-in
        # one's spec lives in read-only Python source, already pointed
        # at whatever built-in check it feeds) -- so this is the whole
        # set a custom check could ever be offered as a binding target,
        # not filtered further by current binding state; add/update
        # below refuse a list already feeding a DIFFERENT check rather
        # than silently reassigning it.
        "bindable_lists": core_config.custom_term_lists(REPO_ROOT, ruleset_id) if custom_capable else {},
    }


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
    module, section = _section_context(ruleset_id)
    return render(request, "checks.html", "checks", {
        "ruleset_ids": ids,
        "ruleset_id": ruleset_id,
        "routed": _routed_caption(ruleset_id),
        **section,
    })


@router.post("/checks/{ruleset_id}/{check_id}/toggle")
async def toggle_check(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    error = None
    try:
        module.set_checks_enabled({check_id: "enabled" in form})
    except ValueError as e:
        error = str(e)
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return fragment_response(request, "fragments/check_row.html",
                              {"row": row, "ruleset_id": ruleset_id}, error=error)


@router.post("/checks/{ruleset_id}/{check_id}/config")
async def set_check_config(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    error = None
    if "check_config" not in module.CAPABILITIES:
        error = f"{ruleset_id!r} checks have no tunable threshold/action"
    else:
        try:
            threshold = int(form["threshold"]) if form.get("threshold") else None
            action = form.get("action") or None
            module.set_check_config(check_id, threshold=threshold, action=action)
        except ValueError as e:
            error = str(e)
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return fragment_response(request, "fragments/check_row.html",
                              {"row": row, "ruleset_id": ruleset_id}, error=error)


@router.post("/checks/{ruleset_id}/{check_id}/param")
async def set_check_param(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    error = None
    if "check_config" not in module.CAPABILITIES:
        error = f"{ruleset_id!r} checks have no tunable settings"
    else:
        try:
            name = form["name"]
            value = int(form["value"])
            module.set_check_config(check_id, **{name: value})
        except ValueError as e:
            error = str(e)
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return fragment_response(request, "fragments/check_params.html",
                              {"row": row, "ruleset_id": ruleset_id}, error=error)


def _single_row(ruleset_id, check_id):
    module, rows = _rows(ruleset_id)
    row = next(r for r in rows if r["id"] == check_id)
    return module, row


def _check_terms_list_available(ruleset_id, check_id, terms_list):
    """Read-only half of the binding: raises if `terms_list` already
    feeds a DIFFERENT check, rather than silently reassigning it
    (mirrors add_custom_check's own id-collision refusal one level up).
    Called BEFORE the check file itself is written, so a conflict here
    never creates a check whose vocabulary binding then fails -- true
    validate-then-write for the whole add/update, not just the file."""
    terms_list = terms_list or None
    if not terms_list:
        return
    feeds = core_config.custom_term_lists(REPO_ROOT, ruleset_id).get(terms_list, {}).get("feeds")
    if feeds not in (None, check_id):
        raise ValueError(f"list {terms_list!r} already feeds check {feeds!r} "
                          f"-- unbind it there first")


def _apply_terms_list_binding(ruleset_id, check_id, terms_list):
    """The write half: called only after the check file itself saved
    successfully (and only after _check_terms_list_available already
    passed), so this never fails on a conflict -- it just moves the
    pointer, unbinding whatever the check used to feed first."""
    core_config.clear_feeds_for_check(REPO_ROOT, ruleset_id, check_id)
    if terms_list:
        core_config.set_custom_term_list_feeds(REPO_ROOT, ruleset_id, terms_list, check_id)


@router.get("/checks/{ruleset_id}/{check_id}/row")
def check_row_fragment(request: Request, ruleset_id: str, check_id: str):
    """The plain (non-editing) row -- Cancel's target, so backing out of
    an edit never needs a full-page reload."""
    module, row = _single_row(ruleset_id, check_id)
    return templates.TemplateResponse(request, "fragments/check_row.html",
                                       {"row": row, "ruleset_id": ruleset_id})


@router.get("/checks/{ruleset_id}/{check_id}/edit")
def edit_custom_check(request: Request, ruleset_id: str, check_id: str):
    """A custom check's matcher body is otherwise invisible once saved --
    this is both the only way to read it back and the form that edits
    it, prefilled from get_custom_check_fields()."""
    module = rulesets.get_ruleset(ruleset_id)
    if "custom_checks" not in module.CAPABILITIES or check_id not in module.custom_check_ids():
        error = (f"{ruleset_id!r} has no support for custom checks"
                  if "custom_checks" not in module.CAPABILITIES else
                  f"{check_id!r} is a built-in check -- only a custom check can be edited")
        module, row = _single_row(ruleset_id, check_id)
        return fragment_response(request, "fragments/check_row.html",
                                  {"row": row, "ruleset_id": ruleset_id}, error=error)
    fields = module.get_custom_check_fields(check_id)
    return templates.TemplateResponse(request, "fragments/check_edit_row.html", {
        "ruleset_id": ruleset_id, "check_id": check_id, "fields": fields,
        "custom_check_units": module.custom_check_units(),
        "bindable_lists": core_config.custom_term_lists(REPO_ROOT, ruleset_id),
    })


@router.post("/checks/{ruleset_id}/{check_id}/update")
async def update_custom_check(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    if "custom_checks" not in module.CAPABILITIES or check_id not in module.custom_check_ids():
        error = (f"{ruleset_id!r} has no support for custom checks"
                  if "custom_checks" not in module.CAPABILITIES else
                  f"{check_id!r} is a built-in check -- only a custom check can be edited")
        module, row = _single_row(ruleset_id, check_id)
        return fragment_response(request, "fragments/check_row.html",
                                  {"row": row, "ruleset_id": ruleset_id}, error=error)
    terms_list = form.get("terms_list") or None
    try:
        threshold = int(form.get("threshold") or 1)
        _check_terms_list_available(ruleset_id, check_id, terms_list)
        module.update_custom_check(
            check_id, form["unit"], form["catches"], form["instead"],
            threshold, form.get("action") or "warn", form["fn_body"], terms_list=terms_list)
        _apply_terms_list_binding(ruleset_id, check_id, terms_list)
    except Exception as e:
        # A failed save (a syntax error in the matcher, say) must not
        # lose what the author typed -- redisplay the edit form with
        # their own just-submitted values, not a re-fetch of the
        # still-old saved ones.
        fields = {"unit": form.get("unit", ""), "catches": form.get("catches", ""),
                  "instead": form.get("instead", ""), "threshold": form.get("threshold", 1),
                  "action": form.get("action", "warn"), "fn_body": form.get("fn_body", ""),
                  "terms_list": terms_list}
        return fragment_response(request, "fragments/check_edit_row.html", {
            "ruleset_id": ruleset_id, "check_id": check_id, "fields": fields,
            "custom_check_units": module.custom_check_units(),
            "bindable_lists": core_config.custom_term_lists(REPO_ROOT, ruleset_id),
        }, error=str(e))
    module, row = _single_row(ruleset_id, check_id)
    return fragment_response(request, "fragments/check_row.html",
                              {"row": row, "ruleset_id": ruleset_id})


@router.post("/checks/{ruleset_id}/{check_id}/remove")
async def remove_check(request: Request, ruleset_id: str, check_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    error = None
    if "custom_checks" not in module.CAPABILITIES:
        error = f"{ruleset_id!r} has no custom checks to remove"
    elif check_id not in module.custom_check_ids():
        error = f"{check_id!r} is a built-in check -- only a custom check can be removed"
    else:
        module.remove_custom_check(check_id)
        # Never leave a term list pointing at a check id that no longer
        # exists -- see core.config.clear_feeds_for_check.
        core_config.clear_feeds_for_check(REPO_ROOT, ruleset_id, check_id)
    module, section = _section_context(ruleset_id)
    return fragment_response(request, "fragments/checks_section.html", section, error=error)


@router.post("/checks/{ruleset_id}/custom/add")
async def add_custom_check(request: Request, ruleset_id: str):
    module = rulesets.get_ruleset(ruleset_id)
    form = await request.form()
    error = None
    if "custom_checks" not in module.CAPABILITIES:
        error = f"{ruleset_id!r} has no support for custom checks"
    else:
        check_id = form["check_id"]
        terms_list = form.get("terms_list") or None
        try:
            threshold = int(form.get("threshold") or 1)
            _check_terms_list_available(ruleset_id, check_id, terms_list)
            module.add_custom_check(
                check_id, form["unit"], form["catches"], form["instead"],
                threshold, form.get("action") or "warn", form["fn_body"], terms_list=terms_list)
            _apply_terms_list_binding(ruleset_id, check_id, terms_list)
        except Exception as e:
            # A custom check's body is arbitrary Python -- a SyntaxError from
            # the validate-then-write import is exactly as likely here as a
            # ValueError from a bad id/unit, and both need the same surface.
            error = str(e)
    module, section = _section_context(ruleset_id)
    return fragment_response(request, "fragments/checks_section.html", section, error=error)


@router.post("/checks/{ruleset_id}/playground")
async def playground(request: Request, ruleset_id: str, text: str = Form(...)):
    module = rulesets.get_ruleset(ruleset_id)
    stored = core_config.rule_packs(REPO_ROOT)
    glob = next((g for g, r, _p in stored if r == ruleset_id), None)
    full = os.path.join(REPO_ROOT, _synthetic_path_for_glob(glob)) if glob else None

    if not text.strip():
        return templates.TemplateResponse(request, "fragments/playground_result.html", {"empty": True})

    try:
        result = module.lint_and_gate(text, file_path=full)
        blocking = module.blocking_semantic_flags(result["semantic_flags"])
        non_blocking = [f for f in result["semantic_flags"] if f not in blocking]
        fixed = module.apply_mechanical_fixes(text, file_path=full) if result["mechanical_violations"] else None
    except Exception as e:
        # Arbitrary pasted text is the whole point of a playground -- more
        # likely than any other route here to hit an edge case a ruleset's
        # lint path didn't anticipate. Caught broadly since the failure
        # modes are the ruleset's own, not ours to enumerate.
        return templates.TemplateResponse(request, "fragments/playground_result.html",
                                           {"lint_error": str(e)})

    return templates.TemplateResponse(request, "fragments/playground_result.html", {
        "blocking": blocking, "mechanical": result["mechanical_violations"],
        "non_blocking": non_blocking, "fixed": fixed,
    })
