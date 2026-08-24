"""Hermes orchestrator — parent first, Claw Opus only, no mock replies."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.api import router as api_router
from web_gateway.security.claw_client import ClawUnavailable, claw_chat
from web_gateway.security.control_plane import current_root, ensure_bootstrapped, register_token
from web_gateway.security.cycle import after_use, daily_rebuild_loop
from web_gateway.security.supervisor_gates import gate_and_ledger_block_if_needed
from web_gateway.security.token import issue_token, is_revoked, revoke_tree, validate_token

_log = logging.getLogger(__name__)

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))

active_connections: set[WebSocket] = set()
sessions: dict[str, dict[str, Any]] = {}

PARENT_CAPABILITIES = {
    "ws:message.send",
    "rest:files:read",
    "rest:skill.save",
    "rest:skill.test",
    "rest:git.status:read",
    "orch:ask_hermes",
    "tool:grant_child",
}


async def _close_websocket_safely(websocket: WebSocket) -> None:
    try:
        await websocket.close(code=4001)
    except Exception:
        pass


async def _dual_watcher_side_behavior(
    *, tree_id: str, websocket: WebSocket, expires_at: int, session_id: str
) -> None:
    max_inactivity_seconds = int(os.environ.get("HERMES_TOKEN_MAX_INACTIVITY_SECONDS", "600"))
    while True:
        await asyncio.sleep(0.5)
        if is_revoked(tree_id):
            await _close_websocket_safely(websocket)
            return
        now = int(time.time())
        if now > expires_at:
            revoke_tree(tree_id, reason="token expired (watcher-side behavior)")
            await _close_websocket_safely(websocket)
            return
        meta = sessions.get(session_id)
        last_activity = int(meta.get("last_activity_ts", now)) if meta else now
        if now - last_activity > max_inactivity_seconds:
            revoke_tree(tree_id, reason="token revoked due to inactivity (watcher-side behavior)")
            await _close_websocket_safely(websocket)
            return


async def _dual_watcher_side_capability(*, tree_id: str, websocket: WebSocket, session_id: str) -> None:
    while True:
        await asyncio.sleep(0.5)
        if is_revoked(tree_id):
            await _close_websocket_safely(websocket)
            return
        meta = sessions.get(session_id)
        if not meta:
            return
        token = meta.get("lifecycle_token")
        ok, _ = validate_token(token)
        if not ok:
            revoke_tree(tree_id, reason="token invalid (watcher-side capability)")
            await _close_websocket_safely(websocket)
            return


def create_app() -> FastAPI:
    ensure_bootstrapped()
    origins = [o for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
    app = FastAPI(title="Hermes Orchestrator", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.on_event("startup")
    async def _startup() -> None:
        asyncio.create_task(daily_rebuild_loop())

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "gateway": "hermes-orchestrator",
            "agent": "claw-opus",
            "merkle_root": current_root(),
            "active_connections": len(active_connections),
        }

    @app.get("/info")
    async def info() -> dict[str, Any]:
        return {
            "gateway": "hermes-orchestrator",
            "agent": "claw-opus",
            "merkle_root": current_root(),
            "hermes_home": str(HERMES_HOME),
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
                    "agent": "claw-opus",
                    "role": "parent",
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
            for sid, meta in list(sessions.items()):
                if meta.get("websocket") is websocket:
                    watchers = meta.get("watchers") or {}
                    for task in watchers.values():
                        try:
                            task.cancel()
                        except Exception:
                            pass
                    await after_use(sid)
                    sessions.pop(sid, None)

    frontend = Path(os.environ.get("FRONTEND_DIR", str(Path(__file__).resolve().parents[2] / "frontend")))
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend), html=True), name="ui")

    return app


async def handle_rpc(msg: dict[str, Any], websocket: WebSocket) -> dict[str, Any] | None:
    method = msg.get("method")
    params = msg.get("params") or {}
    req_id = msg.get("id")

    if method == "session.create":
        sid = str(uuid.uuid4())
        agent_id = str(uuid.uuid4())
        ttl_seconds = int(os.environ.get("HERMES_TOKEN_TTL_SECONDS", "120"))
        token = issue_token(
            tree_id=sid,
            agent_id=agent_id,
            capabilities=PARENT_CAPABILITIES,
            ttl_seconds=ttl_seconds,
            merkle_root=current_root(),
            parent_id=None,
            role="parent",
        )
        register_token(token)

        sessions[sid] = {
            "session_key": params.get("session_key", sid),
            "running": False,
            "agent": "claw-opus",
            "lifecycle_token": token,
            "agent_id": agent_id,
            "tree_id": sid,
            "created_at_ts": int(time.time()),
            "last_activity_ts": int(time.time()),
            "websocket": websocket,
        }
        expires_at = int(token.get("expires_at", 0))
        sessions[sid]["watchers"] = {
            "behavior": asyncio.create_task(
                _dual_watcher_side_behavior(
                    tree_id=sid, websocket=websocket, expires_at=expires_at, session_id=sid
                )
            ),
            "capability": asyncio.create_task(
                _dual_watcher_side_capability(tree_id=sid, websocket=websocket, session_id=sid)
            ),
        }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "session_id": sid,
                "status": "ready",
                "agent": "claw-opus",
                "lifecycle_token": token,
                "merkle_root": current_root(),
            },
        }

    if method == "message.send":
        sid = params.get("session_id", "")
        text = params.get("text", "")
        if sid not in sessions:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": "unknown session"},
            }
        sessions[sid]["last_activity_ts"] = int(time.time())
        sessions[sid]["running"] = True
        lifecycle_token = params.get("lifecycle_token") or sessions[sid].get("lifecycle_token")
        payload = {"session_id": sid, "text": text, "merkle_root": current_root()}
        verdict, reason = gate_and_ledger_block_if_needed(
            payload=payload,
            token=lifecycle_token,
            action="ws:message.send",
            agent_name=str(sessions[sid].get("agent_id", "")),
            session_id=sid,
        )
        if verdict != "PASS":
            revoke_tree(str(sessions[sid].get("tree_id", sid)), reason=reason)
            sessions[sid]["running"] = False
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": "BLOCKED by supervisor", "reason": reason},
            }

        await websocket.send_text(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "event",
                    "params": {"type": "message.start", "payload": {"session_id": sid, "agent": "claw-opus"}},
                }
            )
        )
        try:
            reply = claw_chat(
                text=text,
                session_id=sid,
                merkle_root=current_root(),
                token=lifecycle_token if isinstance(lifecycle_token, dict) else sessions[sid]["lifecycle_token"],
            )
        except ClawUnavailable as exc:
            await websocket.send_text(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "event",
                        "params": {
                            "type": "error",
                            "payload": {"text": f"Claw Opus unavailable: {exc}"},
                        },
                    }
                )
            )
            reply = ""
        if reply:
            await websocket.send_text(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "event",
                        "params": {"type": "message.delta", "payload": {"text": reply}},
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
        await after_use(sid)
        return {"jsonrpc": "2.0", "id": req_id, "result": {"status": "complete", "agent": "claw-opus"}}

    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }
    return None
