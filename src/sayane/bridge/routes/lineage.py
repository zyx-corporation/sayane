"""Lineage route registration."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from sayane.bridge import candidate_api
from sayane.bridge.config import BridgeConfig

AuthDependency = Callable[..., None]


def register_lineage_routes(app: FastAPI, cfg: BridgeConfig, require_bearer: AuthDependency) -> None:
    """Register lineage endpoints."""
    router = APIRouter()

    @router.get("/candidates/{candidate_id}/lineage", dependencies=[Depends(require_bearer)])
    def get_candidate_lineage(candidate_id: str) -> dict:
        try:
            return candidate_api.get_candidate_lineage(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/captures/{capture_id}/lineage", dependencies=[Depends(require_bearer)])
    def get_capture_lineage(capture_id: str) -> dict:
        try:
            return candidate_api.get_capture_lineage(cfg, capture_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    app.include_router(router)
