"""Claw Opus daemon. Real gateway only. No echo, no mock, halt after use."""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import urllib.error
import urllib.request
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_log = logging.getLogger("claw-opus")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Claw Opus")

_halted = False
_seen_this_cycle = False


class ChatRequest(BaseModel):
    text: str
    session_id: str
    merkle_root: str
    lifecycle_token: dict[str, Any]


class HaltRequest(BaseModel):
    reason: str = ""
    merkle_root: str = ""


def _hermes_url() -> str:
    return os.environ.get("HERMES_URL", "").rstrip("/")


def _gateway_url() -> str:
    return os.environ.get("OPENCLAW_GATEWAY_URL", "").rstrip("/")


def _halt(reason: str) -> None:
    global _halted
    _halted = True
    _log.critical("claw-opus halt: %s", reason)
    threading.Timer(0.2, lambda: os._exit(0)).start()


@app.get("/health")
def health() -> dict[str, Any]:
    if _halted:
        raise HTTPException(status_code=503, detail="halted")
    gw = _gateway_url()
    hermes = _hermes_url()
    if not gw or not hermes:
        raise HTTPException(status_code=503, detail="real gateway/hermes not configured")
    return {"status": "ok", "service": "claw-opus", "gateway": True}


@app.post("/internal/halt")
def internal_halt(req: HaltRequest) -> dict[str, Any]:
    _halt(req.reason or "supervisor halt")
    return {"halted": True}


@app.post("/chat")
def chat(req: ChatRequest) -> dict[str, Any]:
    global _seen_this_cycle
    if _halted:
        raise HTTPException(status_code=503, detail="halted")
    if _seen_this_cycle:
        _halt("refusing stacked cycle memory")
        raise HTTPException(status_code=503, detail="cycle already used")
    if not req.merkle_root:
        _halt("merkle root missing")
        raise HTTPException(status_code=401, detail="merkle root required")

    gateway = _gateway_url()
    if not gateway:
        raise HTTPException(status_code=503, detail="OPENCLAW_GATEWAY_URL is not set; no false environment")

    payload = {
        "type": "req",
        "id": req.session_id,
        "method": "chat.send",
        "params": {
            "sessionKey": req.session_id,
            "message": req.text,
            "idempotencyKey": req.session_id,
        },
    }
    try:
        http_req = urllib.request.Request(
            gateway,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
        if token:
            http_req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(http_req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=502, detail=exc.read().decode("utf-8", errors="replace")[:500]) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"openclaw gateway unreachable: {exc}") from exc

    text = ""
    if isinstance(body, dict):
        text = str(
            body.get("text")
            or (body.get("payload") or {}).get("text")
            or body.get("message")
            or ""
        )
    if not text:
        raise HTTPException(status_code=502, detail="openclaw returned no text")

    _seen_this_cycle = True
    threading.Timer(0.5, lambda: _halt("terminate after use")).start()
    return {"text": text, "agent": "claw-opus"}


if __name__ == "__main__":
    if os.environ.get("HERMES_MOCK", "0") == "1":
        sys.stderr.write("refusing to start: false environment HERMES_MOCK=1\n")
        sys.exit(2)
    if not _gateway_url() or not _hermes_url():
        sys.stderr.write("refusing to start: OPENCLAW_GATEWAY_URL and HERMES_URL are required\n")
        sys.exit(2)
    max_life = int(os.environ.get("CLAW_MAX_LIFETIME_SECONDS", "86400"))
    threading.Timer(max_life, lambda: _halt("daily lifetime")).start()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9000")))
