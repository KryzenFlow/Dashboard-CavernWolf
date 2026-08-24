"""Dynamic agent roster — create/list/delete/route. Not a hardcoded monolith."""

from __future__ import annotations

from threading import Lock
from typing import Any

from wsl_backend.agents.base import AgentResult, AgentRole, BaseAgent
from wsl_backend.agents.matrix import ROLE_FACTORIES, create_agent


class AgentRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._agents: dict[str, BaseAgent] = {}
        self.seed_defaults()

    def seed_defaults(self) -> None:
        with self._lock:
            if self._agents:
                return
            for role in AgentRole:
                agent = create_agent(role, stable_id=True)
                self._agents[agent.spec.id] = agent

    def list_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [a.public() for a in self._agents.values()]

    def roles(self) -> list[str]:
        return [r.value for r in AgentRole]

    def get(self, agent_id: str) -> BaseAgent | None:
        with self._lock:
            return self._agents.get(agent_id)

    def create(
        self,
        role: str,
        *,
        name: str | None = None,
        tools: list[str] | None = None,
        plugins: list[str] | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            role_enum = AgentRole(role)
        except ValueError as exc:
            raise KeyError(f"unknown role: {role}") from exc
        if role_enum not in ROLE_FACTORIES:
            raise KeyError(f"unknown role: {role}")
        if role_enum == AgentRole.CLAW_OPUS:
            raise PermissionError("cannot create additional Claw Opus workers via Agent Builder")
        agent = create_agent(role_enum, name=name, tools=tools, plugins=plugins, agent_id=agent_id)
        with self._lock:
            if agent.spec.id in self._agents:
                raise KeyError(f"agent id already exists: {agent.spec.id}")
            self._agents[agent.spec.id] = agent
        return agent.public()

    def delete(self, agent_id: str) -> bool:
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return False
            # Keep at least one Hermes + one Claw Opus instance.
            if agent.spec.role == AgentRole.HERMES:
                hermes_count = sum(1 for a in self._agents.values() if a.spec.role == AgentRole.HERMES)
                if hermes_count <= 1:
                    raise PermissionError("cannot delete the last Hermes supervisor")
            if agent.spec.role == AgentRole.CLAW_OPUS:
                claw_count = sum(1 for a in self._agents.values() if a.spec.role == AgentRole.CLAW_OPUS)
                if claw_count <= 1:
                    raise PermissionError("cannot delete the last Claw Opus worker")
            del self._agents[agent_id]
            return True

    def route(self, agent_id: str, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        agent = self.get(agent_id)
        if not agent:
            return AgentResult(ok=False, kind="error", payload={}, error="agent not found")
        agent.spec.status = "busy"
        try:
            return agent.handle(task, context)
        finally:
            agent.spec.status = "idle"


REGISTRY = AgentRegistry()
