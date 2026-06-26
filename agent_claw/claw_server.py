"""Agent Claw — execution layer (no reasoning logic)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from actions.cicd import trigger_ci_cd
from actions.deploy import deploy_github_pages, deploy_pages_staging
from actions.hosts import (
    deploy_azure_static,
    deploy_railway,
    export_static_zip,
    start_cockroach_sandbox,
)
from actions.package import package_docker_app

app = FastAPI(title="Agent Claw Execution Layer")

ALLOWED_CLI_PREFIXES = ("npm ", "npx ", "node ", "echo ", "git ", "railway ", "az ")


class ActionRequest(BaseModel):
    action: str
    params: dict = Field(default_factory=dict)


# Canonical action names + backward-compatible aliases
ACTION_ALIASES = {
    "deploy_pages": "deploy_pages_staging",
    "docker_package": "package_docker_app",
    "trigger_ci": "trigger_ci_cd",
}


@app.get("/")
def root():
    return {
        "status": "Agent Claw ready",
        "actions": [
            "run_cli",
            "build_website",
            "scaffold",
            "rebuild-site",
            "deploy_github_pages",
            "deploy_pages_staging",
            "package_docker_app",
            "export_static_zip",
            "deploy_railway",
            "deploy_azure_static",
            "start_cockroach_sandbox",
            "trigger_ci_cd",
            "notify",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "agent-claw",
        "github_token": bool(os.getenv("GITHUB_TOKEN")),
        "docker_cli": shutil.which("docker") is not None,
        "gh_cli": shutil.which("gh") is not None,
    }


@app.post("/task")
def task(req: ActionRequest):
    import requests

    backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
    query = req.params.get("query", "")
    session_id = req.params.get("session_id", "web-1")
    r = requests.post(
        f"{backend_url}/agents/task",
        json={"query": query, "session_id": session_id},
        timeout=120,
    )
    return r.json()


@app.post("/execute")
def execute_action(req: ActionRequest):
    action = ACTION_ALIASES.get(req.action, req.action)
    try:
        if action == "run_cli":
            return _run_cli(req.params)
        if action == "build_website":
            return _build_website(req.params)
        if action == "rebuild_hermes":
            return _rebuild_hermes(req.params)
        if action == "rebuild-site":
            return _rebuild_hermes(req.params)
        if action == "scaffold":
            project = req.params.get("project", "demo")
            return _build_website(
                {
                    "template": req.params.get("template", "static-site"),
                    "output_dir": f"/shared/workflows/{project}",
                }
            )
        if action == "notify":
            return _notify_sms(req.params)
        if action == "deploy_github_pages":
            return deploy_github_pages(req.params)
        if action == "deploy_pages_staging":
            return deploy_pages_staging(req.params)
        if action == "package_docker_app":
            return package_docker_app(req.params)
        if action == "trigger_ci_cd":
            return trigger_ci_cd(req.params)
        if action == "export_static_zip":
            return export_static_zip(req.params)
        if action == "deploy_railway":
            return deploy_railway(req.params)
        if action == "deploy_azure_static":
            return deploy_azure_static(req.params)
        if action == "start_cockroach_sandbox":
            return start_cockroach_sandbox(req.params)
        return {"error": f"Unknown action: {req.action}"}
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/rebuild-site")
def rebuild_site_route(req: ActionRequest):
    return execute_action(ActionRequest(action="rebuild-site", params=req.params))


@app.post("/scaffold")
def scaffold_route(req: ActionRequest):
    return execute_action(
        ActionRequest(
            action="scaffold",
            params=req.params or {"template": "static-site", "project": "demo"},
        )
    )


def _run_cli(params: dict) -> dict:
    cmd = params.get("cmd", "")
    if not cmd:
        return {"error": "Missing 'cmd' parameter"}
    if not any(cmd.startswith(p) for p in ALLOWED_CLI_PREFIXES):
        return {"error": f"Command not whitelisted: {cmd[:80]}"}
    workspace = params.get("cwd") or os.getenv("DEV_TOOLS_WORKSPACE", "/shared/workflows")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=workspace)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def _build_website(params: dict) -> dict:
    template = params.get("template", "static-site")
    output_dir = params.get("output_dir", "/shared/workflows/site")
    templates_dir = os.getenv("TEMPLATES_DIR", "/templates")
    src = Path(templates_dir) / template
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        for item in src.iterdir():
            dest = out / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    else:
        out.joinpath("index.html").write_text(
            f"<html><body><h1>Website from {template} template</h1></body></html>",
            encoding="utf-8",
        )
    return {"status": "Website built", "path": str(out)}


def _rebuild_hermes(params: dict) -> dict:
    frontend = params.get("frontend_dir", "/workspace/frontend")
    result = subprocess.run(
        "npm run build",
        shell=True,
        capture_output=True,
        text=True,
        cwd=frontend,
    )
    return {
        "status": "rebuild_complete" if result.returncode == 0 else "rebuild_failed",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def _notify_sms(params: dict):
    sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    token = os.getenv("TWILIO_AUTH_TOKEN", "")
    from_num = os.getenv("TWILIO_FROM", "")
    to_num = params.get("to", "")
    body = params.get("body", "")
    if not all([sid, token, from_num, to_num]):
        return {"error": "Twilio not configured or missing 'to'", "status": 503}
    import requests

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    r = requests.post(
        url,
        data={"From": from_num, "To": to_num, "Body": body},
        auth=(sid, token),
        timeout=30,
    )
    if r.status_code >= 400:
        return {"error": r.text, "status": r.status_code}
    return {"status": "sent", "sid": r.json().get("sid")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
