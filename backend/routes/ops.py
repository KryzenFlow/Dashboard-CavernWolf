"""Private Agent Ops API — full power, internal Studio only."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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


def register_ops_routes(app) -> None:
    init_research_db()
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
