"""Blast-radius policy — scope revocation to the minimum affected agent(s)."""

from __future__ import annotations

from enum import Enum
from typing import Any

from app.security.hierarchy import is_child_token


class RevocationScope(str, Enum):
    NONE = "none"
    AGENT = "agent"
    TREE = "tree"


def classify_block(reason: str, token: dict[str, Any] | None = None) -> RevocationScope:
    """
    Map a BLOCK reason to revocation scope.

    - NONE: reject request only (path/doberman/capability/policy errors)
    - AGENT: revoke the offending child agent; parent and siblings stay alive
    - TREE: severe integrity or compromise signals — revoke entire tree
    """
    lower = reason.lower()

    tree_signals = (
        "signature invalid",
        "merkle tamper",
        "merkle root mismatch",
        "stale or forged",
        "token tree revoked",
    )
    if any(signal in lower for signal in tree_signals):
        return RevocationScope.TREE

    agent_signals = (
        "route through parent",
        "ask parent from container",
        "children cannot contact supervisor",
        "child capability denied",
        "handle_child_via_parent requires child token",
    )
    if token and is_child_token(token) and any(signal in lower for signal in agent_signals):
        return RevocationScope.AGENT

    if token and is_child_token(token) and "child" in lower and "spawn" in lower:
        return RevocationScope.AGENT

    return RevocationScope.NONE
