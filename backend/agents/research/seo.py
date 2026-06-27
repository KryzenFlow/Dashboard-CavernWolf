"""Build SEO / outreach prompts from active bleed config."""

from __future__ import annotations

from pathlib import Path

from web_gateway.bleed_config import get_bleed

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def _format_pain_points(bleed: dict) -> str:
    points = bleed.get("pain_points") or []
    return ", ".join(points) if points else "not specified"


def build_seo_prompt(zip_code: str, map_data: str, bleed_id: str | None = None) -> str:
    bleed = get_bleed(bleed_id)
    prompt_name = bleed.get("prompt_template", "seo_plan")
    template_path = _PROMPTS_DIR / f"{prompt_name}.txt"
    if not template_path.is_file():
        template_path = _PROMPTS_DIR / "seo_plan.txt"
    template = template_path.read_text(encoding="utf-8")
    return template.format(
        vertical=bleed.get("label", bleed.get("id", "local business")),
        description=bleed.get("description", bleed.get("pitch", "")),
        pain_points=_format_pain_points(bleed),
        seo_focus=bleed.get("seo_focus", bleed.get("industry", "local SEO")),
        email_tone=bleed.get("email_tone", "professional"),
        zip=zip_code,
        map_data=map_data,
    )
