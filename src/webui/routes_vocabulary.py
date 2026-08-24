"""Vocabulary page: cross-list search, per-list browser. Real content
lands in Phase 4 -- this is the skeleton's placeholder route."""
from fastapi import APIRouter, Request

from webui.deps import render

router = APIRouter()


@router.get("/vocabulary")
def vocabulary_page(request: Request):
    return render(request, "vocabulary.html", "vocabulary")
