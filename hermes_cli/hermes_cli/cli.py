"""hermes-cli - unified CLI for Hermes Stack (scaffold, build, deploy, AI)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import click

from hermes_cli.client import WORKSPACE, backend_reason, claw_execute

TEMPLATE_ALIASES = {
    "portfolio": "static-site",
    "landing": "landing-page",
    "react": "react-app",
    "business": "landing-page",
    "dashboard": "react-app",
}


def _resolve_template(name: str) -> str:
    return TEMPLATE_ALIASES.get(name, name)


def _project_path(name: str) -> str:
    return str(Path(WORKSPACE) / name)


@click.group()
@click.version_option(package_name="hermes-cli")
def main():
    """Hermes CLI - scaffold, build, and deploy customer projects."""


@main.group()
def new():
    """Create new sites or apps from templates."""


@new.command("site")
@click.option("--template", "-t", default="static-site", help="Template pack name")
@click.option("--name", "-n", required=True, help="Project folder name")
def new_site(template: str, name: str):
    """Scaffold a new website: hermes-cli new site -t portfolio -n mysite"""
    tpl = _resolve_template(template)
    result = claw_execute(
        "scaffold",
        {"template": tpl, "project": name},
    )
    click.echo(json.dumps(result, indent=2))
    if result.get("error"):
        raise SystemExit(1)


@new.command("app")
@click.option("--framework", "-f", default="react", type=click.Choice(["react", "next", "vue", "svelte"]))
@click.option("--name", "-n", required=True)
def new_app(framework: str, name: str):
    """Scaffold an app from a framework template."""
    tpl = {"react": "react-app", "next": "react-app", "vue": "static-site", "svelte": "static-site"}.get(
        framework, "react-app"
    )
    result = claw_execute("scaffold", {"template": tpl, "project": name})
    click.echo(json.dumps(result, indent=2))
    if framework == "next" and not result.get("error"):
        path = Path(_project_path(name))
        pkg = path / "package.json"
        if pkg.exists():
            text = pkg.read_text(encoding="utf-8")
            if "next" not in text:
                click.echo("Tip: run `npx create-next-app` in dev-tools for full Next.js scaffold.")


@main.group()
def build():
    """Build projects."""


@build.command("site")
@click.option("--path", "-p", default=None, help="Project path (default: workspace/name)")
@click.option("--name", "-n", default=None, help="Project name under workspace")
def build_site(path: str | None, name: str | None):
    """Run npm build in a project directory."""
    target = path or (f"{WORKSPACE}/{name}" if name else WORKSPACE)
    result = claw_execute("run_cli", {"cmd": "npm run build", "cwd": target})
    click.echo(json.dumps(result, indent=2))


@main.group()
def deploy():
    """Deploy to hosting targets."""


@deploy.command("github")
@click.option("--repo", "-r", default=None, help="GitHub repo (user/repo) or full git URL")
@click.option("--site-dir", "-p", default=None, help="Site directory to deploy")
@click.option("--name", "-n", default="site", help="Project name if site-dir omitted")
@click.option("--branch", default="gh-pages")
def deploy_github(repo: str | None, site_dir: str | None, name: str, branch: str):
    """Deploy site to GitHub Pages branch."""
    site = site_dir or _project_path(name)
    params: dict = {"site_dir": site, "branch": branch}
    if repo:
        if "://" in repo:
            params["repo_url"] = repo
        else:
            params["repo_url"] = f"https://github.com/{repo}.git"
    result = claw_execute("deploy_github_pages", params)
    click.echo(json.dumps(result, indent=2))
    if result.get("error"):
        raise SystemExit(1)


@deploy.command("docker")
@click.option("--image", "-i", default="customer/app:latest")
@click.option("--path", "-p", default=None)
@click.option("--name", "-n", default="site")
def deploy_docker(image: str, path: str | None, name: str):
    """Package project as Docker image."""
    app_dir = path or _project_path(name)
    result = claw_execute("package_docker_app", {"app_dir": app_dir, "image_name": image})
    click.echo(json.dumps(result, indent=2))


@deploy.command("netlify")
@click.option("--site", required=True, help="Netlify site ID")
@click.option("--path", "-p", default=None)
@click.option("--name", "-n", default="site")
def deploy_netlify(site: str, path: str | None, name: str):
    """Deploy via Netlify CLI (must be installed in dev-tools)."""
    target = path or _project_path(name)
    cmd = f"npx netlify deploy --prod --dir={target} --site={site}"
    result = claw_execute("run_cli", {"cmd": cmd, "cwd": target})
    click.echo(json.dumps(result, indent=2))


@deploy.command("vercel")
@click.option("--path", "-p", default=None)
@click.option("--name", "-n", default="site")
def deploy_vercel(path: str | None, name: str):
    """Deploy via Vercel CLI (must be installed in dev-tools)."""
    target = path or _project_path(name)
    result = claw_execute("run_cli", {"cmd": "npx vercel deploy --prod", "cwd": target})
    click.echo(json.dumps(result, indent=2))


@main.group()
def workflow():
    """Run automation workflows."""


@workflow.command("run")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
def workflow_run(file_path: str):
    """Run a JSON workflow file (sequence of claw actions)."""
    spec = json.loads(Path(file_path).read_text(encoding="utf-8"))
    steps = spec.get("steps", [])
    results = []
    for step in steps:
        action = step.get("action")
        params = step.get("params", {})
        if action == "trigger_ci_cd":
            r = claw_execute("trigger_ci_cd", params)
        else:
            r = claw_execute(action, params)
        results.append({"step": action, "result": r})
        click.echo(json.dumps(r, indent=2))
        if r.get("error"):
            raise SystemExit(1)
    return results


@main.command("suggest")
@click.option("--industry", required=True)
def suggest_template(industry: str):
    """AI-suggest best template for an industry."""
    q = f"Recommend the best Hermes website template for industry: {industry}. Options: portfolio/static-site, business/landing-page, react-app dashboard, e-commerce. Reply with one template id and one sentence why."
    result = backend_reason(q)
    click.echo(result.get("answer", json.dumps(result)))


@main.command("generate")
@click.option("--topic", required=True)
@click.option("--path", "-p", default=None)
@click.option("--name", "-n", default="site")
def generate_content(topic: str, path: str | None, name: str):
    """AI-generate website copy and write index.html snippet."""
    q = f"Write concise HTML body content (h1, p, ul) for a website about: {topic}. No markdown, only inner HTML."
    result = backend_reason(q)
    html = result.get("answer", "")
    target = Path(path or _project_path(name))
    target.mkdir(parents=True, exist_ok=True)
    index = target / "index.html"
    if index.exists():
        backup = target / "index.generated.html"
        backup.write_text(html, encoding="utf-8")
        click.echo(f"Wrote generated copy to {backup}")
    else:
        full = f"<!DOCTYPE html><html><head><meta charset=utf-8><title>{topic}</title></head><body>{html}</body></html>"
        index.write_text(full, encoding="utf-8")
        click.echo(f"Wrote {index}")


@main.command("optimize")
@click.option("--path", "-p", default=None)
@click.option("--name", "-n", default="site")
def optimize_seo(path: str | None, name: str):
    """AI SEO suggestions for a project path."""
    target = path or _project_path(name)
    index = Path(target) / "index.html"
    snippet = index.read_text(encoding="utf-8")[:3000] if index.exists() else "(no index.html)"
    q = f"SEO improvements for this HTML (bullet list only):\n{snippet}"
    result = backend_reason(q)
    click.echo(result.get("answer", json.dumps(result)))


@main.command("tools")
def list_tools():
    """Show which CLIs are available in this container."""
    tools = ["hermes-cli", "node", "npm", "npx", "git", "gh", "docker", "python3", "pip"]
    optional = ["netlify", "vercel", "supabase", "firebase", "n8n", "vite", "poetry"]
    for t in tools:
        found = subprocess.run(["which", t], capture_output=True).returncode == 0
        click.echo(f"  {t}: {'yes' if found else 'no'}")
    click.echo("Optional (install via npm/pip in dev-tools):")
    for t in optional:
        found = subprocess.run(["which", t], capture_output=True).returncode == 0
        click.echo(f"  {t}: {'yes' if found else 'no'}")


if __name__ == "__main__":
    main()
