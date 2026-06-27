"""Write draft HTML to shared workflows and optional static zip export."""

from __future__ import annotations

import os
from pathlib import Path

from agents.content.db import get_draft, mark_published
from web_gateway.hermes_bridge import execute_claw, run_profile

WORKSPACE = os.getenv("DEV_TOOLS_WORKSPACE", "/shared/workflows")
_REPO_WORKSPACE = Path(__file__).resolve().parents[3] / "shared" / "workflows"


def _workspace_root() -> Path:
    p = Path(WORKSPACE)
    if p.is_dir():
        return p
    _REPO_WORKSPACE.mkdir(parents=True, exist_ok=True)
    return _REPO_WORKSPACE


def _page_html(title: str, body_html: str, meta: str | None) -> str:
    desc = meta or title
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <meta name="description" content="{desc}">
</head>
<body>
  <article>
    <h1>{title}</h1>
    {body_html}
  </article>
</body>
</html>
"""


def publish_draft_to_disk(draft_id: int) -> dict:
    draft = get_draft(draft_id)
    if not draft:
        return {"error": f"Draft {draft_id} not found"}
    if draft["status"] not in ("draft", "approved"):
        if draft["status"] == "published" and draft.get("deploy_path"):
            return {"status": "already_published", "path": draft["deploy_path"]}

    project = draft["project"]
    root = _workspace_root() / project
    blog_dir = root / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    out_file = blog_dir / f"{draft['slug']}.html"
    out_file.write_text(
        _page_html(draft["title"], draft["body_html"], draft.get("meta_description")),
        encoding="utf-8",
    )

    index = root / "index.html"
    if not index.is_file():
        index.write_text(
            _page_html(project, f"<p>Site home — posts in /blog/</p><ul><li><a href=\"blog/{draft['slug']}.html\">{draft['title']}</a></li></ul>", None),
            encoding="utf-8",
        )

    mark_published(draft_id, str(out_file))
    return {"status": "published", "path": str(out_file), "project": project}


def publish_and_export(draft_id: int, profile: str = "static-export") -> dict:
    disk = publish_draft_to_disk(draft_id)
    if disk.get("error"):
        return disk
    project = disk["project"]
    export = run_profile(profile, project, "static-site")
    return {"publish": disk, "export": export}
