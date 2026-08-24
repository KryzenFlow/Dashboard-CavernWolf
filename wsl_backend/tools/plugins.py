"""Plugin loader — reads manifests from ./plugins without executing untrusted code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def plugins_root() -> Path:
    return Path(__file__).resolve().parents[2] / "plugins"


def list_plugins() -> list[dict[str, Any]]:
    root = plugins_root()
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/plugin.json")):
        try:
            meta = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(meta, dict):
            continue
        out.append(
            {
                "id": meta.get("id") or path.parent.name,
                "name": meta.get("name") or path.parent.name,
                "version": meta.get("version", "0.0.0"),
                "description": meta.get("description", ""),
                "tools": meta.get("tools", []),
            }
        )
    return out
