"""Docker image packaging for customer apps."""

from __future__ import annotations

import subprocess
from pathlib import Path


def package_docker_app(params: dict) -> dict:
    app_dir = Path(params.get("app_dir", params.get("project_dir", "/shared/workflows/site")))
    image_name = params.get("image_name", params.get("tag", "customer-app:latest"))
    dockerfile_name = params.get("dockerfile", "Dockerfile")
    dockerfile = app_dir / dockerfile_name

    if not app_dir.is_dir():
        return {"error": f"app_dir not found: {app_dir}"}

    if not dockerfile.is_file():
        dockerfile.write_text(
            "FROM nginx:alpine\nCOPY . /usr/share/nginx/html\nEXPOSE 80\n",
            encoding="utf-8",
        )

    result = subprocess.run(
        ["docker", "build", "-t", image_name, "-f", str(dockerfile), str(app_dir)],
        capture_output=True,
        text=True,
    )
    return {
        "status": "built" if result.returncode == 0 else "build_failed",
        "image": image_name,
        "app_dir": str(app_dir),
        "stdout": result.stdout[-3000:],
        "stderr": result.stderr[-3000:],
        "returncode": result.returncode,
    }
