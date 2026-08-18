"""Brave Search LLM Context API client.

Calls GET https://api.search.brave.com/res/v1/llm/context
with X-Subscription-Token from BRAVE_SEARCH_API_KEY (or BRAVE_API_KEY).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

BRAVE_LLM_CONTEXT_URL = "https://api.search.brave.com/res/v1/llm/context"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_QUERY_CHARS = 400
MAX_QUERY_WORDS = 50
DEFAULT_LOCAL_QUERY = "near me"


class BraveSearchError(Exception):
    """Upstream Brave Search request failed."""

    def __init__(self, message: str, status_code: int = 502, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class BraveNotConfiguredError(BraveSearchError):
    """API key is missing from the environment."""

    def __init__(self) -> None:
        super().__init__(
            "Brave Search is not configured. Set BRAVE_SEARCH_API_KEY.",
            status_code=503,
        )


def get_api_key(override: str | None = None) -> str | None:
    if override is not None:
        stripped = override.strip()
        if stripped:
            return stripped
    key = os.environ.get("BRAVE_SEARCH_API_KEY") or os.environ.get("BRAVE_API_KEY")
    if key is None:
        return None
    stripped = key.strip()
    return stripped or None


def validate_query(q: str) -> str:
    query = q.strip()
    if not query:
        raise ValueError("Query cannot be empty")
    if len(query) > MAX_QUERY_CHARS:
        raise ValueError(f"Query cannot exceed {MAX_QUERY_CHARS} characters")
    if len(query.split()) > MAX_QUERY_WORDS:
        raise ValueError(f"Query cannot exceed {MAX_QUERY_WORDS} words")
    return query


@dataclass(frozen=True)
class BraveLocation:
    """Optional client location forwarded as Brave X-Loc-* headers."""

    lat: float | None = None
    long: float | None = None
    city: str | None = None
    state: str | None = None
    state_name: str | None = None
    country: str | None = None
    postal_code: str | None = None

    def has_any(self) -> bool:
        return any(
            (
                self.lat is not None,
                self.long is not None,
                bool(self.city),
                bool(self.state),
                bool(self.state_name),
                bool(self.country),
                bool(self.postal_code),
            )
        )

    def validate(self) -> None:
        if (self.lat is None) ^ (self.long is None):
            raise ValueError("X-Loc-Lat and X-Loc-Long must be provided together")
        if self.lat is not None and not -90.0 <= self.lat <= 90.0:
            raise ValueError("X-Loc-Lat must be between -90 and 90")
        if self.long is not None and not -180.0 <= self.long <= 180.0:
            raise ValueError("X-Loc-Long must be between -180 and 180")

    def as_headers(self) -> dict[str, str]:
        """Build Brave location headers. Coordinates take precedence over place names."""
        self.validate()
        if self.lat is not None and self.long is not None:
            return {
                "X-Loc-Lat": _format_coord(self.lat),
                "X-Loc-Long": _format_coord(self.long),
            }
        headers: dict[str, str] = {}
        if self.city:
            headers["X-Loc-City"] = self.city
        if self.state:
            headers["X-Loc-State"] = self.state
        if self.state_name:
            headers["X-Loc-State-Name"] = self.state_name
        if self.country:
            headers["X-Loc-Country"] = self.country
        if self.postal_code:
            headers["X-Loc-Postal-Code"] = self.postal_code
        return headers

    def as_public_dict(self) -> dict[str, Any]:
        self.validate()
        data: dict[str, Any] = {}
        if self.lat is not None and self.long is not None:
            data["lat"] = self.lat
            data["long"] = self.long
            return data
        if self.city:
            data["city"] = self.city
        if self.state:
            data["state"] = self.state
        if self.state_name:
            data["state_name"] = self.state_name
        if self.country:
            data["country"] = self.country
        if self.postal_code:
            data["postal_code"] = self.postal_code
        return data


def _format_coord(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def _snippet_block(
    index: int,
    title: str | None,
    url: str | None,
    snippets: list[Any] | None,
    name: str | None = None,
) -> str:
    heading = title or name or "Untitled"
    if name and title and name != title:
        heading = f"{name} — {title}"
    body = "\n".join(str(snippet) for snippet in (snippets or []) if snippet)
    return f"[{index}] {heading}\n{url or ''}\n{body}".rstrip()


def format_grounding_for_llm(payload: dict[str, Any]) -> str:
    """Flatten Brave grounding snippets into a single prompt-ready string."""
    grounding = payload.get("grounding") or {}
    blocks: list[str] = []
    index = 1
    poi = grounding.get("poi")
    if isinstance(poi, dict) and (poi.get("url") or poi.get("snippets") or poi.get("name")):
        blocks.append(
            _snippet_block(index, poi.get("title"), poi.get("url"), poi.get("snippets"), poi.get("name"))
        )
        index += 1
    for place in grounding.get("map") or []:
        blocks.append(
            _snippet_block(
                index,
                place.get("title"),
                place.get("url"),
                place.get("snippets"),
                place.get("name"),
            )
        )
        index += 1
    for item in grounding.get("generic") or []:
        blocks.append(_snippet_block(index, item.get("title"), item.get("url"), item.get("snippets")))
        index += 1
    return "\n\n".join(blocks)


async def fetch_llm_context(
    q: str,
    *,
    count: int = 20,
    country: str | None = None,
    search_lang: str | None = None,
    maximum_number_of_tokens: int | None = None,
    enable_source_metadata: bool = True,
    enable_local: bool | None = None,
    location: BraveLocation | None = None,
    api_key: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Fetch pre-extracted web context from Brave LLM Context API."""
    token = get_api_key(api_key)
    if not token:
        raise BraveNotConfiguredError()

    query = validate_query(q)
    if count < 1 or count > 50:
        raise ValueError("count must be between 1 and 50")
    if location is not None:
        location.validate()

    params: dict[str, Any] = {
        "q": query,
        "count": count,
        "enable_source_metadata": str(enable_source_metadata).lower(),
    }
    if country:
        params["country"] = country
    if search_lang:
        params["search_lang"] = search_lang
    if maximum_number_of_tokens is not None:
        if maximum_number_of_tokens < 1024 or maximum_number_of_tokens > 32768:
            raise ValueError("maximum_number_of_tokens must be between 1024 and 32768")
        params["maximum_number_of_tokens"] = maximum_number_of_tokens
    if enable_local is not None:
        params["enable_local"] = str(enable_local).lower()

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": token,
    }
    if location is not None and location.has_any():
        headers.update(location.as_headers())

    own_client = client is None
    http = client or httpx.AsyncClient(timeout=timeout)
    try:
        response = await http.get(BRAVE_LLM_CONTEXT_URL, params=params, headers=headers)
    except httpx.TimeoutException as exc:
        raise BraveSearchError("Brave Search request timed out", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise BraveSearchError(f"Brave Search request failed: {exc}", status_code=502) from exc
    finally:
        if own_client:
            await http.aclose()

    if response.status_code == 401:
        raise BraveSearchError(
            "Brave Search rejected the API key. Check BRAVE_SEARCH_API_KEY.",
            status_code=502,
            details=response.text,
        )
    if response.status_code == 429:
        raise BraveSearchError(
            "Brave Search rate limit exceeded. Try again shortly.",
            status_code=429,
            details=response.text,
        )
    if response.status_code >= 400:
        raise BraveSearchError(
            f"Brave Search returned HTTP {response.status_code}",
            status_code=502,
            details=response.text,
        )

    try:
        return response.json()
    except ValueError as exc:
        raise BraveSearchError("Brave Search returned invalid JSON", status_code=502) from exc
