"""
Hermes Studio security — public customer dashboard vs internal agent ops.

STUDIO_MODE=public  → safe whitelist only; no raw agent stack, no proprietary profiles.
STUDIO_MODE=internal → full agent routes, internal deploy profiles, Agent Ops (future).
"""

from __future__ import annotations

import os
from typing import Any

# Bing/Grok-aligned whitelist: command -> allowed subcommands (first positional arg)
PUBLIC_ALLOWED_COMMANDS: dict[str, list[str]] = {
    "new": ["site", "app"],
    "deploy": ["github", "docker", "static"],
    "ai": ["suggest-template", "generate-content"],
}

# Deploy workflow profiles visible in public Studio UI
PUBLIC_DEPLOY_PROFILES = frozenset({"static-export", "github-pages", "docker"})

# Internal-only — Railway, Azure, Cockroach, custom agent workflows
INTERNAL_DEPLOY_PROFILES = frozenset({"railway", "azure-static", "cockroach-sandbox"})

# Flags that must never be accepted from public API (injection / token leak)
FORBIDDEN_ARG_PREFIXES = ("--repo", "http://", "https://", "@", "ghp_", "Bearer")


def studio_mode() -> str:
    return os.getenv("STUDIO_MODE", "public").lower()


def is_public_studio() -> bool:
    return studio_mode() != "internal"


def is_internal_studio() -> bool:
    return studio_mode() == "internal"


def public_config() -> dict[str, Any]:
    return {
        "mode": studio_mode(),
        "public": is_public_studio(),
        "allowed_commands": PUBLIC_ALLOWED_COMMANDS,
        "public_deploy_profiles": sorted(PUBLIC_DEPLOY_PROFILES),
        "features": {
            "agent_stack_api": is_internal_studio(),
            "memory_panel": is_internal_studio(),
            "skills_ide": is_internal_studio(),
            "proprietary_workflows": is_internal_studio(),
            "ai_suggest": True,
            "ai_generate": True,
        },
    }


def validate_public_cli(command: str, args: list[str]) -> str | None:
    """Return error message if not allowed, else None."""
    if is_internal_studio():
        return None

    cmd = (command or "").strip().lower()
    if cmd not in PUBLIC_ALLOWED_COMMANDS:
        return f"Command not allowed in public Studio: {command}"

    if not args:
        return "Subcommand required"

    sub = args[0].lower()
    if sub not in PUBLIC_ALLOWED_COMMANDS[cmd]:
        return f"Subcommand not allowed: {cmd} {sub}"

    for arg in args[1:]:
        low = arg.lower()
        if any(low.startswith(p.lower()) for p in FORBIDDEN_ARG_PREFIXES):
            return "Argument not allowed in public Studio (use Studio buttons or internal mode)"

    return None


def filter_public_profiles(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if is_internal_studio():
        return profiles
    return [p for p in profiles if p.get("id") in PUBLIC_DEPLOY_PROFILES]


def assert_profile_allowed(profile_id: str) -> str | None:
    if is_internal_studio():
        return None
    if profile_id not in PUBLIC_DEPLOY_PROFILES:
        return f"Profile '{profile_id}' is internal-only. Use public Studio or set STUDIO_MODE=internal."
    return None


def assert_internal_access() -> str | None:
    if is_public_studio():
        return "Internal agent stack is not exposed in public Studio mode."
    return None
