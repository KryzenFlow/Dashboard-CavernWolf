"""Docker agent pool — 8 agents polling jobs and writing files."""

from __future__ import annotations

import logging
import os
import threading
import time

from agents.registry import get_agent, list_agents
from agents.research.db import claim_next_job, init_research_db
from agents.worker.processor import process_job

_log = logging.getLogger(__name__)


def run_agent_loop(agent_id: str) -> None:
    agent = get_agent(agent_id)
    if not agent:
        _log.error("Unknown agent: %s", agent_id)
        return
    job_types = agent.get("job_types", [])
    poll = int(os.getenv("AGENT_POLL_SECONDS", "15"))
    _log.info("Agent %s started (types: %s)", agent_id, job_types)

    while True:
        job = claim_next_job(agent_id=agent_id, job_types=job_types)
        if job:
            outcome = process_job(job, agent_id)
            _log.info("Agent %s job #%s %s -> %s", agent_id, job["id"], job.get("job_type"), outcome.get("status"))
        else:
            time.sleep(poll)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    init_research_db()

    single = os.getenv("AGENT_ID", "").strip()
    if single:
        run_agent_loop(single)
        return

    agents = [a for a in list_agents(auto_run_only=True)]
    if not agents:
        _log.warning("No auto_run agents in registry")
        return

    _log.info("Starting %d agents in pool", len(agents))
    for meta in agents:
        t = threading.Thread(target=run_agent_loop, args=(meta["id"],), daemon=True, name=meta["id"])
        t.start()

    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
