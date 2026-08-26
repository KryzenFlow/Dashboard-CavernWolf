"""Refuse trickery and false environment values. Fail closed in production."""

from __future__ import annotations

import os

FALSE_MARKERS = (
    "dev-change-me",
    "changeme",
    "placeholder",
    "example.com",
    "not-a-secret",
    "dummy",
    "fake",
    "mock",
    "test-key",
    "changemeplease",
)


class FalseEnvironment(RuntimeError):
    pass


def _looks_false(value: str) -> bool:
    low = value.strip().lower()
    if not low:
        return True
    return any(marker in low for marker in FALSE_MARKERS)


def require_real_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if _looks_false(value):
        raise FalseEnvironment(
            f"refusing to start: {name} is missing or looks like a false environment value"
        )
    return value


def assert_no_false_environment() -> None:
    if os.environ.get("HERMES_MOCK", "0") == "1":
        raise FalseEnvironment("refusing to start: HERMES_MOCK=1 is a false environment")
    require_real_env("HERMES_SUPERVISOR_HMAC_KEY")
