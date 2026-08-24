"""Bash tool — argument lists only. Never shell=True."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any


ALLOWED_BINARIES = frozenset({"git", "ls", "pwd", "echo", "python3", "node", "npm", "bw", "tailscale", "docker"})


def run_bash_list(argv: list[str], *, cwd: str | None = None, timeout: int = 60) -> dict[str, Any]:
    if not argv:
        return {"ok": False, "error": "empty argv"}
    binary = argv[0]
    if "/" in binary or "\\" in binary:
        return {"ok": False, "error": "path binaries not allowed; use bare command name"}
    which = shutil.which(binary)
    if not which or binary not in ALLOWED_BINARIES:
        return {"ok": False, "error": f"binary not allowlisted: {binary}"}
    try:
        completed = subprocess.run(
            [which, *argv[1:]],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "")[:8000],
        "stderr": (completed.stderr or "")[:2000],
    }
