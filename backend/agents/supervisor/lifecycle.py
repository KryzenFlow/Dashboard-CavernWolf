"""Agent lifecycle hooks — start, task_assigned, task_completed, shutdown.

These fire HTTP notifications to Dashboard and CavernWolf endpoints
when running in a real environment. In sandbox mode they only log.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

from agents.supervisor.rules import Supervisor

_log = logging.getLogger(__name__)

DASHBOARD_URL = os.getenv("DASHBOARD_LIFECYCLE_URL", "http://backend:8000")
CAVERNWOLF_URL = os.getenv("CAVERNWOLF_STATE_URL", "http://backend:8000")


def _post(url: str, data: dict[str, Any]) -> None:
    try:
        requests.post(url, json=data, timeout=5)
    except Exception as exc:
        _log.warning("Lifecycle POST to %s failed: %s", url, exc)


def on_agent_start(agent_id: str, **_: Any) -> None:
    _log.info("Agent %s started", agent_id)
    _post(f"{CAVERNWOLF_URL}/ops/lifecycle", {
        "agent_id": agent_id,
        "event": "started",
    })


def on_task_assigned(agent_id: str, task: dict[str, Any] | None = None, **_: Any) -> None:
    task_type = (task or {}).get("type", (task or {}).get("job_type", "unknown"))
    _log.info("Agent %s assigned task: %s", agent_id, task_type)
    _post(f"{DASHBOARD_URL}/ops/lifecycle", {
        "agent_id": agent_id,
        "event": "task_assigned",
        "task_type": task_type,
    })


def on_task_completed(
    agent_id: str,
    task: dict[str, Any] | None = None,
    status: str = "completed",
    **_: Any,
) -> None:
    task_type = (task or {}).get("type", (task or {}).get("job_type", "unknown"))
    _log.info("Agent %s task %s -> %s", agent_id, task_type, status)
    _post(f"{CAVERNWOLF_URL}/ops/lifecycle", {
        "agent_id": agent_id,
        "event": "task_completed",
        "task_type": task_type,
        "status": status,
    })


def on_agent_shutdown(agent_id: str, **_: Any) -> None:
    _log.info("Agent %s shutting down", agent_id)
    _post(f"{DASHBOARD_URL}/ops/lifecycle", {
        "agent_id": agent_id,
        "event": "shutdown",
    })


def on_task_rejected(
    agent_id: str,
    task: dict[str, Any] | None = None,
    reason: str = "",
    **_: Any,
) -> None:
    task_type = (task or {}).get("type", (task or {}).get("job_type", "unknown"))
    _log.warning("Agent %s REJECTED task %s: %s", agent_id, task_type, reason)
    _post(f"{DASHBOARD_URL}/ops/lifecycle", {
        "agent_id": agent_id,
        "event": "task_rejected",
        "task_type": task_type,
        "reason": reason,
    })


def register_all_hooks(supervisor: Supervisor) -> None:
    supervisor.register_hook("on_agent_start", on_agent_start)
    supervisor.register_hook("on_task_assigned", on_task_assigned)
    supervisor.register_hook("on_task_completed", on_task_completed)
    supervisor.register_hook("on_task_rejected", on_task_rejected)
    supervisor.register_hook("on_agent_shutdown", on_agent_shutdown)
