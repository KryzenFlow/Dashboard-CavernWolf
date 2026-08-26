"""Deterministic pre-exec gate — no model, fail-closed."""

from __future__ import annotations

import re
from typing import Any

_PRIVATE_KEY_MARKERS = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?KEY-----")
_SUSPICIOUS_ENV_LEAK_RE = re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b")
_HIGH_ENTROPY_RE = re.compile(r"[A-Za-z0-9+/=]{80,}")


def _iter_strings(payload: Any) -> list[str]:
    if payload is None:
        return []
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for value in payload.values():
            out.extend(_iter_strings(value))
        return out
    if isinstance(payload, list):
        out: list[str] = []
        for value in payload:
            out.extend(_iter_strings(value))
        return out
    return []


def pre_exec(
    payload: dict[str, Any],
    *,
    agent_name: str = "",
    session_id: str = "global",
    lifecycle_token: dict[str, Any] | str | None = None,
) -> str:
    """
    Returns \"PASS\" | \"BLOCK\" | \"AUTH\".
    Fail-closed: any error → \"BLOCK\".
    Optional AI anomaly check is intentionally omitted — deterministic only.
    """
    try:
        _ = (agent_name, session_id, lifecycle_token)

        strings = _iter_strings(payload)
        for s in strings:
            if len(s) > 200_000:
                return "BLOCK"
            if _PRIVATE_KEY_MARKERS.search(s):
                return "BLOCK"
            if _HIGH_ENTROPY_RE.search(s) and "hash" not in s.lower():
                return "BLOCK"

        for s in strings:
            if _SUSPICIOUS_ENV_LEAK_RE.search(s) and "leak" in s.lower():
                return "BLOCK"

        return "PASS"
    except Exception:
        return "BLOCK"
