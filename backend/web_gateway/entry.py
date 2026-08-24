"""Entry point for the Hermes orchestrator. Refuses false environments."""

import logging
import os
import sys

import uvicorn

from web_gateway.security.environment import FalseEnvironment, assert_no_false_environment

logging.basicConfig(level=logging.INFO)


def main() -> None:
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
