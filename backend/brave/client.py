"""Brave Search LLM Context API client.

Calls GET https://api.search.brave.com/res/v1/llm/context
with X-Subscription-Token from BRAVE_SEARCH_API_KEY (or BRAVE_API_KEY).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

BRAVE_LLM_CONTEXT_URL = "https://api.search.brave.com/res/v1/llm/context"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_QUERY_CHARS = 400
MAX_QUERY_WORDS = 50


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


def get_api_key() -> str | None:
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


def format_grounding_for_llm(payload: dict[str, Any]) -> str:
    """Flatten Brave grounding snippets into a single prompt-ready string."""
    grounding = payload.get("grounding") or {}
    generic = grounding.get("generic") or []
    blocks: list[str] = []
    for index, item in enumerate(generic, start=1):
        title = item.get("title") or "Untitled"
        url = item.get("url") or ""
        snippets = item.get("snippets") or []
        body = "\n".join(str(snippet) for snippet in snippets if snippet)
        blocks.append(f"[{index}] {title}\n{url}\n{body}".rstrip())
    return "\n\n".join(blocks)


async def fetch_llm_context(
    q: str,
    *,
    count: int = 20,
    country: str | None = None,
    search_lang: str | None = None,
    maximum_number_of_tokens: int | None = None,
    enable_source_metadata: bool = True,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Fetch pre-extracted web context from Brave LLM Context API."""
    api_key = get_api_key()
    if not api_key:
        raise BraveNotConfiguredError()

    query = validate_query(q)
    if count < 1 or count > 50:
        raise ValueError("count must be between 1 and 50")

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

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }

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
