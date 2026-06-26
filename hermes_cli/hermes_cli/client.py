"""HTTP clients for Agent Claw and Hermes backend."""

from __future__ import annotations

import os
from typing import Any

import requests

CLAW_URL = os.getenv("CLAW_URL", "http://agent-claw:9000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
WORKSPACE = os.getenv("DEV_TOOLS_WORKSPACE", "/shared/workflows")


def claw_execute(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = requests.post(
        f"{CLAW_URL}/execute",
        json={"action": action, "params": params or {}},
        timeout=300,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"error": resp.text, "status_code": resp.status_code}
    if resp.status_code >= 400 and "error" not in data:
        data["error"] = resp.text
    return data


def backend_reason(query: str) -> dict[str, Any]:
    resp = requests.post(
        f"{BACKEND_URL}/reason",
        json={"query": query},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def backend_action(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = requests.post(
        f"{BACKEND_URL}/action",
        json={"action": action, "params": params or {}},
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()
