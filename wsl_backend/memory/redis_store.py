"""Ephemeral memory via Redis. Fail closed when REDIS_URL is unset."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse


class RedisMemory:
    def __init__(self, url: str | None = None) -> None:
        self.url = (url or os.environ.get("REDIS_URL", "")).strip()
        self._client: Any = None

    @property
    def configured(self) -> bool:
        return bool(self.url)

    def connect(self) -> None:
        if not self.url:
            raise RuntimeError("REDIS_URL not configured")
        try:
            import redis  # type: ignore
        except ImportError as exc:
            raise RuntimeError("redis package not installed") from exc
        parsed = urlparse(self.url)
        self._client = redis.Redis.from_url(self.url, decode_responses=True)
        self._client.ping()
        _ = parsed  # validated by from_url

    def get(self, key: str) -> str | None:
        if not self._client:
            self.connect()
        assert self._client is not None
        return self._client.get(key)

    def set(self, key: str, value: str, ttl_seconds: int | None = 3600) -> None:
        if not self._client:
            self.connect()
        assert self._client is not None
        if ttl_seconds:
            self._client.setex(key, int(ttl_seconds), value)
        else:
            self._client.set(key, value)

    def status(self) -> dict[str, Any]:
        if not self.configured:
            return {"backend": "redis", "ok": False, "error": "REDIS_URL not configured"}
        try:
            self.connect()
            return {"backend": "redis", "ok": True}
        except Exception as exc:
            return {"backend": "redis", "ok": False, "error": str(exc)[:200]}
