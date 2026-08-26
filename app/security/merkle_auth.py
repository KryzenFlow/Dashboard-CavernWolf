"""Merkle tree for lifecycle token / decision batch authentication."""

from __future__ import annotations

import hmac
from hashlib import sha256


def leaf_digest(leaf: str) -> bytes:
    return sha256(leaf.encode("utf-8")).digest()


def compute_merkle_root(leaves: list[str]) -> str:
    """SHA-256 Merkle root over ordered string leaves. Empty tree returns \"\"."""
    if not leaves:
        return ""
    level = [leaf_digest(leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        nxt: list[bytes] = []
        for i in range(0, len(level), 2):
            nxt.append(sha256(level[i] + level[i + 1]).digest())
        level = nxt
    return level[0].hex()


def verify_inclusion(leaf: str, proof: list[dict[str, str]], root_hex: str) -> bool:
    if not root_hex or not leaf:
        return False
    node = leaf_digest(leaf)
    try:
        for step in proof:
            sibling = bytes.fromhex(step["sibling"])
            side = step.get("side")
            if side == "left":
                node = sha256(sibling + node).digest()
            elif side == "right":
                node = sha256(node + sibling).digest()
            else:
                return False
        return hmac.compare_digest(node.hex(), root_hex)
    except (KeyError, ValueError, TypeError):
        return False


def roots_match(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return hmac.compare_digest(left, right)
