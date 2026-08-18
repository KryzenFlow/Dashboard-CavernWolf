"""REST routes for Brave Search LLM Context."""

from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from brave.client import (
    BRAVE_LLM_CONTEXT_URL,
    BraveSearchError,
    fetch_llm_context,
    format_grounding_for_llm,
    get_api_key,
)

router = APIRouter(prefix="/search", tags=["search"])


class LlmContextRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=400)
    count: int = Field(20, ge=1, le=50)
    country: str | None = Field(None, min_length=2, max_length=3)
    search_lang: str | None = None
    maximum_number_of_tokens: int | None = Field(None, ge=1024, le=32768)
    enable_source_metadata: bool = True


def _raise_brave(exc: BraveSearchError) -> NoReturn:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"error": exc.message, "details": exc.details},
    ) from exc


def _wrap_payload(query: str, payload: dict[str, Any]) -> dict[str, Any]:
    generic = (payload.get("grounding") or {}).get("generic") or []
    return {
        "query": query,
        "provider": "brave",
        "endpoint": BRAVE_LLM_CONTEXT_URL,
        "result_count": len(generic),
        "context": format_grounding_for_llm(payload),
        "grounding": payload.get("grounding") or {"generic": [], "map": []},
        "sources": payload.get("sources") or {},
    }


@router.get("/status")
async def search_status() -> dict[str, Any]:
    return {
        "configured": get_api_key() is not None,
        "provider": "brave",
        "endpoint": BRAVE_LLM_CONTEXT_URL,
    }


@router.get("/llm-context")
async def get_llm_context(
    q: str = Query(..., min_length=1, max_length=400, description="Search query"),
    count: int = Query(20, ge=1, le=50),
    country: str | None = Query(None, min_length=2, max_length=3),
    search_lang: str | None = Query(None),
    maximum_number_of_tokens: int | None = Query(None, ge=1024, le=32768),
    enable_source_metadata: bool = Query(True),
) -> dict[str, Any]:
    """Proxy GET https://api.search.brave.com/res/v1/llm/context."""
    try:
        payload = await fetch_llm_context(
            q,
            count=count,
            country=country,
            search_lang=search_lang,
            maximum_number_of_tokens=maximum_number_of_tokens,
            enable_source_metadata=enable_source_metadata,
        )
    except BraveSearchError as exc:
        _raise_brave(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _wrap_payload(q.strip(), payload)


@router.post("/llm-context")
async def post_llm_context(body: LlmContextRequest) -> dict[str, Any]:
    """Same as GET, with a JSON body for longer or structured queries."""
    try:
        payload = await fetch_llm_context(
            body.q,
            count=body.count,
            country=body.country,
            search_lang=body.search_lang,
            maximum_number_of_tokens=body.maximum_number_of_tokens,
            enable_source_metadata=body.enable_source_metadata,
        )
    except BraveSearchError as exc:
        _raise_brave(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _wrap_payload(body.q.strip(), payload)
