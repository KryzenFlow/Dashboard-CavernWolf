"""Hermes Studio — customer-safe scaffold & deploy (no raw agent stack in public mode)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from web_gateway.bleed_config import (
    bleed_context,
    load_manifest,
    resolve_quick_actions,
    set_active_bleed,
)
from web_gateway.hermes_bridge import (
    bridge_status,
    deploy_target,
    list_profiles,
    new_site,
    run_cli_command,
    run_profile,
)
from web_gateway.studio_security import is_public_studio, public_config

router = APIRouter(prefix="/studio", tags=["studio"])

TEMPLATES = [
    {"id": "static-site", "name": "Portfolio Site", "stack": "HTML — Namecheap / any host"},
    {"id": "landing-page", "name": "Business Landing", "stack": "HTML landing page"},
    {"id": "react-app", "name": "App Dashboard", "stack": "React — Railway / Azure / Docker"},
]


class NewWebsiteRequest(BaseModel):
    template: str = "static-site"
    name: str


class DeployRequest(BaseModel):
    profile: str | None = Field(default=None, description="Workflow profile id from deploy-profiles.yaml")
    target: str | None = Field(default=None, description="Public: github | docker | static")
    project: str = "site"
    template: str = "static-site"
    repo: str | None = None
    image: str | None = None


class CliRunRequest(BaseModel):
    command: str = Field(description="Top-level command: new | deploy | ai")
    args: list[str] = Field(default_factory=list, description="Subcommand and flags, e.g. ['site', '--name', 'demo']")


class BleedSelectRequest(BaseModel):
    bleed_id: str
    project: str = "mysite"


def register_studio_routes(app) -> None:
    app.include_router(router)
    app.add_api_route("/cli/run", studio_cli_run, methods=["POST"], tags=["studio"])


@router.get("/config")
def studio_config() -> dict[str, Any]:
    return public_config()


@router.get("/bleeds")
def studio_bleeds(project: str = "mysite") -> dict[str, Any]:
    """Active vertical + switchable bleeds. Public mode hides non-public targets."""
    ctx = bleed_context(public_only=is_public_studio())
    ctx["quick_actions"] = resolve_quick_actions(project=project)
    return ctx


@router.post("/bleed/select")
def studio_bleed_select(req: BleedSelectRequest) -> dict[str, Any]:
    """Switch target vertical — edit bleed-manifest.yaml or ACTIVE_BLEED; this updates the live session."""
    bleeds = load_manifest().get("bleeds", {})
    if req.bleed_id not in bleeds:
        raise HTTPException(status_code=404, detail=f"Unknown bleed: {req.bleed_id}")
    if is_public_studio() and not bleeds[req.bleed_id].get("public", False):
        raise HTTPException(
            status_code=403,
            detail=f"Bleed '{req.bleed_id}' is internal-only. Add public: true in bleed-manifest.yaml or use STUDIO_MODE=internal.",
        )
    switch_err = set_active_bleed(req.bleed_id)
    if switch_err:
        raise HTTPException(status_code=400, detail=switch_err)
    ctx = bleed_context(public_only=is_public_studio())
    ctx["quick_actions"] = resolve_quick_actions(project=req.project)
    return ctx


@router.get("/templates")
def studio_templates() -> dict[str, Any]:
    return {"templates": TEMPLATES}


@router.get("/profiles")
def studio_profiles() -> dict[str, Any]:
    return {"profiles": list_profiles(), "mode": public_config()["mode"]}


@router.get("/bridge-status")
def studio_bridge_status() -> dict[str, Any]:
    return bridge_status()


@router.post("/new-website")
def studio_new_website(req: NewWebsiteRequest) -> dict[str, Any]:
    result = new_site(req.template, req.name)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result)
    return result


@router.post("/deploy")
def studio_deploy(req: DeployRequest) -> dict[str, Any]:
    if is_public_studio() and req.target in ("railway", "azure", "cockroach", "namecheap"):
        raise HTTPException(status_code=403, detail="Use static, github, or docker in public Studio.")
    if req.profile:
        result = run_profile(req.profile, req.project, req.template, {"repo": req.repo, "image": req.image})
    elif req.target:
        result = deploy_target(
            req.target,
            req.project,
            template=req.template,
            repo=req.repo,
            image=req.image,
        )
    else:
        result = run_profile(None, req.project, req.template)
    if result.get("error"):
        code = 403 if "internal-only" in str(result.get("error", "")).lower() else 500
        raise HTTPException(status_code=code, detail=result)
    return result


def _format_cli_output(result: dict[str, Any]) -> str:
    import json

    if "output" in result:
        return str(result["output"])
    if "answer" in result:
        return str(result["answer"])
    return json.dumps(result, indent=2)


@router.post("/cli/run")
def studio_cli_run(req: CliRunRequest) -> dict[str, Any] | StreamingResponse:
    result = run_cli_command(req.command, req.args)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result)

    return {
        "command": req.command,
        "args": req.args,
        "result": result,
        "output": _format_cli_output(result),
    }
