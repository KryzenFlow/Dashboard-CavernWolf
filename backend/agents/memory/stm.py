"""Short-term memory via Redis with in-process fallback."""

from __future__ import annotations

import json
import os
import time
from typing import Any

_stm_fallback: dict[str, list[dict[str, Any]]] = {}
_redis_client = None
_redis_checked = False


def _ttl() -> int:
    return int(os.getenv("STM_TTL_SECONDS", "3600"))


def _get_redis():
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True
    url = os.getenv("REDIS_URL", "")
    if not url:
        return None
    try:
        import redis

        _redis_client = redis.from_url(url, decode_responses=True)
        _redis_client.ping()
    except Exception:
        _redis_client = None
    return _redis_client


def stm_store(session_id: str, entry: dict[str, Any]) -> None:
    entry = {**entry, "ts": time.time()}
    client = _get_redis()
    key = f"session:{session_id}"
    if client:
        client.rpush(key, json.dumps(entry))
        client.expire(key, _ttl())
        return
    _stm_fallback.setdefault(session_id, []).append(entry)


def stm_recall(session_id: str, limit: int = 20) -> list[dict[str, Any]]:
    client = _get_redis()
    key = f"session:{session_id}"
    if client:
        raw = client.lrange(key, -limit, -1)
        return [json.loads(x) for x in raw]
    return _stm_fallback.get(session_id, [])[-limit:]
