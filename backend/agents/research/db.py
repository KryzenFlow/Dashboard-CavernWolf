"""Agent research job queue — keeps agents busy finding vertical/ZIP intel."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

_conn: sqlite3.Connection | None = None


def _db_path() -> str:
    url = os.getenv("RESEARCH_DB_URL", "sqlite:////data/research.db")
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


def init_research_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS research_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bleed_id TEXT NOT NULL,
            zip_code TEXT,
            map_data TEXT,
            job_type TEXT DEFAULT 'seo_scan',
            status TEXT DEFAULT 'pending',
            findings TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS research_findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            bleed_id TEXT NOT NULL,
            zip_code TEXT,
            summary TEXT NOT NULL,
            payload TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES research_jobs(id)
        )
        """
    )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()


def enqueue_job(
    bleed_id: str,
    zip_code: str | None = None,
    map_data: Any = None,
    job_type: str = "seo_scan",
) -> int:
    conn = _connect()
    cur = conn.execute(
        """
        INSERT INTO research_jobs (bleed_id, zip_code, map_data, job_type, status)
        VALUES (?, ?, ?, ?, 'pending')
        """,
        (bleed_id, zip_code, json.dumps(map_data) if map_data is not None else None, job_type),
    )
    conn.commit()
    job_id = int(cur.lastrowid)
    if _db_path() != ":memory:":
        conn.close()
    return job_id


def list_jobs(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    if status:
        rows = conn.execute(
            "SELECT * FROM research_jobs WHERE status = ? ORDER BY id DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM research_jobs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out = [dict(r) for r in rows]
    if _db_path() != ":memory:":
        conn.close()
    return out


def claim_next_job(agent_id: str | None = None, job_types: list[str] | None = None) -> dict[str, Any] | None:
    """Agents poll this to stay busy. Optional filter by agent registry job_types."""
    conn = _connect()
    conn.row_factory = sqlite3.Row
    if job_types:
        placeholders = ",".join("?" * len(job_types))
        row = conn.execute(
            f"""
            SELECT * FROM research_jobs
            WHERE status = 'pending' AND job_type IN ({placeholders})
            ORDER BY id ASC LIMIT 1
            """,
            job_types,
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM research_jobs WHERE status = 'pending' ORDER BY id ASC LIMIT 1"
        ).fetchone()
    if not row:
        if _db_path() != ":memory:":
            conn.close()
        return None
    conn.execute(
        "UPDATE research_jobs SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (row["id"],),
    )
    conn.commit()
    job = dict(row)
    if agent_id:
        job["claimed_by"] = agent_id
    if _db_path() != ":memory:":
        conn.close()
    return job


def complete_job(job_id: int, findings: Any, error: str | None = None) -> None:
    conn = _connect()
    status = "failed" if error else "done"
    conn.execute(
        """
        UPDATE research_jobs
        SET status = ?, findings = ?, error = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, json.dumps(findings) if findings is not None else None, error, job_id),
    )
    if findings and not error:
        row = conn.execute("SELECT bleed_id, zip_code FROM research_jobs WHERE id = ?", (job_id,)).fetchone()
        if row:
            summary = findings if isinstance(findings, str) else json.dumps(findings)[:2000]
            conn.execute(
                """
                INSERT INTO research_findings (job_id, bleed_id, zip_code, summary, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, row[0], row[1], summary[:2000], json.dumps(findings)),
            )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()
