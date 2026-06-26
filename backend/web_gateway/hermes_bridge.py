"""
Hermes bridge — reversible, token-optional execution via Agent Claw.

Default: HERMES_CLI_BRIDGE=claw (direct HTTP to Agent Claw, no docker-exec, no AI).
Studio deploy/scaffold never calls /reason unless AGENT_STACK_USE_AI=1.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import requests
import yaml

_log = logging.getLogger(__name__)

CLAW_URL = os.getenv("CLAW_URL", "http://agent-claw:9000")
DEV_TOOLS_CONTAINER = os.getenv("DEV_TOOLS_CONTAINER", "dev-tools")
BRIDGE_MODE = os.getenv("HERMES_CLI_BRIDGE", "claw").lower()
PROFILES_PATH = os.getenv(
    "DEPLOY_PROFILES_PATH",
    "/shared/workflows/deploy-profiles.yaml",
)
# Fallback when not in Docker
_REPO_PROFILES = Path(__file__).resolve().parents[2] / "shared" / "workflows" / "deploy-profiles.yaml"


def _profiles_file() -> Path:
    p = Path(PROFILES_PATH)
    if p.is_file():
        return p
    if _REPO_PROFILES.is_file():
        return _REPO_PROFILES
    return p


def _docker_available() -> bool:
    return shutil.which("docker") is not None and os.path.exists("/var/run/docker.sock")


def execute_claw(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Single entry point for all Claw actions (no AI, no tokens by default)."""
    try:
        r = requests.post(
            f"{CLAW_URL}/execute",
            json={"action": action, "params": params or {}},
            timeout=300,
        )
        data = r.json()
        data["via"] = "agent-claw"
        if r.status_code >= 400 and "error" not in data:
            data["error"] = r.text
        return data
    except Exception as exc:
        return {"error": str(exc), "via": "agent-claw"}


