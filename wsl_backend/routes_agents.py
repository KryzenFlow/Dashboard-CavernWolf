"""REST API for dynamic agent roster + system status + plugins."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from wsl_backend.agents.registry import REGISTRY
from wsl_backend.memory.redis_store import RedisMemory
from wsl_backend.memory.vector_store import VectorMemory
from wsl_backend.tailscale_net import detect_tailscale_ipv4
from wsl_backend.tools.plugins import list_plugins

router = APIRouter(prefix="/agents", tags=["agents"])
status_router = APIRouter(tags=["status"])


class CreateAgentBody(BaseModel):
    role: str
    name: str | None = None
    id: str | None = None
    model: str | None = None
    description: str | None = None
    tools: list[str] = Field(default_factory=list)
    plugins: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class RouteBody(BaseModel):
    task: str | None = None
    message: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


@router.get("")
def list_agents() -> dict[str, Any]:
    return {"agents": REGISTRY.list_public(), "roles": REGISTRY.roles()}


@router.get("/roles")
def list_roles() -> dict[str, Any]:
    return {"roles": REGISTRY.roles()}


@router.post("")
def create_agent(body: CreateAgentBody) -> dict[str, Any]:
    try:
        agent = REGISTRY.create(
            body.role,
            name=body.name,
            tools=body.tools or None,
            plugins=body.plugins or None,
            agent_id=(body.id or "").strip() or None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if body.model:
        agent["model"] = body.model
    if body.description:
        agent["description"] = body.description
    return {"agent": agent}


@router.delete("/{agent_id}")
def delete_agent(agent_id: str) -> dict[str, Any]:
    try:
        ok = REGISTRY.delete(agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(status_code=404, detail="agent not found")
    return {"deleted": True, "id": agent_id}


@router.post("/{agent_id}/route")
def route_agent(agent_id: str, body: RouteBody) -> dict[str, Any]:
    task = (body.task or body.message or "").strip()
    if not task:
        raise HTTPException(status_code=400, detail="task or message required")
    result = REGISTRY.route(agent_id, task, body.context)
    public = result.public()
    return {"agent_id": agent_id, "result": public, "plan": public}


def _docker_ps() -> tuple[list[str], bool]:
    docker = shutil.which("docker")
    if not docker:
        return [], False
    try:
        completed = subprocess.run(
            [docker, "ps", "--format", "{{.Names}}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return [], False
    if completed.returncode != 0:
        return [], False
    names = [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]
    return names, True


def _claw_listening(containers: list[str], docker_ok: bool) -> bool:
    names = {c.lower() for c in containers}
    if "claw-opus" in names:
        return True
    if docker_ok:
        return False
    try:
        from web_gateway.security.control_plane import is_halted

        return not is_halted()
    except Exception:
        return False


@status_router.get("/system/status")
def system_status() -> dict[str, Any]:
    agents = REGISTRY.list_public()
    containers, docker_ok = _docker_ps()
    redis = RedisMemory().status()
    vector = VectorMemory().status()
    merkle_root = None
    halted = None
    try:
        from web_gateway.security.control_plane import current_root, is_halted

        merkle_root = current_root()
        halted = is_halted()
    except Exception:
        pass
    listening = False if halted is True else _claw_listening(containers, docker_ok)
    return {
        "agents": [
            {"id": a["id"], "name": a["name"], "role": a["role"], "status": a["status"]}
            for a in agents
        ],
        "agents_count": len(agents),
        "ports": {
            "hermes": int(os.environ.get("PORT", "8000")),
            "claw": 9000,
            "studio_vite": 1420,
        },
        "containers": containers,
        "tailscale_ip": detect_tailscale_ipv4(),
        "bind": "tailscale" if os.environ.get("HERMES_BIND_TAILSCALE", "1") == "1" else "local",
        "claw_url": os.environ.get("CLAW_URL", ""),
        "claw": {"listening": listening, "halted": halted},
        "hermes": {"ready": True},
        "memory": {
            "redis": bool(redis.get("ok")),
            "vector": bool(vector.get("ok")),
            "redis_detail": redis,
            "vector_detail": vector,
        },
        "security": {"merkle_root": merkle_root},
        "merkle_root": merkle_root,
    }


@status_router.get("/plugins")
def plugins() -> dict[str, Any]:
    return {"plugins": list_plugins()}
