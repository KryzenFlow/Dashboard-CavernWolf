"""Hosting targets: static export (Namecheap), Railway, Azure, Cockroach sandbox."""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path


def export_static_zip(params: dict) -> dict:
    """Zip site for FTP upload to Namecheap or any host — no API tokens."""
    site_dir = Path(params.get("site_dir", "/shared/workflows/site"))
    if not site_dir.is_dir():
        return {"error": f"site_dir not found: {site_dir}"}

    zip_path = site_dir.parent / f"{site_dir.name}-upload.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in site_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(site_dir).as_posix())

    guide = site_dir.parent / f"{site_dir.name}-NAMECHEAP-DEPLOY.md"
    guide.write_text(
        f"""# Deploy to Namecheap (or any FTP host)

1. Upload contents of `{site_dir}` OR extract `{zip_path.name}` to `public_html`.
2. In Namecheap Advanced DNS, point your domain A record to your hosting IP (or use Namecheap hosting DNS).
3. No Netlify/Vercel required — your domain stays on Namecheap.

Files ready at:
- Folder: `{site_dir}`
- Zip: `{zip_path}`
""",
        encoding="utf-8",
    )
    return {
        "status": "ready_for_upload",
        "site_dir": str(site_dir),
        "zip": str(zip_path),
        "guide": str(guide),
    }


def deploy_railway(params: dict) -> dict:
    token = os.getenv("RAILWAY_TOKEN", "").strip()
    if not token:
        return {"error": "RAILWAY_TOKEN not set in .env", "status": 503}
    project_dir = params.get("project_dir", "/shared/workflows/site")
    env = {**os.environ, "RAILWAY_TOKEN": token}
    result = subprocess.run(
        "npx --yes @railway/cli up --detach",
        shell=True,
        capture_output=True,
        text=True,
        cwd=project_dir,
        env=env,
    )
    return {
        "status": "deployed" if result.returncode == 0 else "failed",
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-3000:],
        "returncode": result.returncode,
    }


def deploy_azure_static(params: dict) -> dict:
    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
    account = os.getenv("AZURE_STORAGE_ACCOUNT", "").strip()
    container = params.get("container", "$web")
    site_dir = params.get("site_dir", "/shared/workflows/site")
    if not conn and not account:
        return {"error": "Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT in .env", "status": 503}
    if conn:
        cmd = (
            f'az storage blob upload-batch --connection-string "{conn}" '
            f'--destination "{container}" --source "{site_dir}" --overwrite'
        )
    else:
        cmd = (
            f'az storage blob upload-batch --account-name "{account}" '
            f'--destination "{container}" --source "{site_dir}" --overwrite --auth-mode login'
        )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {
        "status": "uploaded" if result.returncode == 0 else "failed",
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-3000:],
        "returncode": result.returncode,
        "hint": "Point Namecheap DNS CNAME to your Azure Static Website endpoint when ready.",
    }


def start_cockroach_sandbox(params: dict) -> dict:
    repo = os.getenv("GIT_REPO_ROOT", "/repo")
    compose_file = Path(repo) / "clinic" / "docker-compose.sandbox.yml"
    if not compose_file.is_file():
        return {"error": f"Sandbox compose not found: {compose_file}"}
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "-d"],
        capture_output=True,
        text=True,
        cwd=compose_file.parent,
    )
    return {
        "status": "started" if result.returncode == 0 else "failed",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "admin_ui": "http://localhost:8080",
        "sql": "localhost:26257",
    }
