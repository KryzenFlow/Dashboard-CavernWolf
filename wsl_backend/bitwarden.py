"""Bitwarden CLI secret pull. No local .env for production secrets. No shell=True."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Mapping

_log = logging.getLogger(__name__)

# Env var -> Bitwarden item name (password field)
DEFAULT_SECRET_MAP: dict[str, str] = {
    "HERMES_SUPERVISOR_HMAC_KEY": "hermes-supervisor-hmac",
    "OPENCLAW_GATEWAY_URL": "openclaw-gateway-url",
    "OPENCLAW_GATEWAY_TOKEN": "openclaw-gateway-token",
    "TS_AUTHKEY": "tailscale-authkey",
}


class BitwardenError(RuntimeError):
    pass


def _bw_bin() -> str:
    path = shutil.which("bw")
    if not path:
        raise BitwardenError("Bitwarden CLI (`bw`) not found on PATH")
    return path


def _run_bw(args: list[str], *, session: str) -> str:
    cmd = [_bw_bin(), *args, "--session", session]
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as exc:
        raise BitwardenError("bw CLI timed out") from exc
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "").strip()[:300]
        raise BitwardenError(f"bw failed ({completed.returncode}): {err}")
    return (completed.stdout or "").strip()


def ensure_unlocked(session: str) -> None:
    import json

    raw = _run_bw(["status"], session=session)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BitwardenError(f"bw status not JSON: {raw[:120]}") from exc
    if payload.get("status") != "unlocked":
        raise BitwardenError(
            "Bitwarden vault is not unlocked. Run: export BW_SESSION=$(bw unlock --raw)"
        )


def get_password(item_name: str, *, session: str) -> str:
    value = _run_bw(["get", "password", item_name], session=session)
    if not value:
        raise BitwardenError(f"empty password for Bitwarden item: {item_name}")
    return value


def pull_secrets_into_environ(
    mapping: Mapping[str, str] | None = None,
    *,
    overwrite: bool = False,
) -> list[str]:
    """
    Authenticate with Bitwarden CLI (session) and set process environment.
    Does not read a local .env file.
    Returns list of env keys that were set from the vault.
    """
    session = os.environ.get("BW_SESSION", "").strip()
    if not session:
        raise BitwardenError(
            "BW_SESSION is required. Unlock with: export BW_SESSION=$(bw unlock --raw)"
        )

    ensure_unlocked(session)
    secret_map = dict(mapping or DEFAULT_SECRET_MAP)
    set_keys: list[str] = []

    for env_key, item_name in secret_map.items():
        existing = os.environ.get(env_key, "").strip()
        if existing and not overwrite:
            _log.info("keeping existing env %s (not overwriting from Bitwarden)", env_key)
            continue
        value = get_password(item_name, session=session)
        os.environ[env_key] = value
        set_keys.append(env_key)
        _log.info("loaded %s from Bitwarden item %s", env_key, item_name)

    return set_keys
