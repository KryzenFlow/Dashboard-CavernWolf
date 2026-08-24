"""Resolve Tailscale IPv4 for WSL FastAPI bind. Fail closed if required and missing."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

_log = logging.getLogger(__name__)


def detect_tailscale_ipv4() -> str | None:
    forced = os.environ.get("TS_IP", "").strip() or os.environ.get("TAILSCALE_IP", "").strip()
    if forced:
        return forced

    bw = shutil.which("tailscale")
    if not bw:
        return None
    try:
        completed = subprocess.run(
            [bw, "ip", "-4"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    for line in (completed.stdout or "").splitlines():
        candidate = line.strip()
        if candidate and candidate[0].isdigit():
            return candidate
    return None


def resolve_bind_host() -> str:
    """
    Prefer explicit HERMES_BIND_HOST, else Tailscale IPv4 when
    HERMES_BIND_TAILSCALE=1 (default for wsl_backend). Never bind all
    interfaces unless explicitly allowed for docker/Tailscale-serve.
    """
    explicit = os.environ.get("HERMES_BIND_HOST", "").strip()
    if explicit:
        return explicit

    allow_all = os.environ.get("HERMES_BIND_ALL", "0") == "1"
    want_ts = os.environ.get("HERMES_BIND_TAILSCALE", "1") == "1"

    if want_ts:
        ts_ip = detect_tailscale_ipv4()
        if ts_ip:
            _log.info("binding to Tailscale IPv4 %s", ts_ip)
            return ts_ip
        if not allow_all:
            raise RuntimeError(
                "Tailscale IPv4 not found. Set TS_IP / join the tailnet, "
                "or HERMES_BIND_HOST=127.0.0.1 for loopback-only WSL testing."
            )

    if allow_all:
        return "0.0.0.0"
    return "127.0.0.1"
