"""Perceive → Recall → Reason → Plan → Reflect learning loop."""

from __future__ import annotations

from typing import Any

from agents.memory.db import save_memory
from agents.memory.ltm import ltm_ingest, ltm_search
from agents.memory.stm import stm_recall, stm_store
from agents.reasoning.engine import reason_with_context


def run_pipeline(query: str, session_id: str = "web-1") -> dict[str, Any]:
    stm_entries = stm_recall(session_id)
    ltm_hits = ltm_search(query, limit=3)
    context_parts = []
    for e in stm_entries[-5:]:
        context_parts.append(str(e.get("text", e)))
    for hit in ltm_hits:
        context_parts.append(hit.get("text", ""))
    context = "\n".join(context_parts) or "(no prior context)"

    answer = reason_with_context(query, context)

    stm_store(session_id, {"role": "user", "text": query})
    stm_store(session_id, {"role": "assistant", "text": answer})

    save_memory(f"Q: {query} | A: {answer}", source="orchestration", outcome="ok")
    try:
        ltm_ingest(
            f"Q: {query} | A: {answer}",
            metadata={"session_id": session_id, "source": "orchestration", "outcome": "ok"},
        )
    except Exception:
        pass  # LTM optional; do not block reasoning

    actions: list[dict[str, Any]] = [{"type": "reply", "text": answer}]
    if query.strip().lower().startswith("/build"):
        actions.append(
            {
                "type": "build_website",
                "params": {"template": "static-site", "output_dir": "/shared/workflows/site"},
            }
        )

    return {
        "decision": answer,
        "actions": actions,
        "session_id": session_id,
        "context_used": len(context_parts),
    }
