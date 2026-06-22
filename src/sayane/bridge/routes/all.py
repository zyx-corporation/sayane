"""Built-in Bridge route registration."""

from __future__ import annotations

from typing import Callable

from fastapi import FastAPI

from sayane.bridge.config import BridgeConfig
from sayane.bridge.routes.candidates import register_candidate_routes
from sayane.bridge.routes.capture import register_capture_routes
from sayane.bridge.routes.context_export import register_context_export_routes
from sayane.bridge.routes.context_packet import register_context_packet_routes
from sayane.bridge.routes.import_bundle import register_import_routes
from sayane.bridge.routes.lineage import register_lineage_routes
from sayane.bridge.routes.profiles import register_profile_routes
from sayane.bridge.routes.resident_app import register_resident_app_routes

AuthDependency = Callable[..., None]


def register_bridge_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register Bridge API routes.

    Keep route registration mechanical and behavior-preserving for #173.
    `create_app()` remains the public FastAPI app factory.
    """
    register_profile_routes(app, cfg, require_bearer)
    register_capture_routes(app, cfg, require_bearer)
    register_context_export_routes(app, cfg, require_bearer)
    register_import_routes(app, cfg, require_bearer)
    register_context_packet_routes(app, cfg, require_bearer)
    register_candidate_routes(app, cfg, require_bearer)
    register_lineage_routes(app, cfg, require_bearer)
    register_resident_app_routes(app, cfg, require_bearer)
