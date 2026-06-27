"""Environment flags for Hermes gateway and API routes."""

from __future__ import annotations

import os


def env_flag(name: str, default: str = "0") -> bool:
    """True when env var is 1, true, or yes (case-insensitive)."""
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


MOCK_MODE = env_flag("HERMES_MOCK", "0")
AGENT_STACK_ENABLED = env_flag("AGENT_STACK_ENABLED", "0")
STUDIO_MODE = os.environ.get("STUDIO_MODE", "public").strip().lower()
AGENT_STACK_USE_AI = env_flag("AGENT_STACK_USE_AI", "0")
