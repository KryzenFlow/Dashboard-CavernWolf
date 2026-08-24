"""RESTful CLI helper for Hermes routing. No secrets in logs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def rest_call(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    base_url: str | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    base = (base_url or os.environ.get("HERMES_URL") or "http://127.0.0.1:8000").rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    url = base + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method.upper(),
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                parsed: Any = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {"text": raw[:2000]}
            return {"ok": True, "status": resp.status, "body": parsed}
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "error": exc.read().decode("utf-8", errors="replace")[:500],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}
