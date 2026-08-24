from __future__ import annotations

import hmac
import json
import os
import time
from hashlib import sha256
from pathlib import Path
from typing import Any

from .merkle import compute_merkle_root
from .token import _canonical_json, _hmac_sig, _now_ts


def _ledger_base_dir() -> Path:
    hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    return hermes_home / "ledger"


def _ledger_hmac_key() -> bytes:
    from .environment import require_real_env

    return require_real_env("HERMES_SUPERVISOR_HMAC_KEY").encode("utf-8")


def _decisions_path() -> Path:
    return _ledger_base_dir() / "decisions.jsonl"


def _roots_path() -> Path:
    return _ledger_base_dir() / "merkle_roots.jsonl"


def _ensure_dirs() -> None:
    _ledger_base_dir().mkdir(parents=True, exist_ok=True)


def append_decision(decision: dict[str, Any]) -> None:
    """
    Append a fail-closed supervisor decision to a JSONL ledger.
    Also periodically emits a Merkle root for tamper evidence.
    """
    _ensure_dirs()

    hmac_key = _ledger_hmac_key()

    entry = dict(decision)
    entry.setdefault("ts", _now_ts())
    entry.setdefault("decision_id", sha256(_canonical_json(entry).encode("utf-8")).hexdigest())

    # Compute leaf hash for later Merkle batching.
    leaf = sha256(_canonical_json(entry).encode("utf-8")).hexdigest()
    entry["leaf_hash"] = leaf

    sig_target = dict(entry)
    sig_target.pop("ledger_sig", None)
    entry["ledger_sig"] = _hmac_sig(_canonical_json(sig_target), hmac_key)

    _decisions_path().open("a", encoding="utf-8").write(json.dumps(entry, sort_keys=True) + "\n")

    batch_size = int(os.environ.get("HERMES_LEDGER_BATCH_SIZE", "50"))

    # Compute Merkle root only when we have enough leaves.
    # Keep it simple/robust for this v1 implementation.
    try:
        # Count lines quickly.
        # If the file is huge, this could be optimized; for this repo it's acceptable.
        with _decisions_path().open("r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) % batch_size != 0:
            return

        recent = lines[-batch_size:]
        recent_leaves: list[str] = []
        for line in recent:
            parsed = json.loads(line)
            if "leaf_hash" in parsed:
                recent_leaves.append(str(parsed["leaf_hash"]))
        root = compute_merkle_root(recent_leaves)

        root_entry = {
            "ts": _now_ts(),
            "batch_size": batch_size,
            "from_idx": max(0, len(lines) - batch_size),
            "to_idx_exclusive": len(lines),
            "merkle_root": root,
        }
        root_sig = _hmac_sig(_canonical_json(root_entry), hmac_key)
        root_entry["ledger_sig"] = root_sig
        _roots_path().open("a", encoding="utf-8").write(json.dumps(root_entry, sort_keys=True) + "\n")
    except Exception:
        # Never block requests on ledger failures; but keep the ledger best-effort.
        return

