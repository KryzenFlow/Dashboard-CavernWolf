"""Agent REST routes: /reason, /action, /memory, /agents/* (internal Studio only)."""

from __future__ import annotations

import os
from typing import Any

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.memory.db import get_memory_rows, init_db, save_memory
from agents.orchestration.pipeline import run_pipeline
from agents.reasoning.engine import llama_index_available, query_llama
from web_gateway.hermes_bridge import bridge_status, execute_claw
from web_gateway.studio_security import assert_internal_access, is_public_studio

router = APIRouter()


class ReasonRequest(BaseModel):
    query: str
    session_id: str = "web-1"


class ActionRequest(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


def _require_internal() -> None:
    err = assert_internal_access()
    if err:
        raise HTTPException(
            status_code=403,
            detail={
                "error": err,
                "hint": "Use POST /studio/cli/run or Projects Quick Actions in public Studio.",
            },
        )


def register_agent_routes(app) -> None:
    init_db()
    app.include_router(router)


@router.get("/")
def root_status() -> dict[str, Any]:
    return {
        "status": "Backend running",
        "service": "Hermes Multi-Agent Backend",
        "llama_index": llama_index_available(),
        "agent_stack": os.getenv("AGENT_STACK_ENABLED", "0") == "1",
        "studio_mode": os.getenv("STUDIO_MODE", "public"),
    }


@router.post("/reason")
def reason(req: ReasonRequest) -> dict[str, Any]:
    if is_public_studio():
        return {
            "answer": (
                "Public Hermes Studio does not expose the full reasoning stack. "
                "Use Projects → Quick Actions, or POST /studio/cli/run with whitelisted commands "
                "(new site, deploy github|docker|static, ai suggest-template|generate-content)."
            ),
        }
    use_ai = os.getenv("AGENT_STACK_USE_AI", "0") == "1"
    if use_ai and os.getenv("AGENT_STACK_ENABLED", "0") == "1":
        result = run_pipeline(req.query, req.session_id)
        return {"answer": result["decision"], "actions": result.get("actions", [])}
    answer = query_llama(req.query)
    save_memory(f"Q: {req.query} | A: {answer}")
    return {"answer": answer}


@router.post("/action")
def trigger_action(req: ActionRequest) -> dict[str, Any]:
    _require_internal()
    result = execute_claw(req.action, req.params)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result)
    return result


@router.get("/memory")
def get_memory() -> list[dict[str, Any]]:
    _require_internal()
    return get_memory_rows()


@router.get("/agents/health")
def agents_health() -> dict[str, Any]:
    bridge = bridge_status()
    claw_ok = False
    try:
        r = requests.get(f"{os.getenv('CLAW_URL', 'http://agent-claw:9000')}/health", timeout=5)
        claw_ok = r.status_code == 200
    except Exception:
        pass
    payload = {
        "backend": "ok",
        "claw": claw_ok,
        "llama_index": llama_index_available(),
        "bridge": bridge,
    }
    if is_public_studio():
        payload["memory_rows"] = None
        payload["note"] = "Agent health summary only in public mode."
        return payload
    payload["memory_rows"] = len(get_memory_rows(5))
    return payload


@router.post("/agents/task")
def agents_task(req: ReasonRequest) -> dict[str, Any]:
    """Full AI pipeline — internal Studio + AGENT_STACK_USE_AI=1."""
    _require_internal()
    if os.getenv("AGENT_STACK_USE_AI", "0") != "1":
        return {
            "error": "AI task pipeline disabled. Set AGENT_STACK_USE_AI=1 or use /studio/deploy (no AI).",
            "hint": "Use POST /studio/new-website and POST /studio/deploy for click-to-deploy without tokens.",
        }
    result = run_pipeline(req.query, req.session_id)
    claw_result = None
    for action in result.get("actions", []):
        if action.get("type") == "reply":
            continue
        act = action.get("type", "")
        claw_result = execute_claw(act, action.get("params", {}))
    return {**result, "claw_result": claw_result}


@router.post("/agents/rebuild")
def agents_rebuild() -> dict[str, Any]:
    _require_internal()
    return trigger_action(ActionRequest(action="rebuild_hermes", params={}))
