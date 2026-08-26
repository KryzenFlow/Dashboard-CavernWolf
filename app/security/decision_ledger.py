"""HMAC-signed decision ledger with optional Merkle batch roots."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from pathlib import Path
from typing import Any

from app.security.control_plane import batch_window, register_decision_leaf
from app.security.merkle_auth import compute_merkle_root
from app.security.token import _canonical_json, _hmac_sig, _now_ts, _supervisor_hmac_key


def _ledger_dir() -> Path:
    hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    path = hermes_home / "ledger"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _decisions_path() -> Path:
    return _ledger_dir() / "decisions.jsonl"


def _roots_path() -> Path:
    return _ledger_dir() / "merkle_roots.jsonl"


def append_decision(decision: dict[str, Any]) -> None:
    """Append fail-closed supervisor decision; batch Merkle roots periodically."""
    hmac_key = _supervisor_hmac_key()

    entry = dict(decision)
    entry.setdefault("ts", _now_ts())
    entry.setdefault("decision_id", sha256(_canonical_json(entry).encode("utf-8")).hexdigest())

    leaf = sha256(_canonical_json(entry).encode("utf-8")).hexdigest()
    entry["leaf_hash"] = leaf

    sig_target = dict(entry)
    sig_target.pop("ledger_sig", None)
    entry["ledger_sig"] = _hmac_sig(_canonical_json(sig_target), hmac_key)

    register_decision_leaf(
        {
            "decision_id": entry["decision_id"],
            "verdict": entry.get("verdict"),
            "action": entry.get("action"),
            "tree_id": entry.get("tree_id"),
        }
    )

    with _decisions_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")

    batch_size, _ = batch_window()
    try:
        lines = _decisions_path().read_text(encoding="utf-8").splitlines()
        if not lines or len(lines) % batch_size != 0:
            return
        recent = lines[-batch_size:]
        recent_leaves = [
            str(json.loads(line).get("leaf_hash", ""))
            for line in recent
            if json.loads(line).get("leaf_hash")
        ]
        root = compute_merkle_root(recent_leaves)
        root_entry = {
            "ts": _now_ts(),
            "batch_size": batch_size,
            "from_idx": max(0, len(lines) - batch_size),
            "to_idx_exclusive": len(lines),
            "merkle_root": root,
        }
        root_entry["ledger_sig"] = _hmac_sig(_canonical_json(root_entry), hmac_key)
        with _roots_path().open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(root_entry, sort_keys=True) + "\n")
    except OSError:
        return
