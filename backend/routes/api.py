"""REST API for Hermes Studio. No mock files. Skills/memory are what is on disk."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from web_gateway.security.control_plane import current_root, daily_rebuild, is_halted
from web_gateway.security.supervisor_gates import gate_and_ledger_block_if_needed
from web_gateway.security.token import extract_tree_id, revoke_tree

router = APIRouter()

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
SKILLS_DIR = HERMES_HOME / "skills"
MEMORY_DIR = HERMES_HOME / "memory"


class SkillPayload(BaseModel):
    path: str
    content: str
    language: str = "python"


class SkillTestPayload(BaseModel):
    path: str
    code: str


def _gate_or_block(
    *,
    payload: dict[str, Any],
    lifecycle_token: str | None,
    action: str,
    session_id: str,
) -> None:
    verdict, reason = gate_and_ledger_block_if_needed(
        payload=payload,
        token=lifecycle_token,
        action=action,
        agent_name="hermes-web",
        session_id=session_id,
    )
    if verdict == "PASS":
        return
    tree_id = extract_tree_id(lifecycle_token)
    if tree_id:
        revoke_tree(str(tree_id), reason=reason)
    raise HTTPException(status_code=403, detail=reason)


def _ensure_dirs() -> None:
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _list_dir(root: Path, prefix: str, file_type: str, language: str) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    if not root.is_dir():
        return files
    for path in root.rglob("*"):
        if path.is_file():
            files.append(
                {
                    "path": f"{prefix}/{path.relative_to(root).as_posix()}",
                    "type": file_type,
                    "language": language,
                    "content": path.read_text(encoding="utf-8"),
                    "lastModified": int(path.stat().st_mtime),
                }
            )
    return files


@router.get("/files")
async def list_files(
    type: str = "all",
    x_lifecycle_token: str | None = Header(default=None, alias="X-Lifecycle-Token"),
) -> dict[str, Any]:
    _gate_or_block(
        payload={"type": type},
        lifecycle_token=x_lifecycle_token,
        action="rest:files:read",
        session_id="rest",
    )
    _ensure_dirs()
    files = _list_dir(SKILLS_DIR, "skills", "skill", "python")
    files.extend(_list_dir(MEMORY_DIR, "memory", "memory", "markdown"))
    if type != "all":
        files = [f for f in files if f["type"] == type]
    return {"files": files}


@router.post("/skill/save")
async def save_skill(
    payload: SkillPayload,
    x_lifecycle_token: str | None = Header(default=None, alias="X-Lifecycle-Token"),
) -> dict[str, Any]:
    _gate_or_block(
        payload={"path": payload.path, "language": payload.language, "content_len": len(payload.content)},
        lifecycle_token=x_lifecycle_token,
        action="rest:skill.save",
        session_id="rest",
    )
    _ensure_dirs()
    rel = payload.path.removeprefix("skills/")
    target = SKILLS_DIR / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload.content, encoding="utf-8")
    return {"success": True, "path": str(target)}


@router.post("/skill/test")
async def test_skill(
    payload: SkillTestPayload,
    x_lifecycle_token: str | None = Header(default=None, alias="X-Lifecycle-Token"),
) -> dict[str, Any]:
    _gate_or_block(
        payload={"path": payload.path, "code_len": len(payload.code)},
        lifecycle_token=x_lifecycle_token,
        action="rest:skill.test",
        session_id="rest",
    )
    try:
        compile(payload.code, payload.path, "exec")
        return {"passed": 1, "failed": 0}
    except SyntaxError:
        return {"passed": 0, "failed": 1}


@router.get("/git/status")
async def git_status(
    x_lifecycle_token: str | None = Header(default=None, alias="X-Lifecycle-Token"),
) -> dict[str, Any]:
    _gate_or_block(payload={}, lifecycle_token=x_lifecycle_token, action="rest:git.status:read", session_id="rest")
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=Path.cwd(),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        lines = [line for line in out.splitlines() if line.strip()]
        return {"status": out or "Clean working tree", "uncommitted": len(lines), "unpushed": 0}
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"status": "Git status unavailable", "uncommitted": 0, "unpushed": 0}


@router.get("/control/status")
async def control_status() -> dict[str, Any]:
    return {
        "agent": "claw-opus",
        "halted": is_halted(),
        "merkle_root": current_root(),
    }


@router.post("/control/daily-rebuild")
async def control_daily_rebuild(
    x_lifecycle_token: str | None = Header(default=None, alias="X-Lifecycle-Token"),
) -> dict[str, Any]:
    _gate_or_block(
        payload={"action": "daily-rebuild"},
        lifecycle_token=x_lifecycle_token,
        action="orch:ask_hermes",
        session_id="rest",
    )
    return daily_rebuild()
