from __future__ import annotations

import re
from typing import Any


_PRIVATE_KEY_MARKERS = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?KEY-----")
_SUSPICIOUS_ENV_LEAK_RE = re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b")


def _iter_strings(payload: Any) -> list[str]:
    if payload is None:
        return []
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for v in payload.values():
            out.extend(_iter_strings(v))
        return out
    if isinstance(payload, list):
        out = []
        for v in payload:
            out.extend(_iter_strings(v))
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
    Deterministic Doberman-like hook.

    In this v1 implementation we avoid calling a model. The function is strict
    about secrets/leaks and obviously dangerous input shapes, but otherwise
    keeps allow-list behavior so the dashboard remains usable.

    Returns: "PASS" | "BLOCK" | "AUTH"
    """
    try:
        _ = (agent_name, session_id, lifecycle_token)  # used for future policy expansion

        strings = _iter_strings(payload)
        for s in strings:
            if len(s) > 200_000:
                return "BLOCK"
            if _PRIVATE_KEY_MARKERS.search(s):
                return "BLOCK"

        # Light heuristic: if the request explicitly asks to exfiltrate secrets,
        # block. (The gateway does not execute anyway, but this keeps policy coherent.)
        for s in strings:
            if _SUSPICIOUS_ENV_LEAK_RE.search(s) and "leak" in s.lower():
                return "BLOCK"

        return "PASS"
    except Exception:
        # Fail-closed.
        return "BLOCK"

