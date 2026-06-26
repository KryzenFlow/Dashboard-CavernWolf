"""SQLite structured memory for reasoning history."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

_memory_conn: sqlite3.Connection | None = None


def _db_path() -> str:
    url = os.getenv("MEMORY_DB_URL", "sqlite:////data/memory.db")
    if url in ("sqlite:///:memory:", ":memory:"):
        return ":memory:"
    path = url.replace("sqlite:///", "").replace("sqlite://", "")
    if path == ":memory:":
        return path
    if not path.startswith("/") and not (len(path) > 1 and path[1] == ":"):
        path = str(Path.cwd() / path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    global _memory_conn
    path = _db_path()
    if path == ":memory:":
        if _memory_conn is None:
            _memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
        return _memory_conn
    return sqlite3.connect(path)


def init_db() -> None:
    conn = _connect()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'reasoning',
            outcome TEXT DEFAULT 'ok',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()


def save_memory(content: str, source: str = "reasoning", outcome: str = "ok") -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO memory (content, source, outcome) VALUES (?, ?, ?)",
        (content, source, outcome),
    )
    conn.commit()
    if _db_path() != ":memory:":
        conn.close()


def get_memory_rows(limit: int = 50) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT id, content, source, outcome, created_at FROM memory ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    if _db_path() != ":memory:":
        conn.close()
    return [
        {
            "id": r[0],
            "content": r[1],
            "source": r[2],
            "outcome": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]
