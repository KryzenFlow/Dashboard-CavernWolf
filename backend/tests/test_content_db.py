"""Content DB and publish tests."""

import os
from pathlib import Path

os.environ["CONTENT_DB_URL"] = "sqlite:///:memory:"
os.environ["DEV_TOOLS_WORKSPACE"] = str(Path(__file__).resolve().parents[2] / "shared" / "workflows")

from agents.content.db import create_draft, init_content_db, list_drafts
from agents.content.publish import publish_draft_to_disk


def test_draft_create_and_publish():
    init_content_db()
    draft = create_draft(
        bleed_id="vellorae",
        title="Test Post",
        body_html="<p>Hello clinic world</p>",
        project="test-site",
        slug="test-post",
    )
    assert draft["id"]
    published = publish_draft_to_disk(draft["id"])
    assert published["status"] == "published"
    assert Path(published["path"]).is_file()
    rows = list_drafts(status="published")
    assert any(r["id"] == draft["id"] for r in rows)
