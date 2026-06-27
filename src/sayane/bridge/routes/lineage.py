"""Lineage route registration."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from sayane.bridge import candidate_api
from sayane.bridge.config import BridgeConfig
from sayane.bridge.runtime_config import resolve_runtime_backed_bridge_config

AuthDependency = Callable[..., None]


def register_lineage_routes(app: FastAPI, cfg: BridgeConfig, require_bearer: AuthDependency) -> None:
    """Register lineage endpoints."""
    router = APIRouter()

    @router.get("/candidates/{candidate_id}/lineage", dependencies=[Depends(require_bearer)])
    def get_candidate_lineage(candidate_id: str) -> dict:
        try:
            route_cfg, _, _ = resolve_runtime_backed_bridge_config(
                cfg,
                required_scope="lineage:read",
                error_message="Local Vault lineage reads require an active unlock session",
            )
            return candidate_api.get_candidate_lineage(route_cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/captures/{capture_id}/lineage", dependencies=[Depends(require_bearer)])
    def get_capture_lineage(capture_id: str) -> dict:
        try:
            route_cfg, _, _ = resolve_runtime_backed_bridge_config(
                cfg,
                required_scope="lineage:read",
                error_message="Local Vault lineage reads require an active unlock session",
            )
            return candidate_api.get_capture_lineage(route_cfg, capture_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    app.include_router(router)
