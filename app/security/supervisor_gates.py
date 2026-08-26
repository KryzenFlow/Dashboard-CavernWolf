"""Deterministic supervisor gates — Steps A–C before any model or child execution."""

from __future__ import annotations

import json
from typing import Any

from app.security.control_plane import current_root, token_merkle_root_matches, verify_live_root
from app.security.doberman_hook import pre_exec
from app.security.path_confinement import check_payload
from app.security.hierarchy import (
    child_must_ask_parent,
    is_child_token,
    parent_may_contact_supervisor,
)
from app.security.token import capability_allowed, validate_token


def _parse_token(token: str | dict[str, Any] | None) -> dict[str, Any] | None:
    if token is None:
        return None
    if isinstance(token, dict):
        return token
    try:
        parsed = json.loads(token)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def validate_and_gate(
    payload: dict[str, Any],
    token: str | dict[str, Any] | None,
    *,
    action: str | None = None,
    agent_name: str = "",
    session_id: str = "global",
) -> tuple[str, str]:
    """
    Full fast path deterministic gate.
    Returns (\"PASS\" | \"BLOCK\", reason_string). Fail-closed on any exception.
    """
    try:
        # Step A — lifecycle token + capability
        ok, reason = validate_token(token)
        if not ok:
            return "BLOCK", f"Token revoked or signature invalid: {reason}"

        token_parsed = _parse_token(token)
        if not token_parsed:
            return "BLOCK", "Token type invalid for capability check"

        # Children never contact supervisor — they ask parent from inside their container.
        if is_child_token(token_parsed):
            return "BLOCK", "children cannot contact supervisor; ask parent from container"

        if not parent_may_contact_supervisor(token_parsed):
            return "BLOCK", "only host-tier parent may reach supervisor gates"

        if not verify_live_root():
            return "BLOCK", "Merkle tamper detected on control plane"

        if not token_merkle_root_matches(token_parsed):
            return "BLOCK", "Token merkle root mismatch (stale or forged)"

        requested_action = action or payload.get("action")
        if requested_action and not capability_allowed(token_parsed, str(requested_action)):
            return "BLOCK", f"Action '{requested_action}' outside granted capabilities"

        # Step B — path confinement
        path_verdict, path_reason = check_payload(payload)
        if path_verdict != "PASS":
            return "BLOCK", f"Path confinement violation: {path_reason}"

        # Step C — Doberman hook (deterministic)
        doberman_verdict = pre_exec(
            payload,
            agent_name=agent_name or str(token_parsed.get("agent_id", "unknown")),
            session_id=session_id or str(token_parsed.get("tree_id", "global")),
            lifecycle_token=token_parsed,
        )
        if doberman_verdict != "PASS":
            return "BLOCK", f"Doberman inspection rejected payload (Verdict: {doberman_verdict})"

        _ = current_root()
        return "PASS", "All deterministic gates cleared"
    except Exception as exc:
        return "BLOCK", f"System gate exception: {exc}"
