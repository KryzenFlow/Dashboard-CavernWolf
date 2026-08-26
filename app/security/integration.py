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
from app.security.hierarchy import (
    EXECUTION_CONTAINER,
    ROLE_PARENT,
    child_must_ask_parent,
    is_child_token,
    parent_may_contact_supervisor,
)
from app.security.decision_ledger import append_decision
from app.security.supervisor_gates import validate_and_gate
from app.security.revocation_policy import RevocationScope, classify_block
from app.security.token import (
    CapabilityViolationError,
    SecurityError,
    capability_allowed,
    extract_agent_id,
    extract_tree_id,
    issue_child_token,
    issue_token,
    revoke_agent,
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


def _apply_block_revocation(
    token: dict[str, Any] | str | None,
    reason: str,
) -> RevocationScope:
    """Apply minimum-scope revocation for a BLOCK. Returns scope applied."""
    token_dict = _parse_token(token)
    scope = classify_block(reason, token_dict)
    if scope == RevocationScope.TREE:
        tree_id = extract_tree_id(token)
        if tree_id:
            revoke_tree(tree_id, reason=reason)
    elif scope == RevocationScope.AGENT:
        agent_id = extract_agent_id(token)
        if agent_id:
            revoke_agent(agent_id, reason=reason)
    return scope


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
    1. Fast deterministic gates (A–C) — **parent only**; children ask parent, never supervisor
    2. Supervisor decision on PASS — spawn short-lived child in container behind parent
    3. BLOCK → scoped revocation (agent or tree only when warranted) + ledger
    """
    token_dict = _parse_token(incoming_token)
    if token_dict and is_child_token(token_dict):
        reason = "children cannot contact supervisor; route through parent (ask_parent)"
        _apply_block_revocation(incoming_token, reason)
        log_decision(
            payload=payload,
            token=incoming_token,
            verdict="BLOCK",
            reason=reason,
            agent_name=agent_name,
            session_id=session_id,
        )
        return GateResult(verdict="BLOCK", reason=reason)

    if token_dict and not parent_may_contact_supervisor(token_dict):
        reason = "only host-tier parent may contact supervisor"
        return GateResult(verdict="BLOCK", reason=reason)

    action = str(payload.get("action") or "")
    verdict, reason = validate_and_gate(
        payload,
        incoming_token,
        action=action,
        agent_name=agent_name,
        session_id=session_id,
    )

    if verdict != "PASS":
        _apply_block_revocation(incoming_token, reason)
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
        if is_child_token(token_dict):
            return GateResult(
                verdict="BLOCK",
                reason="children cannot spawn children; only parent issues container workers",
            )
        try:
            child_token = finalize_issued_token(
                issue_child_token(token_dict, child_capabilities, ttl=child_ttl)
            )
            assert child_token.get("execution_tier") == EXECUTION_CONTAINER
            assert child_token.get("role") == "child"
            assert child_token.get("parent_id") == token_dict.get("agent_id")
        except (SecurityError, CapabilityViolationError) as exc:
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


def bootstrap_parent_session(
    capabilities: list[str],
    *,
    ttl_seconds: int = 300,
    tree_id: str | None = None,
) -> dict[str, Any]:
    """Issue host-tier parent token. Parent talks to supervisor; children never do."""
    ensure_bootstrapped()
    root = current_root()
    token = finalize_issued_token(
        issue_token(
            tree_id=tree_id or str(uuid4()),
            agent_id=str(uuid4()),
            capabilities=capabilities,
            ttl_seconds=ttl_seconds,
            merkle_root=root,
            role=ROLE_PARENT,
        )
    )
    assert token.get("execution_tier") == "host"
    return token


def bootstrap_supervisor_session(
    capabilities: list[str],
    *,
    ttl_seconds: int = 300,
    tree_id: str | None = None,
) -> dict[str, Any]:
    """Alias for bootstrap_parent_session — parent is the supervisor-facing session."""
    return bootstrap_parent_session(capabilities, ttl_seconds=ttl_seconds, tree_id=tree_id)


def handle_child_via_parent(
    payload: dict[str, Any],
    child_token: dict[str, Any],
    parent_token: dict[str, Any],
) -> GateResult:
    """
    Child → parent route only. Child runs in container; parent forwards to supervisor if needed.
    Child payload action must be ask_parent or a granted worker capability — never supervisor.
    """
    if not is_child_token(child_token):
        return GateResult(verdict="BLOCK", reason="handle_child_via_parent requires child token")
    if is_child_token(parent_token):
        return GateResult(verdict="BLOCK", reason="parent must be host-tier, not child")

    action = str(payload.get("action") or "")
    allowed, reason = child_must_ask_parent(child_token, action)
    if not allowed:
        _apply_block_revocation(child_token, reason)
        return GateResult(verdict="BLOCK", reason=reason)

    if action == "ask_parent":
        # Parent receives child's ask — parent decides whether to call supervisor.
        log_decision(
            payload=payload,
            token=child_token,
            verdict="PASS",
            reason="child ask_parent received by parent (not forwarded to supervisor)",
            agent_name=str(child_token.get("agent_id", "")),
            session_id=str(child_token.get("tree_id", "")),
        )
        return GateResult(verdict="PASS", reason="routed to parent")

    # Worker action inside container — parent already granted capability; no supervisor contact.
    if not capability_allowed(child_token, action):
        return GateResult(verdict="BLOCK", reason=f"child capability denied: {action}")
    return GateResult(verdict="PASS", reason="child worker action in container")
