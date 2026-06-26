"""LLaMA / mock LLM client for reasoning."""

from __future__ import annotations

import logging
import os

import requests

_log = logging.getLogger(__name__)

try:
    from llama_index.core import __version__ as LLAMA_INDEX_VERSION

    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_VERSION = None
    LLAMA_INDEX_AVAILABLE = False


def llama_index_available() -> bool:
    return LLAMA_INDEX_AVAILABLE


def query_llama(prompt: str, n_predict: int = 128) -> str:
    provider = os.getenv("LLM_PROVIDER", "mock")
    if provider == "mock":
        return f"[Mock LLaMA] Reasoned response for: {prompt[:400]}"

    url = os.getenv("LLAMA_URL", "http://llama-service:8080")
    try:
        resp = requests.post(
            f"{url}/completion",
            json={"prompt": prompt, "n_predict": n_predict},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content") or data.get("response") or ""
        if content:
            return content
    except Exception as exc:
        _log.warning("LLM request failed (%s): %s", provider, exc)

    return f"[Mock LLaMA] Reasoned response for: {prompt[:400]}"


def reason_with_context(query: str, context: str) -> str:
    soul_path = os.getenv("SOUL_MD_PATH", "/repo/SOUL.md")
    soul_prefix = ""
    try:
        with open(soul_path, encoding="utf-8") as f:
            soul_prefix = f.read()[:1500] + "\n\n"
    except OSError:
        pass

    prompt = f"{soul_prefix}Context:\n{context}\n\nUser query: {query}\n\nAnswer:"
    return query_llama(prompt)
