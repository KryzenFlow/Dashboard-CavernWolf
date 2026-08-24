"""Agent matrix base types. Claw Opus is the only execution worker."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class AgentRole(str, Enum):
    HERMES = "hermes"
    REASONING_ANALYTICAL = "reasoning_analytical"
    REASONING_RAPID = "reasoning_rapid"
    MEMORY_EPHEMERAL = "memory_ephemeral"
    MEMORY_SEMANTIC = "memory_semantic"
    CODEX = "codex"
    GROK = "grok"
    DEEPSEEK_ARCHITECT = "deepseek_architect"
    CLAW_OPUS = "claw_opus"


@dataclass
class AgentSpec:
    id: str
    role: AgentRole
    name: str
    style: str
    tools: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    status: str = "idle"

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "name": self.name,
            "style": self.style,
            "model": self.style,
            "tools": list(self.tools),
            "plugins": list(self.plugins),
            "status": self.status,
            "description": f"{self.name} ({self.role.value})",
            "executes": self.role == AgentRole.CLAW_OPUS,
        }


@dataclass
class AgentResult:
    ok: bool
    kind: str
    payload: dict[str, Any]
    route_to_claw: bool = False
    error: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "kind": self.kind,
            "payload": self.payload,
            "route_to_claw": self.route_to_claw,
            "error": self.error,
        }


STABLE_ROLE_IDS: dict[AgentRole, str] = {
    AgentRole.HERMES: "hermes",
    AgentRole.REASONING_ANALYTICAL: "reasoning-analytical",
    AgentRole.REASONING_RAPID: "reasoning-rapid",
    AgentRole.MEMORY_EPHEMERAL: "memory-ephemeral",
    AgentRole.MEMORY_SEMANTIC: "memory-semantic",
    AgentRole.CODEX: "codex",
    AgentRole.GROK: "grok",
    AgentRole.DEEPSEEK_ARCHITECT: "deepseek-architect",
    AgentRole.CLAW_OPUS: "claw-opus",
}


class BaseAgent(ABC):
    """Specialists propose; only Claw Opus executes against OpenClaw."""

    role: AgentRole
    default_name: str
    default_style: str
    default_tools: list[str] = []

    def __init__(
        self,
        *,
        name: str | None = None,
        tools: list[str] | None = None,
        plugins: list[str] | None = None,
        agent_id: str | None = None,
        stable_id: bool = False,
    ) -> None:
        if agent_id:
            resolved_id = agent_id
        elif stable_id:
            resolved_id = STABLE_ROLE_IDS[self.role]
        else:
            resolved_id = str(uuid4())
        self.spec = AgentSpec(
            id=resolved_id,
            role=self.role,
            name=name or self.default_name,
            style=self.default_style,
            tools=list(tools if tools is not None else self.default_tools),
            plugins=list(plugins or []),
        )

    @abstractmethod
    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        raise NotImplementedError

    def public(self) -> dict[str, Any]:
        return self.spec.public()
