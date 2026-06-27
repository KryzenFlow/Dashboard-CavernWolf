"""REST API routes for Hermes Studio dashboard."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from web_gateway.studio_security import assert_internal_access, is_public_studio

router = APIRouter()

GIT_REPO_ROOT = Path(os.environ.get("GIT_REPO_ROOT", Path.cwd()))

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
SKILLS_DIR = HERMES_HOME / "skills"
MEMORY_DIR = HERMES_HOME / "memory"
from web_gateway.env import MOCK_MODE


class SkillPayload(BaseModel):
    path: str
    content: str
    language: str = "python"


class SkillTestPayload(BaseModel):
    path: str
    code: str


class GitCommitPayload(BaseModel):
    message: str = "Studio update"


def _ensure_dirs() -> None:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _mock_files() -> list[dict[str, Any]]:
    now = int(datetime.now(timezone.utc).timestamp())
    return [
        {
            "path": "skills/example_greeting.py",
            "type": "skill",
            "language": "python",
            "content": 'def run(name: str) -> str:\n    return f"Hello, {name}!"\n',
            "lastModified": now,
        },
        {
            "path": "memory/facts.md",
            "type": "memory",
            "language": "markdown",
            "content": "# Learned facts\n\n- User prefers OpenClaw + Ollama\n",
            "lastModified": now,
        },
    ]


def _require_internal_api() -> None:
    err = assert_internal_access()
    if err:
        raise HTTPException(status_code=403, detail=err)


@router.get("/files")
async def list_files(type: str = "all") -> dict[str, Any]:
    if is_public_studio():
        return {"files": []}
    _ensure_dirs()
    files: list[dict[str, Any]] = []

    if MOCK_MODE and not any(SKILLS_DIR.glob("*.py")):
        files.extend(_mock_files())
    else:
        for path in SKILLS_DIR.rglob("*"):
            if path.is_file():
                files.append(
                    {
                        "path": f"skills/{path.relative_to(SKILLS_DIR).as_posix()}",
                        "type": "skill",
                        "language": "python",
                        "content": path.read_text(encoding="utf-8"),
                        "lastModified": int(path.stat().st_mtime),
                    }
                )
        for path in MEMORY_DIR.rglob("*"):
            if path.is_file():
                files.append(
                    {
                        "path": f"memory/{path.relative_to(MEMORY_DIR).as_posix()}",
                        "type": "memory",
                        "language": "markdown",
                        "content": path.read_text(encoding="utf-8"),
                        "lastModified": int(path.stat().st_mtime),
                    }
                )

    if type != "all":
        files = [f for f in files if f["type"] == type]
    return {"files": files}


@router.post("/skill/save")
async def save_skill(payload: SkillPayload) -> dict[str, Any]:
    _require_internal_api()
    _ensure_dirs()
    rel = payload.path.removeprefix("skills/")
    target = SKILLS_DIR / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload.content, encoding="utf-8")
    return {"success": True, "path": str(target)}


@router.post("/skill/test")
async def test_skill(payload: SkillTestPayload) -> dict[str, Any]:
    _require_internal_api()
    if MOCK_MODE:
        passed = "def " in payload.code and "return" in payload.code
        return {"passed": 1 if passed else 0, "failed": 0 if passed else 1}

    try:
        compile(payload.code, payload.path, "exec")
        return {"passed": 1, "failed": 0}
    except SyntaxError:
        return {"passed": 0, "failed": 1}


@router.get("/git/status")
async def git_status() -> dict[str, Any]:
    if is_public_studio():
        return {"status": "Git tools available in internal Studio only.", "uncommitted": 0, "unpushed": 0}
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=GIT_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines = [l for l in out.splitlines() if l.strip()]
        return {"status": out or "Clean working tree", "uncommitted": len(lines), "unpushed": 0}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"status": "Not a git repo or git unavailable", "uncommitted": 0, "unpushed": 0}


@router.post("/git/commit")
async def git_commit(payload: GitCommitPayload) -> dict[str, Any]:
    _require_internal_api()
    try:
        subprocess.check_call(["git", "add", "-A"], cwd=GIT_REPO_ROOT)
        subprocess.check_call(["git", "commit", "-m", payload.message], cwd=GIT_REPO_ROOT)
        return {"success": True}
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {"success": False, "error": str(exc)}


@router.post("/git/push")
async def git_push() -> dict[str, Any]:
    _require_internal_api()
    try:
        subprocess.check_call(["git", "push"], cwd=GIT_REPO_ROOT)
        return {"success": True}
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {"success": False, "error": str(exc)}
