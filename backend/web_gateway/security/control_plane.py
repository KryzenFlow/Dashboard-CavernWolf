"""Live Merkle control plane for Claw Opus.

Claw Opus will not run without a valid Merkle root. A missing, forged, or
mismatched root raises an alert and terminates the docked Claw daemon.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from .ledger import append_decision
from .merkle import compute_merkle_root, inclusion_proof, roots_match, verify_inclusion
from .token import SecurityError, _canonical_json, _now_ts, _supervisor_hmac_key, sign_token

_log = logging.getLogger(__name__)

_lock = Lock()
_leaves: list[str] = []
_root: str = ""
_halted = False
_bootstrapped = False


def _control_dir() -> Path:
    hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    path = hermes_home / "control"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _halt_file() -> Path:
    return _control_dir() / "HALT"


def _root_file() -> Path:
    return _control_dir() / "merkle_root.json"


def is_halted() -> bool:
    if _halted:
        return True
    return _halt_file().is_file()


def current_root() -> str:
    ensure_bootstrapped()
    return _root


def current_leaves() -> list[str]:
    ensure_bootstrapped()
    return list(_leaves)


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
                "plane": "claw-opus",
            }
        )
        _leaves = [genesis]
        _root = compute_merkle_root(_leaves)
        _persist_root("genesis")
        _bootstrapped = True
        _log.info("Merkle control plane genesis root=%s", _root[:16])


def _persist_root(reason: str) -> None:
    payload = {
        "merkle_root": _root,
        "leaf_count": len(_leaves),
        "reason": reason,
        "ts": _now_ts(),
    }
    payload["sig"] = sign_token(payload)
    _root_file().write_text(_canonical_json(payload) + "\n", encoding="utf-8")


def append_leaf(leaf: str, reason: str = "append") -> str:
    """Append a leaf and return the new root. Fail-closed if HMAC key is missing."""
    ensure_bootstrapped()
    _supervisor_hmac_key()
    with _lock:
        _leaves.append(leaf)
        global _root
        _root = compute_merkle_root(_leaves)
        _persist_root(reason)
        return _root


def proof_for_leaf(leaf: str) -> tuple[str, list[dict[str, str]]]:
    ensure_bootstrapped()
    try:
        idx = _leaves.index(leaf)
    except ValueError as exc:
        raise SecurityError("leaf not in merkle tree") from exc
    return _root, inclusion_proof(_leaves, idx)


def verify_control(merkle_root: str | None, leaf: str | None = None, proof: list[dict[str, str]] | None = None) -> tuple[bool, str]:
    """Authenticate against the live Merkle root. Empty/missing root is a control failure."""
    ensure_bootstrapped()
    if is_halted():
        return False, "control plane halted"
    if not merkle_root:
        return False, "merkle root required"
    if not roots_match(merkle_root, _root):
        recomputed = compute_merkle_root(_leaves)
        if not roots_match(recomputed, _root):
            return False, "merkle tamper detected"
        return False, "merkle root mismatch"
    if leaf is not None:
        if proof is None:
            try:
                _, proof = proof_for_leaf(leaf)
            except SecurityError as exc:
                return False, str(exc)
        if not verify_inclusion(leaf, proof, _root):
            return False, "merkle inclusion proof failed"
    return True, "ok"


def record_decision(decision: dict[str, Any]) -> str:
    """Audit-only. Does not grow the Merkle tree (Claw will not listen if memory stacks)."""
    ensure_bootstrapped()
    entry = dict(decision)
    entry["merkle_root"] = _root
    append_decision(entry)
    return _root


def alert(reason: str, *, details: dict[str, Any] | None = None) -> None:
    payload = {
        "type": "ALERT",
        "reason": reason,
        "details": details or {},
        "ts": _now_ts(),
        "merkle_root": _root,
    }
    _log.critical("CLAW-OPUS ALERT: %s", reason)
    try:
        append_leaf(_canonical_json(payload), reason="alert")
        record_decision({"action": "security.alert", "verdict": "BLOCK", "reason": reason, **payload})
    except Exception as exc:
        _log.critical("alert ledger failed: %s", exc)
    webhook = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
    if webhook:
        try:
            req = urllib.request.Request(
                webhook,
                data=_canonical_json(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception as exc:
            _log.warning("alert webhook failed: %s", exc)


def terminate_docked_daemon(reason: str, *, persist_halt: bool = True) -> dict[str, Any]:
    """Fail-closed kill of the docked Claw Opus daemon only — never the host docker daemon."""
    global _halted
    if persist_halt:
        _halted = True
        _halt_file().write_text(_canonical_json({"reason": reason, "ts": _now_ts()}) + "\n", encoding="utf-8")
        alert(f"terminating docked claw daemon: {reason}")
    else:
        _log.info("terminating docked claw daemon after use: %s", reason)

    results: dict[str, Any] = {"halted": True, "reason": reason, "self_halt": None, "docker_kill": None}

    claw_url = os.environ.get("CLAW_URL", "http://claw-opus:9000").rstrip("/")
    try:
        req = urllib.request.Request(
            f"{claw_url}/internal/halt",
            data=_canonical_json({"reason": reason, "merkle_root": _root}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2)
        results["self_halt"] = "signaled"
    except Exception as exc:
        results["self_halt"] = f"unreachable:{exc}"

    if os.environ.get("CLAW_DOCKER_KILL", "0") == "1":
        container = os.environ.get("CLAW_CONTAINER", "claw-opus")
        if container == "claw-opus" and container.replace("-", "").isalnum():
            try:
                subprocess.run(
                    ["docker", "kill", "--signal=SIGTERM", container],
                    check=False,
                    timeout=5,
                    capture_output=True,
                    text=True,
                )
                results["docker_kill"] = "signaled"
            except Exception as exc:
                results["docker_kill"] = str(exc)
        else:
            results["docker_kill"] = "refused: container name not allowlisted"

    return results


def fail_control(reason: str) -> dict[str, Any]:
    """Missing or invalid Merkle control → alert + kill docked Claw Opus."""
    alert(reason)
    return terminate_docked_daemon(reason, persist_halt=True)


def token_leaf(token: dict[str, Any]) -> str:
    body = {k: v for k, v in token.items() if k != "sig"}
    return _canonical_json(body)


def register_token(token: dict[str, Any]) -> str:
    """Bind a signed token into the Merkle tree. Required for later auth."""
    return append_leaf(token_leaf(token), reason="token.issue")


def token_in_tree(token: dict[str, Any]) -> bool:
    ensure_bootstrapped()
    return token_leaf(token) in _leaves


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))


def purge_cycle_memory() -> None:
    """Drop stacked session memory so Claw will listen on the next cycle."""
    home = _hermes_home()
    for name in ("memory", "sessions"):
        path = home / name
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)
    _log.info("purged cycle memory under %s", home)


def clear_halt() -> None:
    global _halted
    _halted = False
    halt = _halt_file()
    if halt.is_file():
        halt.unlink()


def terminate_after_use(reason: str = "cycle complete") -> dict[str, Any]:
    """End-of-use: kill Claw, wipe cycle memory, allow a fresh daemon to re-auth."""
    purge_cycle_memory()
    result = terminate_docked_daemon(reason, persist_halt=False)
    clear_halt()
    return result


def daily_rebuild() -> dict[str, Any]:
    """Once a day: new Merkle genesis, empty memory, terminate Claw, allow rebuild."""
    global _bootstrapped, _leaves, _root
    terminate_docked_daemon("daily rebuild", persist_halt=False)
    purge_cycle_memory()
    ledger = _hermes_home() / "ledger"
    if ledger.is_dir():
        shutil.rmtree(ledger, ignore_errors=True)
    with _lock:
        _leaves = []
        _root = ""
        _bootstrapped = False
    clear_halt()
    ensure_bootstrapped()
    _log.info("daily rebuild complete root=%s", _root[:16])
    return {"rebuilt": True, "merkle_root": _root}
