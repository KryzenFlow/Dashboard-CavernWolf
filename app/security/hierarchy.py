"""Role hierarchy — children ask parent, never supervisor; children run in containers."""

from __future__ import annotations

from typing import Any

ROLE_PARENT = "parent"
ROLE_CHILD = "child"

EXECUTION_CONTAINER = "container"
EXECUTION_HOST = "host"

# Child tokens may never hold these — they contact supervisor or bypass parent.
_CHILD_FORBIDDEN_CAPABILITIES = frozenset(
    {
        "orch:ask_hermes",
        "orch:ask_supervisor",
        "supervisor:request",
        "supervisor:gate",
        "gate:validate",
        "issue_child",
        "tool:grant_child",
        "claw:invoke",
        "ws:message.send",
        "rest:git.commit",
        "rest:git.push",
        "spawn:container",
    }
)

# Only parent (host-tier) tokens may call the supervisor gate or spawn children.
_PARENT_ONLY_CAPABILITIES = frozenset(
    {
        "issue_child",
        "spawn:container",
        "supervisor:request",
        "gate:validate",
        "tool:grant_child",
    }
)

# The only upward channel for a child — must route through parent, not supervisor.
_CHILD_UPWARD_CAPABILITY = "ask_parent"


def token_role(token: dict[str, Any]) -> str:
    return str(token.get("role") or ROLE_PARENT)


def is_child_token(token: dict[str, Any]) -> bool:
    return token_role(token) == ROLE_CHILD


def is_parent_token(token: dict[str, Any]) -> bool:
    return token_role(token) == ROLE_PARENT


def execution_tier(token: dict[str, Any]) -> str:
    if is_child_token(token):
        return EXECUTION_CONTAINER
    return str(token.get("execution_tier") or EXECUTION_HOST)


def child_must_ask_parent(token: dict[str, Any], action: str | None) -> tuple[bool, str]:
    """
    Children never contact supervisor. Upward requests use ask_parent only.
    Returns (allowed, reason).
    """
    if not is_child_token(token):
        return True, "ok"
    if not action:
        return False, "child must declare action; use ask_parent to reach parent"
    if action == _CHILD_UPWARD_CAPABILITY:
        if _CHILD_UPWARD_CAPABILITY in set(token.get("capabilities", [])):
            return True, "ok"
        return False, "child lacks ask_parent capability"
    if action in _CHILD_FORBIDDEN_CAPABILITIES or action in _PARENT_ONLY_CAPABILITIES:
        return False, f"child cannot use '{action}'; ask parent instead"
    if action.startswith("supervisor:") or action.startswith("gate:"):
        return False, "child cannot contact supervisor"
    return True, "ok"


def parent_may_contact_supervisor(token: dict[str, Any]) -> bool:
    return is_parent_token(token) and execution_tier(token) == EXECUTION_HOST


def assert_parent_may_issue_child(parent_token: dict[str, Any]) -> None:
    if is_child_token(parent_token):
        raise ValueError("children cannot issue tokens; only parent may spawn container children")
    if execution_tier(parent_token) != EXECUTION_HOST:
        raise ValueError("only host-tier parent may issue child tokens")


def validate_child_token_shape(token: dict[str, Any]) -> tuple[bool, str]:
    if not is_child_token(token):
        return True, "ok"
    if not token.get("parent_id"):
        return False, "child token missing parent_id"
    if token.get("execution_tier") != EXECUTION_CONTAINER:
        return False, "child token must declare execution_tier=container"
    return True, "ok"
