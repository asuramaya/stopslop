"""Routing page: the editable first-match-wins rules table. Real content
lands in Phase 5 -- this is the skeleton's placeholder route."""
from fastapi import APIRouter, Request

from webui.deps import render

router = APIRouter()


@router.get("/routing")
def routing_page(request: Request):
    return render(request, "routing.html", "routing")
