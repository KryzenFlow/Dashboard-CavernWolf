"""Private Agent Ops API — full power, internal Studio only."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.content.db import init_content_db
from agents.content.generate import generate_blog_draft
from agents.content.publish import publish_and_export, publish_draft_to_disk
from agents.content.worker import process_claimed_job
from agents.research.db import (
    claim_next_job,
    complete_job,
    enqueue_job,
    init_research_db,
    list_jobs,
)
from agents.research.seo import build_seo_prompt
from agents.reasoning.engine import query_llama
from web_gateway.bleed_config import active_bleed_id, bleed_context, set_active_bleed
from web_gateway.studio_security import assert_internal_access

router = APIRouter(prefix="/ops", tags=["ops"])


class SeoRequest(BaseModel):
    zip: str
    map: str | list[Any] = Field(description="Customer density / map payload")
    bleed_id: str | None = None


class JobEnqueueRequest(BaseModel):
    bleed_id: str | None = None
    zip_code: str | None = None
    map_data: Any = None
    job_type: str = "seo_scan"


class JobCompleteRequest(BaseModel):
    findings: Any = None
    error: str | None = None


class BleedSwitchRequest(BaseModel):
    bleed_id: str


class DraftCreateRequest(BaseModel):
    bleed_id: str | None = None
    project: str = "site"
    title: str
    body_html: str
    slug: str | None = None
    meta_description: str | None = None
    status: str = "draft"


class DraftUpdateRequest(BaseModel):
    title: str | None = None
    body_html: str | None = None
    meta_description: str | None = None
    status: str | None = None


class GenerateBlogRequest(BaseModel):
    topic: str
    bleed_id: str | None = None
    project: str = "site"
    enqueue_only: bool = False


class PublishDraftRequest(BaseModel):
    export: bool = False
    profile: str = "static-export"


def register_ops_routes(app) -> None:
    init_research_db()
    init_content_db()
    app.include_router(router)
    # Bing / LocalRankAI alias
    app.add_api_route("/api/seo", ops_seo_get, methods=["GET"], tags=["ops"])


def _require_internal() -> None:
    err = assert_internal_access()
    if err:
        raise HTTPException(status_code=403, detail=err)


@router.get("/bleeds")
def ops_bleeds() -> dict[str, Any]:
    _require_internal()
    return bleed_context(public_only=False)


@router.post("/bleed/select")
def ops_bleed_select(req: BleedSwitchRequest) -> dict[str, Any]:
    _require_internal()
    err = set_active_bleed(req.bleed_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return bleed_context(public_only=False)


@router.post("/seo")
def ops_seo_post(req: SeoRequest) -> dict[str, Any]:
    return _run_seo(req.zip, req.map, req.bleed_id)


async def ops_seo_get(zip: str, map: str) -> dict[str, Any]:
    return _run_seo(zip, map, None)


def _run_seo(zip_code: str, map_data: str | list[Any], bleed_id: str | None) -> dict[str, Any]:
    _require_internal()
    bid = bleed_id or active_bleed_id()
    map_str = map_data if isinstance(map_data, str) else json.dumps(map_data)
    prompt = build_seo_prompt(zip_code, map_str, bid)
    job_id = enqueue_job(bid, zip_code, map_data, job_type="seo_plan")
    try:
        output = query_llama(prompt, n_predict=512)
        complete_job(job_id, {"output": output, "zip": zip_code})
    except Exception as exc:
        complete_job(job_id, None, error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"vertical": bid, "job_id": job_id, "output": output}


@router.get("/jobs")
def ops_list_jobs(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    _require_internal()
    return {"jobs": list_jobs(status=status, limit=limit)}


@router.post("/jobs")
def ops_enqueue_job(req: JobEnqueueRequest) -> dict[str, Any]:
    _require_internal()
    bid = req.bleed_id or active_bleed_id()
    job_id = enqueue_job(bid, req.zip_code, req.map_data, req.job_type)
    return {"job_id": job_id, "status": "pending"}


@router.post("/jobs/claim")
def ops_claim_job() -> dict[str, Any]:
    """Agents on your other machine poll this to pick up research work."""
    _require_internal()
    job = claim_next_job()
    if not job:
        return {"job": None}
    return {"job": job}


@router.post("/jobs/{job_id}/complete")
def ops_complete_job(job_id: int, req: JobCompleteRequest) -> dict[str, Any]:
    _require_internal()
    complete_job(job_id, req.findings, req.error)
    return {"job_id": job_id, "status": "failed" if req.error else "done"}


@router.post("/jobs/claim-and-run")
def ops_claim_and_run() -> dict[str, Any]:
    """Claim next job and process blog_draft jobs (run on your agent PC)."""
    _require_internal()
    job = claim_next_job()
    if not job:
        return {"job": None}
    outcome = process_claimed_job(job)
    return {"job": job, "outcome": outcome}


@router.get("/content/drafts")
def ops_list_drafts(
    status: str | None = None,
    bleed_id: str | None = None,
    project: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    _require_internal()
    from agents.content.db import list_drafts

    return {"drafts": list_drafts(status=status, bleed_id=bleed_id, project=project, limit=limit)}


@router.post("/content/drafts")
def ops_create_draft(req: DraftCreateRequest) -> dict[str, Any]:
    _require_internal()
    from agents.content.db import create_draft

    bid = req.bleed_id or active_bleed_id()
    draft = create_draft(
        bleed_id=bid,
        title=req.title,
        body_html=req.body_html,
        project=req.project,
        slug=req.slug,
        meta_description=req.meta_description,
        status=req.status,
    )
    return {"draft": draft}


@router.patch("/content/drafts/{draft_id}")
def ops_update_draft(draft_id: int, req: DraftUpdateRequest) -> dict[str, Any]:
    _require_internal()
    from agents.content.db import update_draft

    draft = update_draft(draft_id, **req.model_dump(exclude_unset=True))
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"draft": draft}


@router.post("/content/generate")
def ops_generate_blog(req: GenerateBlogRequest) -> dict[str, Any]:
    _require_internal()
    bid = req.bleed_id or active_bleed_id()
    if req.enqueue_only:
        job_id = enqueue_job(bid, None, {"topic": req.topic, "project": req.project}, job_type="blog_draft")
        return {"job_id": job_id, "status": "pending", "hint": "Run agent_worker.ps1 or POST /ops/jobs/claim-and-run"}
    result = generate_blog_draft(req.topic, bid, req.project)
    return result


@router.post("/content/drafts/{draft_id}/publish")
def ops_publish_draft(draft_id: int, req: PublishDraftRequest) -> dict[str, Any]:
    _require_internal()
    from agents.content.db import get_draft, update_draft

    draft = get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["status"] == "draft":
        update_draft(draft_id, status="approved")
    if req.export:
        return publish_and_export(draft_id, req.profile)
    return publish_draft_to_disk(draft_id)
