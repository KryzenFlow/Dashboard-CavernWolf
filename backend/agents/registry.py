"""Load Agent Hub registry (8 agents) from YAML."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_REGISTRY_PATH = os.getenv(
    "AGENT_REGISTRY_PATH",
    "/shared/agents/registry.yaml",
)
_REPO_REGISTRY = Path(__file__).resolve().parents[2] / "shared" / "agents" / "registry.yaml"


def _registry_file() -> Path:
    p = Path(_REGISTRY_PATH)
    if p.is_file():
        return p
    if _REPO_REGISTRY.is_file():
        return _REPO_REGISTRY
    return p


def load_registry() -> dict[str, Any]:
    path = _registry_file()
    if not path.is_file():
        return {"agents": {}, "workspace": {}}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_agents(auto_run_only: bool = False) -> list[dict[str, Any]]:
    cfg = load_registry()
    out = []
    for aid, meta in cfg.get("agents", {}).items():
        if auto_run_only and not meta.get("auto_run", False):
            continue
        out.append({
            "id": aid,
            "label": meta.get("label", aid),
            "type": meta.get("type", "generic"),
            "model": meta.get("model", ""),
            "auto_run": bool(meta.get("auto_run", False)),
            "job_types": list(meta.get("job_types", [])),
            "status": "running" if meta.get("auto_run") else "stopped",
        })
    return out


def get_agent(agent_id: str) -> dict[str, Any] | None:
    cfg = load_registry()
    meta = cfg.get("agents", {}).get(agent_id)
    if not meta:
        return None
    return {"id": agent_id, **meta}


def agents_for_job_type(job_type: str) -> list[str]:
    return [a["id"] for a in list_agents() if job_type in a.get("job_types", [])]
