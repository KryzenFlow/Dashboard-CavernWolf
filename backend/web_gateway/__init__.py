"""Web gateway for Hermes Agent — FastAPI server with WebSocket support.

Standalone mode runs without the full hermes-agent repo (mock RPC + REST).
When integrated into NousResearch/hermes-agent, wire dispatch() from tui_gateway.server.
"""

__version__ = "0.1.0"
