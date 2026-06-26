"""Bleed manifest — switch verticals without code changes."""

import os

os.environ.setdefault("ACTIVE_BLEED", "doctors")

from web_gateway.bleed_config import (
    active_bleed_id,
    bleed_context,
    resolve_quick_actions,
    set_active_bleed,
)


def test_active_bleed_from_env():
    assert active_bleed_id() == "doctors"


def test_resolve_quick_actions_uses_bleed_industry():
    set_active_bleed("saas")
    actions = resolve_quick_actions(project="demo")
    suggest = next(a for a in actions if a["id"] == "ai-suggest")
    assert "B2B software" in suggest["args"]


def test_bleed_context_includes_pain_points_internal():
    set_active_bleed("auto_repair")
    ctx = bleed_context(public_only=False)
    assert ctx["active"]["id"] == "auto_repair"
    assert len(ctx["active"].get("pain_points", [])) >= 1


def test_public_bleeds_hide_internal():
    set_active_bleed("doctors")
    ctx = bleed_context(public_only=True)
    ids = {b["id"] for b in ctx["bleeds"]}
    assert "doctors" not in ids
    assert "local-services" in ids
