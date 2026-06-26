"""Long-term semantic memory via Chroma (optional when service available)."""

from __future__ import annotations

import logging
import os
from typing import Any

_log = logging.getLogger(__name__)
_chroma_collection = None
_chroma_checked = False


def _ltm_enabled() -> bool:
    return os.getenv("LTM_ENABLED", "1") == "1"


def _get_collection():
    global _chroma_collection, _chroma_checked
    if not _ltm_enabled():
        return None
    if _chroma_checked:
        return _chroma_collection
    _chroma_checked = True
    chroma_url = os.getenv("CHROMA_URL", "")
    if not chroma_url:
        return None
    try:
        import chromadb

        host = chroma_url.replace("http://", "").replace("https://", "").split(":")[0]
        port = int(chroma_url.split(":")[-1].rstrip("/") or "8000")
        client = chromadb.HttpClient(host=host, port=port)
        _chroma_collection = client.get_or_create_collection("hermes_ltm")
    except Exception as exc:
        _log.warning("Chroma unavailable: %s", exc)
        _chroma_collection = None
    return _chroma_collection


def ltm_ingest(text: str, metadata: dict[str, Any] | None = None) -> bool:
    coll = _get_collection()
    if not coll:
        return False
    try:
        import uuid

        coll.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())],
        )
        return True
    except Exception as exc:
        _log.warning("LTM ingest failed: %s", exc)
        return False


def ltm_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    coll = _get_collection()
    if not coll:
        return []
    try:
        result = coll.query(query_texts=[query], n_results=limit)
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        return [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
    except Exception as exc:
        _log.warning("LTM search failed: %s", exc)
        return []
