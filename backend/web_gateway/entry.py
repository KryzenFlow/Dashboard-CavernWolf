"""Entry point for the Hermes orchestrator. Refuses false environments.

Prefer `python3 -m wsl_backend.main` on WSL so secrets come from Bitwarden
CLI at startup. This module does not load a local .env for secrets.
"""

import logging
import os
import sys

import uvicorn

from web_gateway.security.environment import FalseEnvironment, assert_no_false_environment

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)


def _maybe_pull_bitwarden() -> None:
    """If BW_SESSION is set, pull secrets from Bitwarden before boot checks."""
    if not os.environ.get("BW_SESSION", "").strip():
        return
    try:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if root not in sys.path:
            sys.path.insert(0, root)
        from wsl_backend.bitwarden import pull_secrets_into_environ

        keys = pull_secrets_into_environ()
        _log.info("Bitwarden loaded keys: %s", ", ".join(keys) or "(none new)")
    except Exception as exc:
        sys.stderr.write(f"Bitwarden pull failed: {exc}\n")
        raise SystemExit(2) from exc


def main() -> None:
    _maybe_pull_bitwarden()
    try:
        assert_no_false_environment()
    except FalseEnvironment as exc:
        sys.stderr.write(f"{exc}\n")
        raise SystemExit(2) from exc

    port = int(os.environ.get("PORT", os.environ.get("HERMES_GATEWAY_PORT", "8000")))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "0") == "1"
    uvicorn.run(
        "web_gateway.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        loop="asyncio" if os.name == "nt" else "auto",
    )


if __name__ == "__main__":
    main()
