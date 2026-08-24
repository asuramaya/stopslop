"""Watch page: what the gate just did, and why -- filterable by path and
by ruleset, same question dashboard.py's own watch_page()/_watch_activity()
answered. The fragment endpoint is what the page's own htmx polling hits
every 2s; the full page just renders the same fragment once, inline.
"""
import os
import time

from fastapi import APIRouter, Request

import rulesets
from core import history

from webui.deps import REPO_ROOT, render, templates

router = APIRouter()

HISTORY_PATH = history.history_log_path(REPO_ROOT)

# One glyph per gate action -- identical to dashboard.py's own ACTION_ICON.
ACTION_ICON = {"deny": "\U0001F6AB", "auto_fix": "\U0001F527", "clean": "✅",
               "unscoped_write": "❔", "register_term": "➕",
               "unregister_term": "➖", "config_write": "⚙️"}


def _fmt_ts(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "?"


def _relative_time(ts):
    if not ts:
        return "?"
    delta = time.time() - ts
    if delta < 60:
        return f"{int(delta)}s ago"
    if delta < 3600:
        return f"{int(delta // 60)}m ago"
    if delta < 86400:
        return f"{int(delta // 3600)}h ago"
    return f"{int(delta // 86400)}d ago"


def _short_path(file_path):
    if not file_path:
        return ""
    try:
        return os.path.relpath(file_path, REPO_ROOT)
    except ValueError:
        return file_path


@router.get("/watch")
def watch_page(request: Request):
    ids = ["All"] + [m.RULESET_ID for m in rulesets.list_rulesets()]
    return render(request, "watch.html", "watch", {"ruleset_ids": ids})


@router.get("/watch/fragment")
def watch_fragment(request: Request, path: str = "", ruleset: str = "All"):
    events = list(reversed(history.read_history_deduped(HISTORY_PATH)))
    if ruleset and ruleset != "All":
        events = [e for e in events if e.get("ruleset") == ruleset]
    needle = path.strip().lower()
    if needle:
        events = [e for e in events if needle in (e.get("file") or "").lower()]

    denials = [e for e in events if e.get("action") == "deny"][:5]
    rows = [{
        "time": _fmt_ts(e.get("ts")),
        "icon": ACTION_ICON.get(e.get("action"), ""),
        "action": e.get("action", ""),
        "ruleset": e.get("ruleset", ""),
        "file": _short_path(e.get("file")),
        "kinds": ", ".join(e.get("kinds") or []),
    } for e in events[:50]]
    denial_rows = [{
        "file": _short_path(e.get("file")) or "(no file)",
        "ruleset": e.get("ruleset", ""),
        "when": _relative_time(e.get("ts")),
        "kinds": ", ".join(e.get("kinds") or []) or "(no kind recorded)",
    } for e in denials]

    return templates.TemplateResponse(
        request, "fragments/watch_activity.html",
        {"denials": denial_rows, "rows": rows})
