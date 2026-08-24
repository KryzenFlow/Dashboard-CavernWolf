from __future__ import annotations

import hmac
import json
import time
from hashlib import sha256
from typing import Any, Iterable
from uuid import uuid4


class SecurityError(Exception):
    pass


class TokenVerificationError(SecurityError):
    pass


def _now_ts() -> int:
    return int(time.time())


def _supervisor_hmac_key() -> bytes:
    from .environment import require_real_env

    return require_real_env("HERMES_SUPERVISOR_HMAC_KEY").encode("utf-8")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hmac_sig(message: str, key: bytes) -> str:
    return hmac.new(key, message.encode("utf-8"), sha256).hexdigest()


# tree_id -> revoked info
_REVOCATIONS: dict[str, dict[str, Any]] = {}


def revoke_tree(tree_id: str, reason: str = "revoked") -> None:
    _REVOCATIONS[tree_id] = {"revoked_at": _now_ts(), "reason": reason}


def is_revoked(tree_id: str) -> bool:
    return tree_id in _REVOCATIONS


def extract_tree_id(token: str | dict[str, Any] | None) -> str | None:
    if token is None:
        return None
    if isinstance(token, str):
        try:
            token = json.loads(token)
        except Exception:
            return None
    return token.get("tree_id")


def sign_token(token_without_sig: dict[str, Any]) -> str:
    key = _supervisor_hmac_key()
    message = _canonical_json(token_without_sig)
    return _hmac_sig(message, key)


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
    token_without_sig = {
        "tree_id": tree_id,
        "agent_id": agent_id,
        "parent_id": parent_id,
        "role": role,
        "capabilities": sorted(set(capabilities)),
        "issued_at": now,
        "expires_at": now + int(ttl_seconds),
        "nonce": uuid4().hex,
        "merkle_root": merkle_root,
    }
    token_without_sig["sig"] = sign_token(token_without_sig)
    return token_without_sig


_CHILD_FORBIDDEN = frozenset(
    {
        "orch:ask_hermes",
        "claw:invoke",
        "ws:message.send",
        "rest:git.commit",
        "rest:git.push",
    }
)


def issue_child_token(
    parent_token: dict[str, Any],
    child_capabilities: Iterable[str],
    ttl: int = 120,
) -> dict[str, Any]:
    ok, reason = validate_token(parent_token)
    if not ok:
        raise SecurityError(f"Cannot issue child token from invalid/expired parent: {reason}")
    parent_caps = set(parent_token.get("capabilities", []))
    requested_caps = set(child_capabilities)
    if not requested_caps.issubset(parent_caps):
        unauthorized = requested_caps - parent_caps
        raise SecurityError(f"Child requested unauthorized capabilities: {sorted(unauthorized)}")
    overlap = requested_caps & _CHILD_FORBIDDEN
    if overlap:
        raise SecurityError(f"Child cannot receive parent/orchestrator capabilities: {sorted(overlap)}")
    return issue_token(
        tree_id=str(parent_token["tree_id"]),
        agent_id=str(uuid4()),
        capabilities=requested_caps,
        ttl_seconds=ttl,
        merkle_root=str(parent_token["merkle_root"]),
        parent_id=str(parent_token["agent_id"]),
        role="child",
    )


def _parse_token(token: str | dict[str, Any] | None) -> dict[str, Any] | None:
    if token is None:
        return None
    if isinstance(token, str):
        try:
            return json.loads(token)
        except Exception:
            return None
    return token


def validate_token(token: str | dict[str, Any] | None) -> tuple[bool, str]:
    """
    Fail-closed validation:
    - signature check
    - expiry check
    - revocation check
    """
    parsed = _parse_token(token)
    if not parsed:
        return False, "missing or unparseable token"

    try:
        required_fields = [
            "tree_id",
            "agent_id",
            "capabilities",
            "issued_at",
            "expires_at",
            "nonce",
            "merkle_root",
            "sig",
        ]
        for f in required_fields:
            if f not in parsed:
                return False, f"token missing field: {f}"
        if not str(parsed.get("merkle_root") or ""):
            return False, "token missing merkle root (no false environment)"

        tree_id = str(parsed["tree_id"])
        if is_revoked(tree_id):
            return False, "token tree revoked"

        now = _now_ts()
        if now > int(parsed.get("expires_at", 0)):
            return False, "token expired"

        sig = str(parsed.get("sig", ""))
        token_without_sig = dict(parsed)
        token_without_sig.pop("sig", None)
        expected_sig = sign_token(token_without_sig)
        if not hmac.compare_digest(sig, expected_sig):
            return False, "token signature invalid"

        # Capabilities must be a list of strings.
        caps = parsed.get("capabilities", [])
        if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps):
            return False, "token capabilities invalid"

        return True, "ok"
    except Exception as e:  # pragma: no cover
        return False, f"token validation exception: {e}"


def capability_allowed(token: dict[str, Any], capability: str) -> bool:
    return capability in set(token.get("capabilities", []))


def ensure_child_capabilities_subset(
    parent_token: dict[str, Any], child_capabilities: Iterable[str]
) -> tuple[bool, str]:
    parent_caps = set(parent_token.get("capabilities", []))
    requested_caps = set(child_capabilities)
    if not requested_caps.issubset(parent_caps):
        unauthorized = requested_caps - parent_caps
        return False, f"unauthorized capabilities requested: {sorted(unauthorized)}"
    return True, "ok"

