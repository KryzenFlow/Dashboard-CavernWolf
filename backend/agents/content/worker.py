"""Process claimed research jobs into blog drafts (agent worker)."""

from __future__ import annotations

import json
from typing import Any

from agents.content.generate import generate_blog_draft
from agents.research.db import complete_job


def process_claimed_job(job: dict[str, Any]) -> dict[str, Any]:
    """Turn a claimed job into findings; used by agent worker on your other PC."""
    job_type = job.get("job_type", "seo_scan")
    bleed_id = job["bleed_id"]
    job_id = job["id"]

    try:
        if job_type == "blog_draft":
            payload = json.loads(job["map_data"]) if job.get("map_data") else {}
            topic = payload.get("topic") or payload.get("title") or "local business tips"
            project = payload.get("project", "site")
            result = generate_blog_draft(topic, bleed_id, project, job_id=job_id)
            complete_job(job_id, result)
            return {"status": "done", "result": result}

        return {"status": "skipped", "reason": f"No processor for job_type={job_type}"}
    except Exception as exc:
        complete_job(job_id, None, error=str(exc))
        return {"status": "failed", "error": str(exc)}
