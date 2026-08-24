"""Watch page: the live activity feed and denials callout. Real content
lands in Phase 2 -- this is the skeleton's placeholder route."""
from fastapi import APIRouter, Request

from webui.deps import render

router = APIRouter()


@router.get("/watch")
def watch_page(request: Request):
    return render(request, "watch.html", "watch")
