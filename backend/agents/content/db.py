"""Content queue — blog drafts and web pages (SQLite, OneDrive-friendly data/ folder)."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

_conn: sqlite3.Connection | None = None


def _db_path() -> str:
    url = os.getenv("CONTENT_DB_URL", "sqlite:////data/content.db")
    if ":memory:" in url:
        return ":memory:"
    path = url.replace("sqlite:///", "").replace("sqlite://", "")
    if not path.startswith("/") and not (len(path) > 1 and path[1] == ":"):
        path = str(Path.cwd() / path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    global _conn
    path = _db_path()
    if path == ":memory:":
        if _conn is None:
            _conn = sqlite3.connect(":memory:", check_same_thread=False)
        return _conn
    return sqlite3.connect(path)


def init_content_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS blog_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bleed_id TEXT NOT NULL,
            project TEXT NOT NULL DEFAULT 'site',
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            body_html TEXT NOT NULL,
            meta_description TEXT,
            status TEXT NOT NULL DEFAULT 'draft',
            deploy_path TEXT,
            job_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project, slug)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS published_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draft_id INTEGER NOT NULL,
            project TEXT NOT NULL,
            file_path TEXT NOT NULL,
            published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (draft_id) REFERENCES blog_drafts(id)
        )
        """
    )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "post"


def create_draft(
    bleed_id: str,
    title: str,
    body_html: str,
    project: str = "site",
    slug: str | None = None,
    meta_description: str | None = None,
    job_id: int | None = None,
    status: str = "draft",
) -> dict[str, Any]:
    slug = slug or slugify(title)
    conn = _connect()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            INSERT INTO blog_drafts
            (bleed_id, project, title, slug, body_html, meta_description, status, job_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (bleed_id, project, title, slug, body_html, meta_description, status, job_id),
        )
        conn.commit()
        draft_id = int(cur.lastrowid)
    except sqlite3.IntegrityError:
        conn.execute(
            """
            UPDATE blog_drafts
            SET body_html = ?, meta_description = ?, status = ?, job_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE project = ? AND slug = ?
            """,
            (body_html, meta_description, status, job_id, project, slug),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM blog_drafts WHERE project = ? AND slug = ?",
            (project, slug),
        ).fetchone()
        draft_id = int(row["id"])
    row = conn.execute("SELECT * FROM blog_drafts WHERE id = ?", (draft_id,)).fetchone()
    if _db_path() != ":memory:":
        conn.close()
    return dict(row)


def get_draft(draft_id: int) -> dict[str, Any] | None:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM blog_drafts WHERE id = ?", (draft_id,)).fetchone()
    if _db_path() != ":memory:":
        conn.close()
    return dict(row) if row else None


def list_drafts(
    status: str | None = None,
    bleed_id: str | None = None,
    project: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    clauses: list[str] = []
    params: list[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if bleed_id:
        clauses.append("bleed_id = ?")
        params.append(bleed_id)
    if project:
        clauses.append("project = ?")
        params.append(project)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)
    rows = conn.execute(
        f"SELECT * FROM blog_drafts {where} ORDER BY id DESC LIMIT ?",
        params,
    ).fetchall()
    out = [dict(r) for r in rows]
    if _db_path() != ":memory:":
        conn.close()
    return out


def update_draft(draft_id: int, **fields: Any) -> dict[str, Any] | None:
    allowed = {"title", "slug", "body_html", "meta_description", "status", "project", "deploy_path"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return get_draft(draft_id)
    conn = _connect()
    sets = ", ".join(f"{k} = ?" for k in updates)
    vals = list(updates.values()) + [draft_id]
    conn.execute(
        f"UPDATE blog_drafts SET {sets}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        vals,
    )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()
    return get_draft(draft_id)


def mark_published(draft_id: int, file_path: str) -> None:
    conn = _connect()
    row = conn.execute("SELECT project FROM blog_drafts WHERE id = ?", (draft_id,)).fetchone()
    if not row:
        if _db_path() != ":memory:":
            conn.close()
        return
    conn.execute(
        """
        UPDATE blog_drafts
        SET status = 'published', deploy_path = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (file_path, draft_id),
    )
    conn.execute(
        "INSERT INTO published_pages (draft_id, project, file_path) VALUES (?, ?, ?)",
        (draft_id, row[0], file_path),
    )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()
