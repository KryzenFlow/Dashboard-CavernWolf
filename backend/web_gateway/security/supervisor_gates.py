from __future__ import annotations

import json
from typing import Any

from .control_plane import current_leaves, current_root, fail_control, record_decision, token_in_tree
from .doberman_hook_ai import pre_exec
from .merkle import compute_merkle_root, roots_match
from .path_confinement import check_payload
from .token import capability_allowed, extract_tree_id, validate_token


def _parse_token(token: str | dict[str, Any] | None) -> dict[str, Any] | None:
    if token is None:
        return None
    if isinstance(token, dict):
        return token
    try:
        parsed = json.loads(token)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def validate_and_gate(
    *,
    payload: dict[str, Any],
    token: str | dict[str, Any] | None,
    action: str,
    agent_name: str = "",
    session_id: str = "global",
) -> tuple[str, str]:
    """Deterministic gates only. No model. Fail-closed. No false environment."""
    try:
        ok, reason = validate_token(token)
        if not ok:
            return "BLOCK", f"token validation failed: {reason}"

        token_parsed = _parse_token(token)
        if not token_parsed:
            return "BLOCK", "token type invalid for capability check"

        live = current_root()
        if not live:
            fail_control("merkle root missing")
            return "BLOCK", "merkle root missing"

        recomputed = compute_merkle_root(current_leaves())
        if not roots_match(recomputed, live):
            fail_control("merkle tamper detected")
            return "BLOCK", "merkle tamper detected"

        if not token_in_tree(token_parsed):
            return "BLOCK", "token not present in merkle tree"

        if token_parsed.get("role") == "claw-daemon":
            presented = str(payload.get("merkle_root") or token_parsed.get("merkle_root") or "")
            if not roots_match(presented, live):
                fail_control("claw daemon merkle root mismatch")
                return "BLOCK", "claw daemon merkle root mismatch"

        if not capability_allowed(token_parsed, action):
            return "BLOCK", f"capability denied: {action}"

        path_verdict, path_reason = check_payload(payload)
        if path_verdict != "PASS":
            return "BLOCK", f"path confinement violation: {path_reason}"

        doberman_verdict = pre_exec(
            payload,
            agent_name=agent_name,
            session_id=session_id,
            lifecycle_token=token_parsed,
        )
        if doberman_verdict != "PASS":
            return "BLOCK", f"doberman_hook rejected payload (verdict={doberman_verdict})"

        return "PASS", "ok"
    except Exception as e:  # pragma: no cover
        return "BLOCK", f"gate exception: {e}"


def gate_and_ledger_block_if_needed(
    *,
    payload: dict[str, Any],
    token: str | dict[str, Any] | None,
    action: str,
    agent_name: str = "",
    session_id: str = "global",
) -> tuple[str, str]:
    verdict, reason = validate_and_gate(
        payload=payload,
        token=token,
        action=action,
        agent_name=agent_name,
        session_id=session_id,
    )
    record_decision(
        {
            "tree_id": extract_tree_id(token),
            "agent_name": agent_name,
            "session_id": session_id,
            "action": action,
            "verdict": verdict,
            "reason": reason,
        }
    )
    return verdict, reason
