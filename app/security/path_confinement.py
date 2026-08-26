from __future__ import annotations

import re
from typing import Any, Iterable

_TRAVERSAL_RE = re.compile(r"(^|/)(\.\./)+|\\\.\.\\|\\{2,}")

_DESTRUCTIVE_CMD_RE = re.compile(
    r"(?i)\b(rm\s+-rf|mkfs(\.[a-z]+)?|dd\s+if=|dd\s+of=|curl\s+http|wget\s+http|ssh\s+|scp\s+|chmod\s+777|chown\s+)",
)


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for v in value.values():
            yield from _iter_strings(v)
        return
    if isinstance(value, list):
        for v in value:
            yield from _iter_strings(v)


def _violates_path_rules(s: str) -> str | None:
    if "\x00" in s:
        return "NUL byte present"
    if s.startswith("/") or s.startswith("./"):
        return "absolute or relative-to-root paths are not allowed"
    if re.match(r"^[A-Za-z]:", s):
        return "drive-letter paths are not allowed"
    if "\\" in s:
        return "backslash paths are not allowed"
    if ".." in s:
        return "path traversal ('..') detected"
    return None


def check_payload(payload: Any) -> tuple[str, str]:
    """
    Deterministic payload gate.
    Returns (verdict, reason) where verdict is \"PASS\" | \"BLOCK\".
    """
    try:
        path_key_names = {
            "path",
            "paths",
            "cmd",
            "command",
            "cwd",
            "working_dir",
            "directory",
            "file",
            "file_path",
            "target",
            "target_path",
        }

        candidate_path_strings: list[str] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(key, str) and key.lower() in path_key_names:
                    candidate_path_strings.extend(_iter_strings(value))

        for s in candidate_path_strings:
            if _TRAVERSAL_RE.search(s):
                return "BLOCK", "traversal regex hit (path field)"
            violation = _violates_path_rules(s)
            if violation is not None:
                return "BLOCK", f"path rule violation: {violation}"

        for s in _iter_strings(payload):
            if _TRAVERSAL_RE.search(s):
                return "BLOCK", "traversal regex hit"

        for s in _iter_strings(payload):
            if _DESTRUCTIVE_CMD_RE.search(s):
                return "BLOCK", "destructive command pattern detected"

        return "PASS", "ok"
    except Exception as exc:
        return "BLOCK", f"path_confinement exception: {exc}"
