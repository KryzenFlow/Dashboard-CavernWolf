"""CI/CD triggers: webhooks and GitHub Actions CLI."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

import requests


def trigger_ci_cd(params: dict) -> dict:
    webhook_url = params.get("webhook_url", "").strip()
    if webhook_url:
        payload: dict[str, Any] = params.get("payload", {})
        headers = params.get("headers", {})
        token = os.getenv("CI_WEBHOOK_TOKEN", "")
        if token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = requests.post(webhook_url, json=payload, headers=headers, timeout=60)
            return {
                "status": "Triggered CI/CD",
                "webhook_url": webhook_url.split("?")[0],
                "response_code": resp.status_code,
                "response_body": resp.text[:2000],
            }
        except Exception as exc:
            return {"error": str(exc), "webhook_url": webhook_url}

    return _trigger_github_workflow(params)


def _trigger_github_workflow(params: dict) -> dict:
    workflow = params.get("workflow", "pages.yml")
    repo_root = params.get("repo_root") or os.getenv("GIT_REPO_ROOT", "/repo")
    ref = params.get("ref", "main")
    gh = shutil.which("gh")
    if not gh:
        return {
            "error": "Missing webhook_url and gh CLI not installed",
            "hint": "Set webhook_url for external CI, or install GitHub CLI in agent-claw.",
        }
    env = os.environ.copy()
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        env["GH_TOKEN"] = token
    result = subprocess.run(
        [gh, "workflow", "run", workflow, "--ref", ref],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "status": "triggered" if result.returncode == 0 else "failed",
        "workflow": workflow,
        "ref": ref,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }
