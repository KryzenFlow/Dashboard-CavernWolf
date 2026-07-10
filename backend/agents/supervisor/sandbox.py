"""Sandbox test runner — validate supervisor rules without side effects.

Run standalone:  python -m agents.supervisor.sandbox
Or via pytest:   pytest backend/tests/test_supervisor.py
"""

from __future__ import annotations

import logging
from typing import Any

from agents.supervisor.rules import Decision, Supervisor, SupervisorRules

_log = logging.getLogger(__name__)


def _sandbox_execute(task: dict[str, Any]) -> str:
    _log.debug("[SANDBOX] Simulating task: %s", task.get("type", task.get("job_type")))
    return "completed"


def sandbox_run(
    agent_id: str,
    tasks: list[dict[str, Any]],
    rules: SupervisorRules | None = None,
) -> list[dict[str, Any]]:
    """Run a list of mock tasks through the supervisor in sandbox mode.

    Returns a list of result dicts with task, decision, and outcome.
    """
    if rules is None:
        rules = SupervisorRules(sandbox_mode=True)
    else:
        rules.sandbox_mode = True

    supervisor = Supervisor(rules=rules)
    results: list[dict[str, Any]] = []

    supervisor.fire("on_agent_start", agent_id=agent_id)

    for task in tasks:
        supervisor.fire("on_task_assigned", agent_id=agent_id, task=task)
        decision: Decision = supervisor.enforce(task)

        if decision.approved:
            outcome = _sandbox_execute(task)
            supervisor.record_outcome(agent_id, True)
            supervisor.fire(
                "on_task_completed",
                agent_id=agent_id,
                task=task,
                status=outcome,
            )
            results.append({
                "task": task.get("type", task.get("job_type")),
                "approved": True,
                "outcome": outcome,
            })
        else:
            supervisor.record_outcome(agent_id, False)
            supervisor.fire(
                "on_task_rejected",
                agent_id=agent_id,
                task=task,
                reason=decision.reason,
            )
            results.append({
                "task": task.get("type", task.get("job_type")),
                "approved": False,
                "reason": decision.reason,
            })

    supervisor.fire("on_agent_shutdown", agent_id=agent_id)
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    mock_tasks = [
        {"type": "seo_scan", "payload": {"zip": "49221"}},
        {"type": "blog_draft", "payload": {"topic": "local clinic SEO tips"}},
        {"type": "delete_system32", "payload": {}},
        {"type": "reason", "payload": {"query": "plan next bleed vertical"}},
        {"type": "build_site", "payload": {"template": "static-site"}, "estimated_tokens": 999},
    ]

    results = sandbox_run("sandbox_agent_1", mock_tasks)

    print("\n=== Sandbox Results ===")
    for r in results:
        icon = "PASS" if r["approved"] else "BLOCKED"
        detail = r.get("outcome", r.get("reason", ""))
        print(f"  [{icon}] {r['task']} — {detail}")
