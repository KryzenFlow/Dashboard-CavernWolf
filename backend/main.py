"""Unified FastAPI entry: Hermes gateway + multi-agent routes."""

from web_gateway.app import create_app
from routes.agents import register_agent_routes
from routes.ops import register_ops_routes
from routes.studio import register_studio_routes

app = create_app()
register_agent_routes(app)
register_studio_routes(app)
register_ops_routes(app)
