"""Supervisor rules engine — enforce safety, token limits, and forbidden actions.

Inspired by LangChain Supervisor pattern. Validates every task before execution
and fires lifecycle hooks to Dashboard and CavernWolf endpoints.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable

_log = logging.getLogger(__name__)

HookFn = Callable[..., None]


@dataclass
class Decision:
    approved: bool
    reason: str = ""


@dataclass
class SupervisorRules:
    max_tokens_per_step: int = 300
    forbidden_actions: list[str] = field(default_factory=lambda: [
        "delete_system32",
        "shutdown_server",
        "format_disk",
        "rm_rf_root",
    ])
    max_consecutive_failures: int = 5
    sandbox_mode: bool = False

    def enforce(self, task: dict[str, Any]) -> Decision:
        task_type = task.get("type", task.get("job_type", ""))
        payload = task.get("payload", task.get("map_data", {}))

        if task_type in self.forbidden_actions:
            return Decision(approved=False, reason=f"Forbidden action: {task_type}")

        if isinstance(payload, dict):
            payload_str = str(payload)
            for forbidden in self.forbidden_actions:
                if forbidden in payload_str:
                    return Decision(
                        approved=False,
                        reason=f"Payload contains forbidden term: {forbidden}",
                    )

        tokens = task.get("estimated_tokens", 0)
        if tokens > self.max_tokens_per_step:
            return Decision(
                approved=False,
                reason=f"Token estimate {tokens} exceeds limit {self.max_tokens_per_step}",
            )

        if self.sandbox_mode:
            _log.debug("[SANDBOX] Task %s approved (sandbox — no side effects)", task_type)

        return Decision(approved=True)


class Supervisor:
    """Hook-aware supervisor that wraps rules enforcement with lifecycle callbacks."""

    def __init__(self, rules: SupervisorRules | None = None) -> None:
        self.rules = rules or SupervisorRules()
        self._hooks: dict[str, list[HookFn]] = {}
        self._failure_counts: dict[str, int] = {}

    def register_hook(self, event: str, fn: HookFn) -> None:
        self._hooks.setdefault(event, []).append(fn)

    def fire(self, event: str, **kwargs: Any) -> None:
        for fn in self._hooks.get(event, []):
            try:
                fn(**kwargs)
            except Exception as exc:
                _log.warning("Hook %s/%s failed: %s", event, fn.__name__, exc)

    def enforce(self, task: dict[str, Any]) -> Decision:
        return self.rules.enforce(task)

    def record_outcome(self, agent_id: str, success: bool) -> None:
        if success:
            self._failure_counts[agent_id] = 0
        else:
            count = self._failure_counts.get(agent_id, 0) + 1
            self._failure_counts[agent_id] = count
            if count >= self.rules.max_consecutive_failures:
                _log.error(
                    "Agent %s hit %d consecutive failures — pausing",
                    agent_id, count,
                )

    def should_pause(self, agent_id: str) -> bool:
        return (
            self._failure_counts.get(agent_id, 0)
            >= self.rules.max_consecutive_failures
        )


def build_supervisor() -> Supervisor:
    sandbox = os.getenv("SUPERVISOR_SANDBOX", "0") == "1"
    max_tokens = int(os.getenv("SUPERVISOR_MAX_TOKENS", "300"))
    max_failures = int(os.getenv("SUPERVISOR_MAX_FAILURES", "5"))
    rules = SupervisorRules(
        max_tokens_per_step=max_tokens,
        sandbox_mode=sandbox,
        max_consecutive_failures=max_failures,
    )
    return Supervisor(rules=rules)
