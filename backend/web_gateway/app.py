"""FastAPI application for Hermes web gateway.

Governance: soul.md (Trust Discipline Framework) + CI.md (Cognitive Interface).
All sessions must load root context before handling requests in production.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from routes.api import router as api_router

_log = logging.getLogger(__name__)

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
SKILLS_DIR = HERMES_HOME / "skills"
MOCK_MODE = os.environ.get("HERMES_MOCK", "1") == "1"

active_connections: set[WebSocket] = set()
sessions: dict[str, dict[str, Any]] = {}


def create_app() -> FastAPI:
    app = FastAPI(title="Hermes Web Gateway", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "gateway": "hermes-web",
            "mock_mode": MOCK_MODE,
            "active_connections": len(active_connections),
            "governance": {
                "framework": "Trust Discipline Framework",
                "soul": "soul.md",
                "ci": "CI.md",
            },
        }

    @app.get("/info")
    async def info() -> dict[str, Any]:
        return {
            "gateway": "hermes-web",
            "version": "0.1.0",
            "mock_mode": MOCK_MODE,
            "hermes_home": str(HERMES_HOME),
            "active_connections": len(active_connections),
            "sessions": len(sessions),
        }

    @app.get("/sessions")
    async def list_sessions() -> dict[str, Any]:
        return {
            "sessions": [
                {
                    "session_id": sid,
                    "session_key": meta.get("session_key"),
                    "running": meta.get("running", False),
                    "model": meta.get("model", "mock"),
                }
                for sid, meta in sessions.items()
            ]
        }

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        active_connections.add(websocket)
        try:
            while True:
                raw = await websocket.receive_text()
                for line in raw.splitlines():
                    if not line.strip():
                        continue
                    response = await handle_rpc(json.loads(line), websocket)
                    if response is not None:
                        await websocket.send_text(json.dumps(response))
        except WebSocketDisconnect:
            pass
        finally:
            active_connections.discard(websocket)

    return app


async def handle_rpc(msg: dict[str, Any], websocket: WebSocket) -> dict[str, Any] | None:
    method = msg.get("method")
    params = msg.get("params") or {}
    req_id = msg.get("id")

    if method == "session.create":
        sid = str(uuid.uuid4())
        sessions[sid] = {
            "session_key": params.get("session_key", sid),
            "running": False,
            "model": "mock:gpt-4",
        }
        return {"jsonrpc": "2.0", "id": req_id, "result": {"session_id": sid, "status": "ready"}}

    if method == "message.send":
        sid = params.get("session_id", "web-1")
        text = params.get("text", "")
        sessions.setdefault(sid, {"session_key": sid, "running": True})

        await websocket.send_text(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "event",
                    "params": {"type": "message.start", "payload": {"session_id": sid}},
                }
            )
        )

        reply = (
            f"[Mock Hermes] Received: {text[:200]}"
            if MOCK_MODE
            else "Message queued for Hermes agent."
        )
        for chunk in _chunk_text(reply, 24):
            await asyncio.sleep(0.05)
            await websocket.send_text(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "event",
                        "params": {"type": "message.delta", "payload": {"text": chunk}},
                    }
                )
            )

        await websocket.send_text(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "event",
                    "params": {"type": "message.complete", "payload": {"session_id": sid}},
                }
            )
        )
        sessions[sid]["running"] = False
        return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "queued"}}

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }
    return None


def _chunk_text(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)]
