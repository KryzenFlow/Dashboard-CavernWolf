"""
Bleed / vertical targeting — config-driven, switch via ACTIVE_BLEED (no code edits).

Same pattern as deploy-profiles.yaml: edit YAML or change one env var to retarget.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

MANIFEST_PATH = os.getenv(
    "BLEED_MANIFEST_PATH",
    "/shared/workflows/bleed-manifest.yaml",
)
_REPO_MANIFEST = Path(__file__).resolve().parents[2] / "shared" / "workflows" / "bleed-manifest.yaml"

_runtime_bleed_id: str | None = None
_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def _manifest_file() -> Path:
    p = Path(MANIFEST_PATH)
    if p.is_file():
        return p
    if _REPO_MANIFEST.is_file():
        return _REPO_MANIFEST
    return p


def load_manifest() -> dict[str, Any]:
    path = _manifest_file()
    if not path.is_file():
        return {"default_bleed": "local-services", "bleeds": {}, "quick_actions": []}
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def active_bleed_id() -> str:
    global _runtime_bleed_id
    if _runtime_bleed_id:
        return _runtime_bleed_id
    env = os.getenv("ACTIVE_BLEED", "").strip()
    if env:
        return env
    return load_manifest().get("default_bleed", "local-services")


def set_active_bleed(bleed_id: str) -> str | None:
    """Runtime switch (session / dev). Returns error message or None."""
    global _runtime_bleed_id
    cfg = load_manifest()
    bleeds = cfg.get("bleeds", {})
    if bleed_id not in bleeds:
        return f"Unknown bleed: {bleed_id}"
    _runtime_bleed_id = bleed_id
    return None


def get_bleed(bleed_id: str | None = None) -> dict[str, Any]:
    bid = bleed_id or active_bleed_id()
    cfg = load_manifest()
    meta = dict(cfg.get("bleeds", {}).get(bid, {}))
    meta["id"] = bid
    return meta


def list_bleeds(*, public_only: bool = False) -> list[dict[str, Any]]:
    cfg = load_manifest()
    active = active_bleed_id()
    out = []
    for bid, meta in cfg.get("bleeds", {}).items():
        if public_only and not meta.get("public", False):
            continue
        out.append({
            "id": bid,
            "label": meta.get("label", bid),
            "public": bool(meta.get("public", False)),
            "industry": meta.get("industry", ""),
            "template": meta.get("template", "landing-page"),
            "deploy_profile": meta.get("deploy_profile", "static-export"),
            "is_active": bid == active,
        })
    return out


def _resolve_value(value: str, ctx: dict[str, str]) -> str:
    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        return ctx.get(key, m.group(0))

    return _PLACEHOLDER.sub(repl, value)


def resolve_quick_actions(
    project: str = "mysite",
    bleed_id: str | None = None,
) -> list[dict[str, Any]]:
    cfg = load_manifest()
    bleed = get_bleed(bleed_id)
    ctx = {
        "project": project,
        "industry": bleed.get("industry", "general business"),
        "template": bleed.get("template", "static-site"),
        "content_topic": bleed.get("content_topic", "local business"),
        "deploy_profile": bleed.get("deploy_profile", "static-export"),
    }
    actions = []
    for item in cfg.get("quick_actions", []):
        args = [_resolve_value(str(a), ctx) for a in item.get("args", [])]
        actions.append({
            "id": item.get("id"),
            "label": _resolve_value(str(item.get("label", "Run")), ctx),
            "command": item.get("command"),
            "args": args,
        })
    return actions


def bleed_context(public_only: bool = False) -> dict[str, Any]:
    """Payload for Studio UI — active bleed + switchable list + resolved actions."""
    active = get_bleed()
    bid = active.get("id", active_bleed_id())
    ctx = {
        "active_bleed": bid,
        "active": {
            "id": bid,
            "label": active.get("label", bid),
            "industry": active.get("industry", ""),
            "template": active.get("template", "landing-page"),
            "deploy_profile": active.get("deploy_profile", "static-export"),
            "content_topic": active.get("content_topic", ""),
        },
        "bleeds": list_bleeds(public_only=public_only),
        "quick_actions": resolve_quick_actions(),
    }
    if not public_only:
        ctx["active"]["description"] = active.get("description", "")
        ctx["active"]["seo_focus"] = active.get("seo_focus", "")
        ctx["active"]["email_tone"] = active.get("email_tone", "")
        ctx["active"]["pain_points"] = active.get("pain_points", [])
        ctx["active"]["pitch"] = active.get("pitch", "")
        ctx["active"]["notes"] = active.get("notes", "")
    return ctx
