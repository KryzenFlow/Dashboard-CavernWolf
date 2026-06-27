"""Process claimed research jobs — delegates to unified processor."""

from __future__ import annotations

from typing import Any

from agents.worker.processor import process_job


def process_claimed_job(job: dict[str, Any], agent_id: str = "content-writer") -> dict[str, Any]:
    return process_job(job, agent_id)
