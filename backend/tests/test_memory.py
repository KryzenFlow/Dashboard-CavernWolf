"""Backend unit tests."""

from __future__ import annotations

import os

os.environ.setdefault("MEMORY_DB_URL", "sqlite:///:memory:")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("AGENT_STACK_ENABLED", "0")

from agents.memory.db import get_memory_rows, init_db, save_memory
from agents.reasoning.engine import query_llama


def test_memory_roundtrip():
    init_db()
    save_memory("test entry", source="test")
    rows = get_memory_rows(10)
    assert any("test entry" in r["content"] for r in rows)


def test_mock_llm():
    answer = query_llama("hello")
    assert "hello" in answer.lower() or "Mock" in answer
