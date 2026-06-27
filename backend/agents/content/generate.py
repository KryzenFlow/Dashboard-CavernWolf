"""AI blog draft generation from bleed context."""

from __future__ import annotations

from agents.content.db import create_draft, slugify
from agents.reasoning.engine import query_llama
from web_gateway.bleed_config import get_bleed


def generate_blog_draft(
    topic: str,
    bleed_id: str,
    project: str = "site",
    job_id: int | None = None,
) -> dict:
    bleed = get_bleed(bleed_id)
    industry = bleed.get("industry", "local business")
    tone = bleed.get("email_tone", "professional")

    prompt = (
        f"Write a blog post for a {industry} website.\n"
        f"Topic: {topic}\n"
        f"Tone: {tone}\n"
        f"Rules: HTML body only (h2, p, ul). No PHI. Include one clear call-to-action paragraph.\n"
        f"Also on the first line write META: (max 155 char description)."
    )
    raw = query_llama(prompt, n_predict=600)

    meta = None
    body = raw
    for line in raw.splitlines():
        if line.strip().upper().startswith("META:"):
            meta = line.split(":", 1)[1].strip()[:155]
            body = raw.replace(line, "", 1).strip()
            break

    title = topic[:120]
    draft = create_draft(
        bleed_id=bleed_id,
        title=title,
        body_html=body,
        project=project,
        slug=slugify(topic),
        meta_description=meta,
        job_id=job_id,
        status="draft",
    )
    return {"draft": draft, "topic": topic}
