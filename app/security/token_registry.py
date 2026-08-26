"""Register issued tokens on the control plane and refresh merkle_root + signature."""

from __future__ import annotations

from typing import Any

from app.security.control_plane import current_root, register_token_leaf
from app.security.token import sign_token


def finalize_issued_token(token: dict[str, Any]) -> dict[str, Any]:
    """
    Append token to Merkle tree, then re-bind merkle_root + sig to the live root.
    Call immediately after issue_token() / issue_child_token().
    """
    register_token_leaf(token)
    refreshed = dict(token)
    refreshed.pop("sig", None)
    refreshed["merkle_root"] = current_root()
    refreshed["sig"] = sign_token(refreshed)
    return refreshed
