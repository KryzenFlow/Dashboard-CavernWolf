"""
WSL2 FastAPI entry for Hermes Studio Dash.

- Bitwarden CLI secret pull at startup (no local .env secrets)
- Dynamic agent roster (/agents)
- Bind to Tailscale IPv4 when available (not public host ports)
"""

from __future__ import annotations

import logging
import os
import sys

_log = logging.getLogger("wsl_backend")
logging.basicConfig(level=logging.INFO)


def _bootstrap_path() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend = os.path.join(root, "backend")
    for path in (root, backend):
        if path not in sys.path:
            sys.path.insert(0, path)


def _set_defaults() -> None:
    os.environ.setdefault("CLAW_URL", "http://claw-opus:9000")
    os.environ.setdefault("HERMES_URL", "http://127.0.0.1:8000")
    os.environ.setdefault("HERMES_BIND_TAILSCALE", "1")


def create_studio_app():
    """WSL Hermes app: gates + dynamic /agents roster. Binds in main() to Tailscale IPv4."""
    from web_gateway.app import create_app as create_hermes_app

    return create_hermes_app()


def main() -> None:
    _bootstrap_path()
    _set_defaults()

    from wsl_backend.bitwarden import BitwardenError, pull_secrets_into_environ
    from wsl_backend.tailscale_net import resolve_bind_host
    from web_gateway.security.environment import FalseEnvironment, assert_no_false_environment

    _log.info("Bitwarden startup: pulling secrets (no local .env secrets)")
    try:
        set_keys = pull_secrets_into_environ()
        _log.info("Bitwarden loaded keys: %s", ", ".join(set_keys) or "(none new)")
        assert_no_false_environment()
        host = resolve_bind_host()
    except (BitwardenError, FalseEnvironment, RuntimeError) as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(2) from exc

    import uvicorn

    app = create_studio_app()
    port = int(os.environ.get("PORT", "8000"))
    _log.info("Hermes Studio listening on %s:%s (Tailscale-only bind policy)", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
