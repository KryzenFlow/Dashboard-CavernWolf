"""
Supervisor integration sequence — entry point for agent actions and tool requests.

Refined control flow (fail-closed, supervisor authority, short-lived children).
See app/security/INTEGRATION_SEQUENCE.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.security.control_plane import current_root, ensure_bootstrapped
from app.security.decision_ledger import append_decision
from app.security.supervisor_gates import validate_and_gate
from app.security.token import (
    CapabilityViolationError,
    SecurityError,
    extract_tree_id,
    issue_child_token,
    issue_token,
    revoke_tree,
)
from app.security.token import _parse_token
from app.security.token_registry import finalize_issued_token
from app.security.watchers import WatcherHandle, start_dual_watchers


@dataclass
class GateResult:
    verdict: str
    reason: str
    child_token: dict[str, Any] | None = None
    watchers: WatcherHandle | None = None


def extract_request_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize incoming JSON — agent_id, session_id, action, paths, cmd, etc."""
    return {
        "agent_id": payload.get("agent_id"),
        "session_id": payload.get("session_id") or payload.get("tree_id"),
        "action": payload.get("action"),
        "paths": payload.get("paths") or payload.get("path"),
        "cmd": payload.get("cmd") or payload.get("command"),
        "lifecycle_token": payload.get("lifecycle_token") or payload.get("token"),
    }


def log_decision(
    *,
    payload: dict[str, Any],
    token: dict[str, Any] | str | None,
    verdict: str,
    reason: str,
    agent_name: str = "",
    session_id: str = "global",
) -> None:
    append_decision(
        {
            "tree_id": extract_tree_id(token),
            "agent_name": agent_name,
            "session_id": session_id,
            "action": payload.get("action"),
            "verdict": verdict,
            "reason": reason,
        }
    )


def handle_agent_request(
    payload: dict[str, Any],
    incoming_token: dict[str, Any] | str,
    *,
    child_capabilities: list[str] | None = None,
    child_ttl: int = 90,
    start_watchers: bool = False,
    agent_name: str = "",
    session_id: str = "global",
) -> GateResult:
    """
    1. Fast deterministic gates (A–C)
    2. Supervisor decision on PASS — optional child token + dual watchers
    3. BLOCK → revoke_tree + ledger
    """
    action = str(payload.get("action") or "")
    verdict, reason = validate_and_gate(
        payload,
        incoming_token,
        action=action,
        agent_name=agent_name,
        session_id=session_id,
    )

    if verdict != "PASS":
        tree_id = extract_tree_id(incoming_token)
        if tree_id:
            revoke_tree(tree_id, reason=reason)
        log_decision(
            payload=payload,
            token=incoming_token,
            verdict="BLOCK",
            reason=reason,
            agent_name=agent_name,
            session_id=session_id,
        )
        return GateResult(verdict="BLOCK", reason=reason)

    child_token = None
    watchers = None
    if child_capabilities is not None:
        token_dict = _parse_token(incoming_token)
        if not token_dict:
            return GateResult(verdict="BLOCK", reason="invalid token for child issuance")
        try:
            child_token = finalize_issued_token(
                issue_child_token(token_dict, child_capabilities, ttl=child_ttl)
            )
        except (SecurityError, CapabilityViolationError) as exc:
            tree_id = extract_tree_id(incoming_token)
            if tree_id:
                revoke_tree(tree_id, reason=str(exc))
            return GateResult(verdict="BLOCK", reason=str(exc))

        if start_watchers and child_token:
            watchers = start_dual_watchers(child_token, payload)

    log_decision(
        payload=payload,
        token=incoming_token,
        verdict="PASS",
        reason=reason,
        agent_name=agent_name,
        session_id=session_id,
    )

    return GateResult(
        verdict="PASS",
        reason=reason,
        child_token=child_token,
        watchers=watchers,
    )


def bootstrap_supervisor_session(
    capabilities: list[str],
    *,
    ttl_seconds: int = 300,
    tree_id: str | None = None,
) -> dict[str, Any]:
    """Issue parent supervisor token after control plane bootstrap."""
    ensure_bootstrapped()
    root = current_root()
    token = finalize_issued_token(
        issue_token(
            tree_id=tree_id or str(uuid4()),
            agent_id=str(uuid4()),
            capabilities=capabilities,
            ttl_seconds=ttl_seconds,
            merkle_root=root,
            role="parent",
        )
    )
    return token
