"""GitHub Pages and site staging."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Agent Claw")
    env.setdefault("GIT_AUTHOR_EMAIL", "claw@hermes.local")
    return env


def _repo_url_with_token(repo_url: str) -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token or "@" in repo_url:
        return repo_url
    parsed = urlparse(repo_url)
    if parsed.scheme not in ("http", "https"):
        return repo_url
    host = parsed.netloc or parsed.path.split("/")[0]
    path = parsed.path if parsed.netloc else "/" + "/".join(parsed.path.split("/")[1:])
    return f"https://{token}@{host}{path}"


def deploy_github_pages(params: dict) -> dict:
    """Push site_dir to gh-pages branch on GitHub (token via GITHUB_TOKEN or repo_url)."""
    site_dir = Path(params.get("site_dir", "/shared/workflows/site"))
    branch = params.get("branch", "gh-pages")
    repo_url = params.get("repo_url", "").strip()

    if not site_dir.is_dir():
        return {"error": f"site_dir not found: {site_dir}"}

    if not repo_url:
        repo = os.getenv("GITHUB_REPOSITORY", "").strip()
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if repo and token:
            repo_url = f"https://github.com/{repo}.git"
        elif repo:
            repo_url = f"https://github.com/{repo}.git"
        else:
            return {
                "error": "Missing repo_url",
                "hint": "Set repo_url or GITHUB_REPOSITORY (+ GITHUB_TOKEN) in .env",
            }

    auth_url = _repo_url_with_token(repo_url)
    env = _git_env()
    work = site_dir

    def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(cmd, cwd=cwd or work, capture_output=True, text=True, env=env)

    run(["git", "config", "user.name", env["GIT_AUTHOR_NAME"]])
    run(["git", "config", "user.email", env["GIT_AUTHOR_EMAIL"]])

    git_dir = work / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)

    steps = [
        run(["git", "init"]),
        run(["git", "checkout", "-b", branch]),
        run(["git", "add", "."]),
        run(["git", "commit", "-m", params.get("message", "Deploy site via Agent Claw")]),
        run(["git", "remote", "add", "origin", auth_url]),
        run(["git", "push", "-u", "origin", branch, "--force"]),
    ]
    for step in steps[:-1]:
        if step.returncode != 0 and "nothing to commit" not in (step.stdout + step.stderr):
            return {
                "error": "git step failed",
                "cmd": step.args,
                "stderr": step.stderr,
                "stdout": step.stdout,
            }

    push = steps[-1]
    if push.returncode != 0:
        return {
            "error": "git push failed",
            "stderr": push.stderr,
            "stdout": push.stdout,
            "hint": "Ensure GITHUB_TOKEN has repo push access.",
        }

    safe_repo = repo_url.split("@")[-1] if "@" in repo_url else repo_url
    return {
        "status": "Deployed to GitHub Pages",
        "repo": safe_repo,
        "branch": branch,
        "site_dir": str(site_dir),
    }


def deploy_pages_staging(params: dict) -> dict:
    """Build Hermes frontend and copy dist to output_dir (optional git push on main repo)."""
    frontend = params.get("frontend_dir", "/workspace/frontend")
    out = Path(params.get("output_dir", "/shared/workflows/pages-deploy"))
    build = subprocess.run(
        "npm run build",
        shell=True,
        capture_output=True,
        text=True,
        cwd=frontend,
    )
    if build.returncode != 0:
        return {"error": "build failed", "stderr": build.stderr, "returncode": build.returncode}
    dist = Path(frontend) / "dist"
    if not dist.is_dir():
        return {"error": "dist folder missing after build"}
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(dist, out)

    result: dict = {"status": "staged", "path": str(out)}
    if params.get("deploy", False):
        deploy_params = {
            "site_dir": str(out),
            "repo_url": params.get("repo_url", ""),
            "branch": params.get("branch", "gh-pages"),
            "message": params.get("message", "Deploy Pages build"),
        }
        result["deploy"] = deploy_github_pages(deploy_params)
        if deploy_params and result["deploy"].get("status"):
            result["status"] = "deployed"
    return result