def _run_hermes_cli(args: list[str], timeout: int = 300) -> dict[str, Any]:
    cmd = [
        "docker", "exec",
        "-e", f"CLAW_URL={CLAW_URL}",
        "-e", f"BACKEND_URL={os.getenv('BACKEND_URL', 'http://backend:8000')}",
        DEV_TOOLS_CONTAINER, "hermes-cli", *args,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode != 0:
        return {"error": stderr or stdout or f"exit {result.returncode}", "via": "hermes-cli"}
    try:
        data = json.loads(stdout)
        data["via"] = "hermes-cli"
        return data
    except json.JSONDecodeError:
        return {"status": "ok", "output": stdout, "via": "hermes-cli"}


def _dispatch_cli(cli_args: list[str], action: str, params: dict[str, Any]) -> dict[str, Any]:
    if BRIDGE_MODE == "claw":
        return execute_claw(action, params)
    if BRIDGE_MODE in ("docker", "auto") and _docker_available():
        try:
            out = _run_hermes_cli(cli_args)
            if "error" not in out:
                return out
        except Exception as exc:
            _log.warning("hermes-cli exec failed: %s", exc)
        if BRIDGE_MODE == "docker":
            return {"error": "hermes-cli failed in dev-tools", "via": "hermes-cli"}
    return execute_claw(action, params)


def load_profiles() -> dict[str, Any]:
    path = _profiles_file()
    if not path.is_file():
        return {"default_profile": "static-export", "profiles": {}}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def list_profiles() -> list[dict[str, Any]]:
    from web_gateway.studio_security import filter_public_profiles

    cfg = load_profiles()
    profiles = cfg.get("profiles", {})
    default = cfg.get("default_profile", "static-export")
    out = []
    for pid, meta in profiles.items():
        required = meta.get("requires_env", [])
        missing = [k for k in required if not os.getenv(k, "").strip()]
        out.append({
            "id": pid,
            "label": meta.get("label", pid),
            "description": meta.get("description", ""),
            "requires_env": required,
            "ready": len(missing) == 0,
            "missing_env": missing,
            "is_default": pid == os.getenv("DEPLOY_PROFILE", default),
            "internal_only": pid not in {"static-export", "github-pages", "docker"},
        })
    return filter_public_profiles(out)


def _format_params(params: dict[str, Any], project: str, extra: dict[str, Any]) -> dict[str, Any]:
    merged = {**params, **extra}
    return {
        k: v.format(project=project, **extra) if isinstance(v, str) else v
        for k, v in merged.items()
    }


def run_profile(profile_id: str | None, project: str, template: str = "static-site", extra: dict | None = None) -> dict[str, Any]:
    """Run a named deploy profile (reversible — change DEPLOY_PROFILE or pass profile_id)."""
    from web_gateway.studio_security import assert_profile_allowed

    cfg = load_profiles()
    pid = profile_id or os.getenv("DEPLOY_PROFILE") or cfg.get("default_profile", "static-export")

    blocked = assert_profile_allowed(pid)
    if blocked:
        return {"error": blocked, "profile": pid}
    profiles = cfg.get("profiles", {})
    if pid not in profiles:
        return {"error": f"Unknown profile: {pid}", "available": list(profiles.keys())}

    meta = profiles[pid]
    missing = [k for k in meta.get("requires_env", []) if not os.getenv(k, "").strip()]
    if missing:
        return {
            "error": "Missing required environment variables for this profile",
            "profile": pid,
            "missing_env": missing,
            "hint": "Add tokens to .env or choose profile static-export / github-pages / docker",
        }

    ctx = {"project": project, "template": template, **(extra or {})}
    results = []
    for step in meta.get("steps", []):
        action = step["action"]
        params = _format_params(step.get("params", {}), project, ctx)
        if action == "build_website" and "template" not in params:
            params["template"] = template
        r = execute_claw(action, params)
        results.append({"step": action, "result": r})
        if r.get("error"):
            return {"profile": pid, "status": "failed", "steps": results}
    return {"profile": pid, "status": "ok", "steps": results}


def new_site(template: str, name: str) -> dict[str, Any]:
    return _dispatch_cli(
        ["new", "site", "--template", template, "--name", name],
        "scaffold",
        {"template": template, "project": name},
    )


def deploy_target(target: str, project: str, **kwargs: Any) -> dict[str, Any]:
    """Map legacy target strings to profiles."""
    from web_gateway.studio_security import assert_profile_allowed

    mapping = {
        "github": "github-pages",
        "docker": "docker",
        "railway": "railway",
        "azure": "azure-static",
        "static": "static-export",
        "namecheap": "static-export",
        "cockroach": "cockroach-sandbox",
    }
    profile = mapping.get(target, target)
    blocked = assert_profile_allowed(profile)
    if blocked:
        return {"error": blocked, "target": target, "profile": profile}
    return run_profile(profile, project, kwargs.get("template", "static-site"), kwargs)


def run_cli_command(command: str, args: list[str] | None = None) -> dict[str, Any]:
    """
    Run allowlisted CLI. Public mode: strict command/subcommand whitelist.
    Accepts Bing-style {command, args} or legacy single string.
    """
    from web_gateway.cli_dispatch import run_validated_cli
    from web_gateway.studio_security import validate_public_cli

    if args is None:
        parts = command.strip().split()
        if not parts:
            return {"error": "Empty command"}
        command, args = parts[0], parts[1:]

    err = validate_public_cli(command, args)
    if err:
        return {"error": err}

    return run_validated_cli(command, args)


def bridge_status() -> dict[str, Any]:
    from web_gateway.studio_security import public_config

    return {
        **public_config(),
        "bridge_mode": BRIDGE_MODE,
        "docker_available": _docker_available(),
        "claw_url": CLAW_URL,
        "deploy_profile": os.getenv("DEPLOY_PROFILE", load_profiles().get("default_profile")),
        "agent_stack_use_ai": os.getenv("AGENT_STACK_USE_AI", "0") == "1",
        "profiles": list_profiles(),
    }
