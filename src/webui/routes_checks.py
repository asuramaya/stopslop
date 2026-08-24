"""Checks page: per-ruleset check table, inline toggle/threshold/action,
the Try-it playground. Real content lands in Phase 3 -- this is the
skeleton's placeholder route."""
from fastapi import APIRouter, Request

from webui.deps import render

router = APIRouter()


@router.get("/checks")
def checks_page(request: Request):
    return render(request, "checks.html", "checks")
