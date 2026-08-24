"""Concrete agent matrix. No mock LLM replies; plans route through Hermes → Claw."""

from __future__ import annotations

import os
from typing import Any, Never

from wsl_backend.agents.base import AgentResult, AgentRole, BaseAgent


class HermesAgent(BaseAgent):
    role = AgentRole.HERMES
    default_name = "Hermes"
    default_style = "supervisor"
    default_tools = ["rest_cli", "bash_list_args", "route"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            ok=True,
            kind="route_plan",
            payload={
                "supervisor": self.spec.name,
                "task": task,
                "next": "select_specialist_or_claw",
                "context_keys": sorted((context or {}).keys()),
            },
            route_to_claw=False,
        )


class ReasoningAnalyticalAgent(BaseAgent):
    role = AgentRole.REASONING_ANALYTICAL
    default_name = "Reasoning Analytical"
    default_style = "analytical"
    default_tools = ["decompose", "risk_notes"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            ok=True,
            kind="analysis_plan",
            payload={
                "style": self.spec.style,
                "task": task,
                "steps": [
                    "restate goal",
                    "list constraints (Merkle, Tailscale, no false env)",
                    "propose Claw execution checklist",
                ],
            },
            route_to_claw=False,
        )


class ReasoningRapidAgent(BaseAgent):
    role = AgentRole.REASONING_RAPID
    default_name = "Reasoning Rapid"
    default_style = "rapid_prototype"
    default_tools = ["sketch", "prioritize"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            ok=True,
            kind="prototype_plan",
            payload={
                "style": self.spec.style,
                "task": task,
                "mvp": ["smallest verifiable change", "gate check", "Claw cycle"],
            },
            route_to_claw=False,
        )


class MemoryEphemeralAgent(BaseAgent):
    role = AgentRole.MEMORY_EPHEMERAL
    default_name = "Memory Ephemeral"
    default_style = "redis_state"
    default_tools = ["get", "set", "ttl"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        # Backend URL from env when configured — never invent Redis data.
        redis_url = os.environ.get("REDIS_URL", "").strip()
        return AgentResult(
            ok=bool(redis_url),
            kind="memory_ephemeral",
            payload={
                "backend": "redis" if redis_url else "unconfigured",
                "task": task,
                "note": "configure REDIS_URL for ephemeral state; cycle wipe still applies",
            },
            route_to_claw=False,
            error=None if redis_url else "REDIS_URL not configured",
        )


class MemorySemanticAgent(BaseAgent):
    role = AgentRole.MEMORY_SEMANTIC
    default_name = "Memory Semantic"
    default_style = "vector_ltm"
    default_tools = ["embed_query", "upsert", "search"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        vector_url = os.environ.get("VECTOR_DB_URL", "").strip()
        return AgentResult(
            ok=bool(vector_url),
            kind="memory_semantic",
            payload={
                "backend": "vector" if vector_url else "unconfigured",
                "task": task,
                "note": "configure VECTOR_DB_URL for semantic memory",
            },
            route_to_claw=False,
            error=None if vector_url else "VECTOR_DB_URL not configured",
        )


class CodexAgent(BaseAgent):
    role = AgentRole.CODEX
    default_name = "Codex"
    default_style = "coding_tools"
    default_tools = ["read_skill", "propose_patch", "syntax_check"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            ok=True,
            kind="code_plan",
            payload={
                "task": task,
                "propose": ["locate skill/path", "draft patch", "POST /skill/test via Hermes"],
                "execute_via": "claw_opus",
            },
            route_to_claw=True,
        )


class GrokAgent(BaseAgent):
    role = AgentRole.GROK
    default_name = "Grok"
    default_style = "research_extract"
    default_tools = ["extract", "summarize_sources"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            ok=True,
            kind="research_plan",
            payload={
                "task": task,
                "propose": ["list sources", "extract facts", "hand plan to Hermes → Claw"],
                "execute_via": "claw_opus",
            },
            route_to_claw=True,
        )


class DeepSeekArchitectAgent(BaseAgent):
    role = AgentRole.DEEPSEEK_ARCHITECT
    default_name = "DeepSeek Architect"
    default_style = "flash4_architect"
    default_tools = ["review_arch", "fail_report", "sec_hardening"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        return AgentResult(
            ok=True,
            kind="architecture_review",
            payload={
                "task": task,
                "checks": [
                    "Bitwarden — no secrets in telemetry",
                    "Doberman — redacted logs",
                    "subprocess — no shell=True",
                    "Tailscale — no public FastAPI ports",
                    "Merkle — Claw halt on control failure",
                ],
                "verdict": "report_only",
            },
            route_to_claw=False,
        )


class ClawOpusAgent(BaseAgent):
    role = AgentRole.CLAW_OPUS
    default_name = "Claw Opus"
    default_style = "executor"
    default_tools = ["openclaw_chat", "halt_after_use"]

    def handle(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        # Execution is performed by Hermes → claw_client, not inline here.
        return AgentResult(
            ok=True,
            kind="execute",
            payload={
                "task": task,
                "requires": ["live_merkle_root", "OPENCLAW_GATEWAY_URL", "parent_token"],
                "note": "Hermes must call claw_client.claw_chat; this agent does not invent text",
            },
            route_to_claw=True,
        )


def agent_class_for(role: AgentRole) -> type[BaseAgent]:
    """Map every AgentRole to a class. New enum members fail here until handled."""
    match role:
        case AgentRole.HERMES:
            return HermesAgent
        case AgentRole.REASONING_ANALYTICAL:
            return ReasoningAnalyticalAgent
        case AgentRole.REASONING_RAPID:
            return ReasoningRapidAgent
        case AgentRole.MEMORY_EPHEMERAL:
            return MemoryEphemeralAgent
        case AgentRole.MEMORY_SEMANTIC:
            return MemorySemanticAgent
        case AgentRole.CODEX:
            return CodexAgent
        case AgentRole.GROK:
            return GrokAgent
        case AgentRole.DEEPSEEK_ARCHITECT:
            return DeepSeekArchitectAgent
        case AgentRole.CLAW_OPUS:
            return ClawOpusAgent
        case _:
            unused: Never = role
            raise RuntimeError(f"unhandled agent role: {unused}")


ROLE_FACTORIES: dict[AgentRole, type[BaseAgent]] = {
    role: agent_class_for(role) for role in AgentRole
}


def create_agent(
    role: AgentRole,
    *,
    name: str | None = None,
    tools: list[str] | None = None,
    plugins: list[str] | None = None,
    agent_id: str | None = None,
    stable_id: bool = False,
) -> BaseAgent:
    cls = agent_class_for(role)
    return cls(name=name, tools=tools, plugins=plugins, agent_id=agent_id, stable_id=stable_id)
