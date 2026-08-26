"""Lifecycle tokens — short-lived, signed, capability-scoped, revocable trees."""

from __future__ import annotations

import hmac
import json
import secrets
import time
from hashlib import sha256
from typing import Any, Iterable
from uuid import uuid4

from app.security.environment import require_real_env
from app.security.hierarchy import (
    EXECUTION_CONTAINER,
    ROLE_CHILD,
    ROLE_PARENT,
    _CHILD_FORBIDDEN_CAPABILITIES,
    assert_parent_may_issue_child,
    validate_child_token_shape,
)


class SecurityError(Exception):
    pass


class CapabilityViolationError(SecurityError):
    pass


def _now_ts() -> int:
    return int(time.time())


def _supervisor_hmac_key() -> bytes:
    return require_real_env("HERMES_SUPERVISOR_HMAC_KEY").encode("utf-8")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hmac_sig(message: str, key: bytes) -> str:
    return hmac.new(key, message.encode("utf-8"), sha256).hexdigest()


# tree_id -> revocation metadata (in-memory; use Redis pub-sub in production for <1ms)
_REVOCATIONS: dict[str, dict[str, Any]] = {}


def revoke_tree(tree_id: str, reason: str = "revoked") -> None:
    _REVOCATIONS[tree_id] = {"revoked_at": _now_ts(), "reason": reason}


def is_revoked(tree_id: str) -> bool:
    return tree_id in _REVOCATIONS


def clear_revocations() -> None:
    """Test helper only."""
    _REVOCATIONS.clear()


def extract_tree_id(token: str | dict[str, Any] | None) -> str | None:
    if token is None:
        return None
    if isinstance(token, str):
        try:
            token = json.loads(token)
        except json.JSONDecodeError:
            return None
    if not isinstance(token, dict):
        return None
    tree_id = token.get("tree_id")
    return str(tree_id) if tree_id else None


def sign_token(token_without_sig: dict[str, Any]) -> str:
    return _hmac_sig(_canonical_json(token_without_sig), _supervisor_hmac_key())


def issue_token(
    *,
    tree_id: str,
    agent_id: str,
    capabilities: Iterable[str],
    ttl_seconds: int,
    merkle_root: str,
    parent_id: str | None = None,
    role: str = "parent",
) -> dict[str, Any]:
    if not merkle_root:
        raise SecurityError("cannot issue token without a live merkle root")
    now = _now_ts()
    token_body = {
        "tree_id": tree_id,
        "agent_id": agent_id,
        "parent_id": parent_id,
        "role": role,
        "execution_tier": EXECUTION_CONTAINER if role == ROLE_CHILD else "host",
        "capabilities": sorted(set(capabilities)),
        "issued_at": now,
        "expires_at": now + int(ttl_seconds),
        "nonce": secrets.token_hex(16),
        "merkle_root": merkle_root,
    }
    token_body["sig"] = sign_token(token_body)
    return token_body


_CHILD_FORBIDDEN = _CHILD_FORBIDDEN_CAPABILITIES


def issue_child_token(
    parent_token: dict[str, Any],
    child_capabilities: Iterable[str],
    ttl: int = 120,
) -> dict[str, Any]:
    ok, reason = validate_token(parent_token)
    if not ok:
        raise SecurityError(f"Cannot issue child token from invalid/expired parent: {reason}")

    try:
        assert_parent_may_issue_child(parent_token)
    except ValueError as exc:
        raise CapabilityViolationError(str(exc)) from exc

    parent_caps = set(parent_token.get("capabilities", []))
    requested_caps = set(child_capabilities)
    if not requested_caps.issubset(parent_caps):
        unauthorized = requested_caps - parent_caps
        raise CapabilityViolationError(f"Child requested unauthorized capabilities: {sorted(unauthorized)}")

    overlap = requested_caps & _CHILD_FORBIDDEN
    if overlap:
        raise CapabilityViolationError(f"Child cannot receive orchestrator capabilities: {sorted(overlap)}")

    return issue_token(
        tree_id=str(parent_token["tree_id"]),
        agent_id=str(uuid4()),
        capabilities=requested_caps,
        ttl_seconds=ttl,
        merkle_root=str(parent_token["merkle_root"]),
        parent_id=str(parent_token["agent_id"]),
        role=ROLE_CHILD,
    )


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


def validate_token(token: str | dict[str, Any] | None) -> tuple[bool, str]:
    """Fail-closed: signature, expiry, revocation."""
    parsed = _parse_token(token)
    if not parsed:
        return False, "missing or unparseable token"

    try:
        required = (
            "tree_id",
            "agent_id",
            "capabilities",
            "issued_at",
            "expires_at",
            "nonce",
            "merkle_root",
            "sig",
        )
        for field in required:
            if field not in parsed:
                return False, f"token missing field: {field}"

        if not str(parsed.get("merkle_root") or ""):
            return False, "token missing merkle root"

        tree_id = str(parsed["tree_id"])
        if is_revoked(tree_id):
            return False, "token tree revoked"

        if _now_ts() > int(parsed.get("expires_at", 0)):
            return False, "token expired"

        sig = str(parsed.get("sig", ""))
        token_without_sig = dict(parsed)
        token_without_sig.pop("sig", None)
        if not hmac.compare_digest(sig, sign_token(token_without_sig)):
            return False, "token signature invalid"

        caps = parsed.get("capabilities", [])
        if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps):
            return False, "token capabilities invalid"

        shape_ok, shape_reason = validate_child_token_shape(parsed)
        if not shape_ok:
            return False, shape_reason

        return True, "ok"
    except Exception as exc:
        return False, f"token validation exception: {exc}"


def capability_allowed(token: dict[str, Any], capability: str) -> bool:
    return capability in set(token.get("capabilities", []))
