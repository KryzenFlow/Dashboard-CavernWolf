"""REST routes for Brave Search LLM Context."""

from __future__ import annotations

from typing import Any, NoReturn

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from brave.client import (
    BRAVE_LLM_CONTEXT_URL,
    DEFAULT_LOCAL_QUERY,
    BraveLocation,
    BraveSearchError,
    fetch_llm_context,
    format_grounding_for_llm,
    get_api_key,
)

router = APIRouter(prefix="/search", tags=["search"])
brave_compat_router = APIRouter(tags=["search"])


class LlmContextRequest(BaseModel):
    q: str | None = Field(None, min_length=1, max_length=400)
    count: int = Field(20, ge=1, le=50)
    country: str | None = Field(None, min_length=2, max_length=3)
    search_lang: str | None = None
    maximum_number_of_tokens: int | None = Field(None, ge=1024, le=32768)
    enable_source_metadata: bool = True
    enable_local: bool | None = None
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    city: str | None = None
    state: str | None = None
    state_name: str | None = None
    loc_country: str | None = None
    postal_code: str | None = None


def _raise_brave(exc: BraveSearchError) -> NoReturn:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"error": exc.message, "details": exc.details},
    ) from exc


def _resolve_location(
    *,
    lat: float | None,
    lon: float | None,
    city: str | None = None,
    state: str | None = None,
    state_name: str | None = None,
    loc_country: str | None = None,
    postal_code: str | None = None,
    header_lat: float | None = None,
    header_lon: float | None = None,
    header_city: str | None = None,
    header_state: str | None = None,
    header_state_name: str | None = None,
    header_country: str | None = None,
    header_postal_code: str | None = None,
) -> BraveLocation | None:
    location = BraveLocation(
        lat=lat if lat is not None else header_lat,
        long=lon if lon is not None else header_lon,
        city=city or header_city,
        state=state or header_state,
        state_name=state_name or header_state_name,
        country=loc_country or header_country,
        postal_code=postal_code or header_postal_code,
    )
    try:
        location.validate()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return location if location.has_any() else None


def _resolve_query(q: str | None, location: BraveLocation | None) -> str:
    if q is not None and q.strip():
        return q.strip()
    if location is not None and location.lat is not None and location.long is not None:
        return DEFAULT_LOCAL_QUERY
    raise HTTPException(
        status_code=422,
        detail="Query q is required unless X-Loc-Lat and X-Loc-Long are set.",
    )


async def _execute_llm_context(
    *,
    q: str | None,
    count: int,
    country: str | None,
    search_lang: str | None,
    maximum_number_of_tokens: int | None,
    enable_source_metadata: bool,
    enable_local: bool | None,
    location: BraveLocation | None,
    subscription_token: str | None,
) -> dict[str, Any]:
    query = _resolve_query(q, location)
    try:
        payload = await fetch_llm_context(
            query,
            count=count,
            country=country,
            search_lang=search_lang,
            maximum_number_of_tokens=maximum_number_of_tokens,
            enable_source_metadata=enable_source_metadata,
            enable_local=enable_local,
            location=location,
            api_key=subscription_token,
        )
    except BraveSearchError as exc:
        _raise_brave(exc)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _wrap_payload(query, payload, location)


def _result_count(payload: dict[str, Any]) -> int:
    grounding = payload.get("grounding") or {}
    generic = grounding.get("generic") or []
    maps = grounding.get("map") or []
    poi = grounding.get("poi")
    extra = 1 if isinstance(poi, dict) and (poi.get("url") or poi.get("snippets") or poi.get("name")) else 0
    return len(generic) + len(maps) + extra


def _wrap_payload(
    query: str,
    payload: dict[str, Any],
    location: BraveLocation | None = None,
) -> dict[str, Any]:
    return {
        "query": query,
        "provider": "brave",
        "endpoint": BRAVE_LLM_CONTEXT_URL,
        "result_count": _result_count(payload),
        "location": location.as_public_dict() if location else None,
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
@brave_compat_router.get("/res/v1/llm/context")
async def get_llm_context(
    q: str | None = Query(None, min_length=1, max_length=400, description="Search query"),
    count: int = Query(20, ge=1, le=50),
    country: str | None = Query(None, min_length=2, max_length=3),
    search_lang: str | None = Query(None),
    maximum_number_of_tokens: int | None = Query(None, ge=1024, le=32768),
    enable_source_metadata: bool = Query(True),
    enable_local: bool | None = Query(None),
    lat: float | None = Query(None, ge=-90, le=90),
    lon: float | None = Query(None, ge=-180, le=180),
    x_loc_lat: float | None = Header(default=None),
    x_loc_long: float | None = Header(default=None),
    x_loc_city: str | None = Header(default=None),
    x_loc_state: str | None = Header(default=None),
    x_loc_state_name: str | None = Header(default=None),
    x_loc_country: str | None = Header(default=None),
    x_loc_postal_code: str | None = Header(default=None),
    x_subscription_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Proxy GET https://api.search.brave.com/res/v1/llm/context.

    ``q`` may be omitted when ``X-Loc-Lat`` and ``X-Loc-Long`` are set; the
    gateway then searches for ``near me``.
    """
    location = _resolve_location(
        lat=lat,
        lon=lon,
        header_lat=x_loc_lat,
        header_lon=x_loc_long,
        header_city=x_loc_city,
        header_state=x_loc_state,
        header_state_name=x_loc_state_name,
        header_country=x_loc_country,
        header_postal_code=x_loc_postal_code,
    )
    return await _execute_llm_context(
        q=q,
        count=count,
        country=country,
        search_lang=search_lang,
        maximum_number_of_tokens=maximum_number_of_tokens,
        enable_source_metadata=enable_source_metadata,
        enable_local=enable_local,
        location=location,
        subscription_token=x_subscription_token,
    )


@router.post("/llm-context")
@brave_compat_router.post("/res/v1/llm/context")
async def post_llm_context(
    body: LlmContextRequest,
    x_loc_lat: float | None = Header(default=None),
    x_loc_long: float | None = Header(default=None),
    x_loc_city: str | None = Header(default=None),
    x_loc_state: str | None = Header(default=None),
    x_loc_state_name: str | None = Header(default=None),
    x_loc_country: str | None = Header(default=None),
    x_loc_postal_code: str | None = Header(default=None),
    x_subscription_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Same as GET, with a JSON body for longer or structured queries."""
    location = _resolve_location(
        lat=body.lat,
        lon=body.lon,
        city=body.city,
        state=body.state,
        state_name=body.state_name,
        loc_country=body.loc_country,
        postal_code=body.postal_code,
        header_lat=x_loc_lat,
        header_lon=x_loc_long,
        header_city=x_loc_city,
        header_state=x_loc_state,
        header_state_name=x_loc_state_name,
        header_country=x_loc_country,
        header_postal_code=x_loc_postal_code,
    )
    return await _execute_llm_context(
        q=body.q,
        count=body.count,
        country=body.country,
        search_lang=body.search_lang,
        maximum_number_of_tokens=body.maximum_number_of_tokens,
        enable_source_metadata=body.enable_source_metadata,
        enable_local=body.enable_local,
        location=location,
        subscription_token=x_subscription_token,
    )
