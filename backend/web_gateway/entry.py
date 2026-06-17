"""Entry point for the web gateway standalone service."""

import logging
import os

import uvicorn

from web_gateway.app import create_app

logging.basicConfig(level=logging.INFO)


def main() -> None:
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
