#!/usr/bin/env python3
"""FastAPI app for stopslop's local dashboard -- see webui/__init__.py's
docstring for why this replaces the old Streamlit one.

Not a second gate, not a second config store -- the same distinction the
MCP server's and the old dashboard's own docstrings already draw for
themselves. This reads and writes the exact files the hook, the CLI, and
an agent editing stopslop.config.json directly all already use, through
the SAME functions every other entry point calls.

Run directly for local development (see also webui/DEV.md-equivalent
note in the phase-1 verification): from the repo's `src/` directory,
    ../.venv/bin/python3 -m uvicorn webui.app:app --port 8502 --reload
Or through the project's own launcher once cut over:
    stopslop.py dashboard
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from webui import routes_checks, routes_routing, routes_vocabulary, routes_watch
from webui.deps import PACKAGE_DIR, status, templates

app = FastAPI(title="stopslop")
app.mount("/static", StaticFiles(directory=f"{PACKAGE_DIR}/static"), name="static")

app.include_router(routes_watch.router)
app.include_router(routes_checks.router)
app.include_router(routes_vocabulary.router)
app.include_router(routes_routing.router)


@app.get("/health")
def health():
    """Plays the same role streamlit's own /_stcore/health does for
    dashboard_launch.py's liveness probe -- see that module."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index():
    return RedirectResponse(url="/watch")


@app.get("/status/fragment", response_class=HTMLResponse)
def status_fragment(request: Request):
    """What the footer's own hx-trigger="every 10s" polls -- the same
    partial base.html includes inline on first render, so the two never
    drift apart into two copies of this text."""
    return templates.TemplateResponse(
        request, "fragments/status_footer.html", {"status": status()})
