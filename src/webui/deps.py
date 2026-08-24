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
