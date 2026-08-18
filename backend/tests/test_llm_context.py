"""Tests for Brave Search LLM Context client and REST proxy."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from brave.client import (
    BRAVE_LLM_CONTEXT_URL,
    BraveLocation,
    BraveNotConfiguredError,
    BraveSearchError,
    fetch_llm_context,
    format_grounding_for_llm,
    validate_query,
)
from web_gateway.app import create_app

EVEREST_PAYLOAD = {
    "grounding": {
        "generic": [
            {
                "url": "https://en.wikipedia.org/wiki/List_of_highest_mountains_on_Earth",
                "title": "List of highest mountains on Earth",
                "snippets": [
                    "Mount Everest is Earth's highest mountain above sea level at 8,848.86 m.",
                    "K2 is the second-highest mountain on Earth, after Mount Everest.",
                ],
            }
        ],
        "map": [],
    },
    "sources": {
        "https://en.wikipedia.org/wiki/List_of_highest_mountains_on_Earth": {
            "title": "List of highest mountains on Earth",
            "hostname": "en.wikipedia.org",
            "age": [],
        }
    },
}


def _mock_response(status_code: int = 200, payload: dict[str, Any] | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload if payload is not None else {}
    response.text = text
    return response


def test_validate_query_rejects_empty() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_query("   ")


def test_validate_query_rejects_too_many_words() -> None:
    with pytest.raises(ValueError, match="50 words"):
        validate_query(" ".join(f"word{i}" for i in range(51)))


def test_format_grounding_for_llm() -> None:
    text = format_grounding_for_llm(EVEREST_PAYLOAD)
    assert "Mount Everest" in text
    assert "https://en.wikipedia.org" in text
    assert text.startswith("[1] List of highest mountains on Earth")


@pytest.mark.asyncio
async def test_fetch_llm_context_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    with pytest.raises(BraveNotConfiguredError):
        await fetch_llm_context("tallest mountains in the world")


@pytest.mark.asyncio
async def test_fetch_llm_context_sends_subscription_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-token")
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(200, EVEREST_PAYLOAD)

    result = await fetch_llm_context("tallest mountains in the world", client=mock_client)

    assert result["grounding"]["generic"][0]["title"].startswith("List of highest")
    mock_client.get.assert_awaited_once()
    args, kwargs = mock_client.get.await_args
    assert args[0] == BRAVE_LLM_CONTEXT_URL
    assert kwargs["params"]["q"] == "tallest mountains in the world"
    assert kwargs["headers"]["X-Subscription-Token"] == "test-token"
    assert kwargs["headers"]["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_fetch_llm_context_maps_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "bad-token")
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(401, text="unauthorized")
    with pytest.raises(BraveSearchError) as exc_info:
        await fetch_llm_context("tallest mountains in the world", client=mock_client)
    assert exc_info.value.status_code == 502


def test_search_status_reports_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    client = TestClient(create_app())
    response = client.get("/search/status")
    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["endpoint"] == BRAVE_LLM_CONTEXT_URL


def test_get_llm_context_without_key_returns_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    client = TestClient(create_app())
    response = client.get("/search/llm-context", params={"q": "tallest mountains in the world"})
    assert response.status_code == 503
    assert "BRAVE_SEARCH_API_KEY" in response.json()["detail"]["error"]


def test_get_llm_context_proxies_brave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-token")
    client = TestClient(create_app())
    with patch("routes.search.fetch_llm_context", new=AsyncMock(return_value=EVEREST_PAYLOAD)):
        response = client.get("/search/llm-context", params={"q": "tallest mountains in the world"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "tallest mountains in the world"
    assert body["provider"] == "brave"
    assert body["result_count"] == 1
    assert "Mount Everest" in body["context"]
    assert body["grounding"]["generic"][0]["url"].startswith("https://en.wikipedia.org")


def test_post_llm_context_proxies_brave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-token")
    client = TestClient(create_app())
    with patch("routes.search.fetch_llm_context", new=AsyncMock(return_value=EVEREST_PAYLOAD)):
        response = client.post("/search/llm-context", json={"q": "tallest mountains in the world", "count": 5})
    assert response.status_code == 200
    assert response.json()["result_count"] == 1
    assert response.json()["location"] is None


@pytest.mark.asyncio
async def test_fetch_llm_context_sends_location_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-token")
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(200, EVEREST_PAYLOAD)
    location = BraveLocation(lat=37.7749, long=-122.4194)

    await fetch_llm_context("best coffee shops near me", location=location, client=mock_client)

    _args, kwargs = mock_client.get.await_args
    assert kwargs["headers"]["X-Subscription-Token"] == "test-token"
    assert kwargs["headers"]["X-Loc-Lat"] == "37.7749"
    assert kwargs["headers"]["X-Loc-Long"] == "-122.4194"
    assert "X-Loc-City" not in kwargs["headers"]


def test_brave_location_requires_both_coordinates() -> None:
    with pytest.raises(ValueError, match="together"):
        BraveLocation(lat=37.7749).validate()


def test_get_llm_context_forwards_loc_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-token")
    client = TestClient(create_app())
    mock = AsyncMock(return_value=EVEREST_PAYLOAD)
    with patch("routes.search.fetch_llm_context", new=mock):
        response = client.get(
            "/search/llm-context",
            params={"q": "best coffee shops near me"},
            headers={"X-Loc-Lat": "37.7749", "X-Loc-Long": "-122.4194"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["location"]["lat"] == 37.7749
    assert body["location"]["long"] == -122.4194
    kwargs = mock.await_args.kwargs
    assert kwargs["location"] == BraveLocation(lat=37.7749, long=-122.4194)


def test_post_llm_context_accepts_lat_lon(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-token")
    client = TestClient(create_app())
    mock = AsyncMock(return_value=EVEREST_PAYLOAD)
    with patch("routes.search.fetch_llm_context", new=mock):
        response = client.post(
            "/search/llm-context",
            json={"q": "best coffee shops near me", "lat": 37.7749, "lon": -122.4194, "enable_local": True},
        )
    assert response.status_code == 200
    kwargs = mock.await_args.kwargs
    assert kwargs["enable_local"] is True
    assert kwargs["location"] == BraveLocation(lat=37.7749, long=-122.4194)
