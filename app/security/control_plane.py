"""Live Merkle control plane for issued tokens and decision leaves."""

from __future__ import annotations

import os
from threading import Lock
from typing import Any
from uuid import uuid4

from app.security.merkle_auth import compute_merkle_root, roots_match
from app.security.token import _canonical_json, _now_ts

_lock = Lock()
_leaves: list[str] = []
_root: str = ""
_bootstrapped = False


def ensure_bootstrapped() -> None:
    global _bootstrapped, _leaves, _root
    with _lock:
        if _bootstrapped and _root:
            return
        genesis = _canonical_json(
            {
                "type": "genesis",
                "nonce": uuid4().hex,
                "ts": _now_ts(),
                "plane": "supervisor",
            }
        )
        _leaves = [genesis]
        _root = compute_merkle_root(_leaves)
        _bootstrapped = True


def current_root() -> str:
    ensure_bootstrapped()
    return _root


def current_leaves() -> list[str]:
    ensure_bootstrapped()
    return list(_leaves)


def register_token_leaf(token: dict[str, Any]) -> None:
    """Append issued token to Merkle tree (supervisor-only)."""
    global _leaves, _root
    ensure_bootstrapped()
    leaf = _canonical_json(
        {
            "type": "token_issue",
            "tree_id": token.get("tree_id"),
            "agent_id": token.get("agent_id"),
            "capabilities": token.get("capabilities"),
            "expires_at": token.get("expires_at"),
        }
    )
    with _lock:
        _leaves.append(leaf)
        _root = compute_merkle_root(_leaves)


def register_decision_leaf(decision: dict[str, Any]) -> None:
    global _leaves, _root
    ensure_bootstrapped()
    leaf = _canonical_json({"type": "decision", **decision})
    with _lock:
        _leaves.append(leaf)
        _root = compute_merkle_root(_leaves)


def verify_live_root() -> bool:
    ensure_bootstrapped()
    return roots_match(compute_merkle_root(current_leaves()), current_root())


def token_merkle_root_matches(token: dict[str, Any]) -> bool:
    return roots_match(str(token.get("merkle_root", "")), current_root())


def reset_control_plane() -> None:
    """Test helper only."""
    global _bootstrapped, _leaves, _root
    with _lock:
        _leaves = []
        _root = ""
        _bootstrapped = False


def batch_window() -> tuple[int, int]:
    """Merkle batching: N decisions or T seconds (env override)."""
    batch_size = int(os.environ.get("HERMES_LEDGER_BATCH_SIZE", "50"))
    batch_seconds = int(os.environ.get("HERMES_MERKLE_BATCH_SECONDS", "10"))
    return batch_size, batch_seconds
