"""Hermes → Claw Opus only. No mock replies. Fail-closed if Claw is down or halted."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .control_plane import current_root, fail_control, is_halted, verify_control


class ClawUnavailable(Exception):
    pass


def _claw_url() -> str:
    return os.environ.get("CLAW_URL", "http://claw-opus:9000").rstrip("/")


def claw_chat(*, text: str, session_id: str, merkle_root: str, token: dict[str, Any]) -> str:
    if is_halted():
        raise ClawUnavailable("claw daemon halted")
    ok, reason = verify_control(merkle_root)
    if not ok:
        fail_control(reason)
        raise ClawUnavailable(f"merkle control failed: {reason}")

    payload = {
        "text": text,
        "session_id": session_id,
        "merkle_root": current_root(),
        "lifecycle_token": token,
    }
    try:
        req = urllib.request.Request(
            f"{_claw_url()}/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code in {401, 403}:
            fail_control(f"claw rejected merkle auth: {detail[:300]}")
        raise ClawUnavailable(detail[:500]) from exc
    except Exception as exc:
        raise ClawUnavailable(str(exc)) from exc

    if body.get("halted"):
        fail_control(str(body.get("reason", "claw self-halted")))
        raise ClawUnavailable("claw halted")
    text_out = body.get("text")
    if not isinstance(text_out, str) or not text_out:
        raise ClawUnavailable("claw returned no text")
    return text_out
