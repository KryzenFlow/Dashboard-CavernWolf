"""Route queued jobs to the right agent handlers (files, SEO, blogs, claw)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from agents.content.generate import generate_blog_draft
from agents.content.publish import publish_draft_to_disk
from agents.memory.db import save_memory
from agents.memory.ltm import ltm_ingest
from agents.memory.stm import stm_store
from agents.orchestration.pipeline import run_pipeline
from agents.research.db import complete_job
from agents.research.seo import build_seo_prompt
from agents.reasoning.engine import query_llama
from web_gateway.hermes_bridge import execute_claw, run_profile


def _payload(job: dict[str, Any]) -> dict[str, Any]:
    raw = job.get("map_data")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"text": str(raw)}


def process_job(job: dict[str, Any], agent_id: str) -> dict[str, Any]:
    job_type = job.get("job_type", "seo_scan")
    bleed_id = job["bleed_id"]
    job_id = job["id"]

    try:
        if job_type == "blog_draft":
            p = _payload(job)
            topic = p.get("topic") or p.get("title") or "local business tips"
            result = generate_blog_draft(topic, bleed_id, p.get("project", "site"), job_id=job_id)
            complete_job(job_id, {**result, "agent": agent_id})
            return {"status": "done", "result": result}

        if job_type in ("seo_plan", "seo_scan", "analyze"):
            p = _payload(job)
            zip_code = job.get("zip_code") or p.get("zip", "00000")
            map_data = p.get("map", job.get("map_data", "[]"))
            map_str = map_data if isinstance(map_data, str) else json.dumps(map_data)
            prompt = build_seo_prompt(zip_code, map_str, bleed_id)
            output = query_llama(prompt, n_predict=512)
            complete_job(job_id, {"output": output, "zip": zip_code, "agent": agent_id})
            return {"status": "done", "output": output[:200]}

        if job_type == "reason":
            p = _payload(job)
            query = p.get("query", "Summarize next steps for this bleed vertical.")
            answer = query_llama(query, n_predict=256)
            save_memory(f"[{agent_id}] {query} -> {answer}", source=agent_id)
            complete_job(job_id, {"answer": answer, "agent": agent_id})
            return {"status": "done"}

        if job_type == "orchestrate":
            p = _payload(job)
            query = p.get("query", f"Plan workflow for bleed {bleed_id}")
            result = run_pipeline(query, session_id=f"agent-{agent_id}")
            complete_job(job_id, {**result, "agent": agent_id})
            return {"status": "done"}

        if job_type == "build_site":
            p = _payload(job)
            project = p.get("project", "site")
            template = p.get("template", "static-site")
            out_dir = f"/shared/workflows/{project}"
            result = execute_claw("build_website", {"template": template, "output_dir": out_dir})
            complete_job(job_id, {**result, "agent": agent_id})
            return {"status": "done", "result": result}

        if job_type == "deploy":
            p = _payload(job)
            project = p.get("project", "site")
            profile = p.get("profile", "static-export")
            result = run_profile(profile, project)
            complete_job(job_id, {**result, "agent": agent_id})
            return {"status": "done", "result": result}

        if job_type == "file_write":
            p = _payload(job)
            rel = p.get("path", f"workflows/{bleed_id}/notes.txt")
            content = p.get("content", "")
            root = Path(os.getenv("DEV_TOOLS_WORKSPACE", "/shared/workflows"))
            if rel.startswith("/"):
                target = Path(rel)
            elif rel.startswith("workflows/"):
                target = Path("/shared") / rel
            else:
                target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            complete_job(job_id, {"path": str(target), "agent": agent_id})
            return {"status": "done", "path": str(target)}

        if job_type == "memory_ingest":
            p = _payload(job)
            text = p.get("text", job.get("findings", ""))
            save_memory(str(text), source=agent_id)
            try:
                ltm_ingest(str(text), metadata={"bleed_id": bleed_id, "agent": agent_id})
            except Exception:
                pass
            complete_job(job_id, {"ingested": True, "agent": agent_id})
            return {"status": "done"}

        if job_type == "stm_sync":
            p = _payload(job)
            session = p.get("session_id", f"agent-{agent_id}")
            stm_store(session, {"role": "agent", "text": p.get("text", "sync"), "agent": agent_id})
            complete_job(job_id, {"session_id": session, "agent": agent_id})
            return {"status": "done"}

        return {"status": "skipped", "reason": f"No handler for job_type={job_type}"}
    except Exception as exc:
        complete_job(job_id, None, error=str(exc))
        return {"status": "failed", "error": str(exc)}
