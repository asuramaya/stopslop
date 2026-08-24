"""Shared pieces every webui route module needs: the templates instance,
the repo root, the nav table, and one render() helper that stamps the
nav + status footer context onto every full-page response so a route
module only supplies what's genuinely its own.

Split out from app.py to avoid a circular import -- app.py imports each
routes_*.py module to register its router, and every routes_*.py module
needs `templates`/`render`, so neither can import the other directly.
"""
import os
import sys

# Same "make src/ importable regardless of how this process was launched"
# pattern dashboard.py/mcp_server.py/stopslop.py already use -- necessary
# here too since uvicorn imports this package by dotted path, not by
# running a script whose own directory Python auto-adds to sys.path.
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from fastapi.templating import Jinja2Templates

from core import paths
import status_report

REPO_ROOT = paths.find_project_root(__file__)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(PACKAGE_DIR, "templates"))

# (route prefix, label, icon) -- the same four pages, same order and
# icons, dashboard.py's own nav used.
NAV = [
    ("watch", "Watch", "\U0001F441"),
    ("checks", "Checks", "\U0001F6A6"),
    ("vocabulary", "Vocabulary", "\U0001F4D6"),
    ("routing", "Routing", "\U0001F5FA"),
]


def status():
    """Fresh every call, same never-cache-it posture every other config
    read in this project takes -- see core/config.py's own module
    docstring for why."""
    return status_report.build_status_report(REPO_ROOT)


def render(request, template_name, active, extra=None):
    """Every full-page GET route renders through this. `active` is the
    NAV id to highlight."""
    context = {"nav": NAV, "active": active, "status": status()}
    context.update(extra or {})
    return templates.TemplateResponse(request, template_name, context)


def error_banner(message=None):
    """Render the out-of-band #error-banner fragment -- `message=None`
    renders it empty, which is how a route clears a previous error on its
    next successful save. Rendered through Jinja (not an f-string) so a
    ValueError message built from user input -- a term, a glob -- gets
    the same auto-escaping every other user-supplied string on these
    pages gets; see fragment_response()'s docstring for why this exists."""
    return templates.get_template("fragments/error_banner.html").render(message=message)


def fragment_response(request, template_name, context, error=None):
    """What a mutating route returns instead of a plain TemplateResponse:
    the same fragment a clean save would return, PLUS an out-of-band
    #error-banner swap -- populated when `error` is set (the write was
    refused, e.g. a bad threshold or an unknown ruleset id), emptied
    otherwise (clears whatever error the previous attempt on this same
    control left showing). This is what stands between a raised
    ValueError and FastAPI's default 500 -- without it, htmx swaps that
    500 page's raw HTML straight into the row/table it was targeting."""
    from fastapi.responses import HTMLResponse
    body = templates.get_template(template_name).render(context, request=request)
    return HTMLResponse(body + error_banner(error))
