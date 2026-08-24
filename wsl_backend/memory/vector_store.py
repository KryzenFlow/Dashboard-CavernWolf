"""Semantic memory via Qdrant (or compatible). Fail closed when VECTOR_DB_URL unset."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class VectorMemory:
    def __init__(self, url: str | None = None) -> None:
        self.url = (url or os.environ.get("VECTOR_DB_URL", "")).strip().rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.url)

    def status(self) -> dict[str, Any]:
        if not self.url:
            return {"backend": "vector", "ok": False, "error": "VECTOR_DB_URL not configured"}
        try:
            req = urllib.request.Request(f"{self.url}/", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                _ = resp.read(64)
            return {"backend": "vector", "ok": True, "url_host_only": True}
        except Exception as exc:
            return {"backend": "vector", "ok": False, "error": str(exc)[:200]}

    def search(self, collection: str, query_vector: list[float], limit: int = 5) -> dict[str, Any]:
        if not self.url:
            raise RuntimeError("VECTOR_DB_URL not configured")
        # Minimal Qdrant search; callers supply embeddings elsewhere.
        payload = {"vector": query_vector, "limit": limit, "with_payload": True}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.url}/collections/{collection}/points/search",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(exc.read().decode("utf-8", errors="replace")[:300]) from exc
