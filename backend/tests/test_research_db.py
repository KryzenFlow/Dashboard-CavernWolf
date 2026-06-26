"""Research job queue tests."""

import os

os.environ["RESEARCH_DB_URL"] = "sqlite:///:memory:"

from agents.research.db import claim_next_job, complete_job, enqueue_job, init_research_db, list_jobs


def test_job_queue_flow():
    init_research_db()
    job_id = enqueue_job("doctors", "90210", [1, 2, 3])
    claimed = claim_next_job()
    assert claimed["id"] == job_id
    assert claimed["status"] == "pending"
    complete_job(job_id, {"summary": "test findings"})
    jobs = list_jobs(status="done")
    assert any(j["id"] == job_id for j in jobs)
