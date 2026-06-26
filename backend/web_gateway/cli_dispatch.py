"""Map validated public CLI commands to Claw / bridge actions."""

from __future__ import annotations

from typing import Any

from web_gateway.hermes_bridge import (
    deploy_target,
    execute_claw,
    new_site,
)
from web_gateway.studio_security import is_internal_studio


def _parse_flags(args: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            key = args[i][2:].replace("-", "_")
            out[key] = args[i + 1]
            i += 2
        else:
            i += 1
    return out


def run_validated_cli(command: str, args: list[str]) -> dict[str, Any]:
    """Execute a whitelisted hermes-cli-style command (no raw shell)."""
    cmd = command.lower()
    sub = args[0].lower() if args else ""
    flags = _parse_flags(args[1:] if len(args) > 1 else [])

    if cmd == "new" and sub == "site":
        return new_site(
            template=flags.get("template", "static-site"),
            name=flags.get("name", "mysite"),
        )

    if cmd == "new" and sub == "app":
        return new_site(
            template=flags.get("framework", "react-app"),
            name=flags.get("name", "myapp"),
        )

    if cmd == "deploy" and sub == "github":
        project = flags.get("name", "mysite")
        repo = flags.get("repo") if is_internal_studio() else None
        return deploy_target("github", project, repo=repo)

    if cmd == "deploy" and sub == "docker":
        project = flags.get("name", "mysite")
        image = flags.get("image", f"customer/{project}:latest")
        return deploy_target("docker", project, image=image)

    if cmd == "deploy" and sub == "static":
        return deploy_target("static", flags.get("name", "mysite"))

    if cmd == "ai" and sub == "suggest-template":
        industry = flags.get("industry", "general business")
        from agents.reasoning.engine import query_llama

        answer = query_llama(
            f"Suggest one website template id (static-site, landing-page, or react-app) "
            f"for industry: {industry}. One sentence why."
        )
        return {"answer": answer, "via": "ai-lite"}

    if cmd == "ai" and sub == "generate-content":
        topic = flags.get("topic", "business")
        project = flags.get("name", "mysite")
        result = execute_claw(
            "build_website",
            {"template": "static-site", "output_dir": f"/shared/workflows/{project}"},
        )
        if result.get("error"):
            return result
        from agents.reasoning.engine import query_llama

        copy = query_llama(f"Write short HTML body content (h1, p) for: {topic}. Plain inner HTML only.")
        return {
            "status": "content_generated",
            "project": project,
            "topic": topic,
            "content_preview": copy[:500],
            "path": result.get("path"),
            "via": "ai-lite",
        }

    return {"error": f"Unhandled command: {cmd} {sub}"}
