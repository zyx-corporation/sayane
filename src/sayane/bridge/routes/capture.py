"""Capture and preflight route registration."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from sayane.bridge.capture_store import save_capture
from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import (
    CaptureRequest,
    CaptureResponse,
    ImportantTermsPreflightRequest,
    ImportantTermsPreflightResponse,
)
from sayane.bridge.preflight import preview_important_terms_diff
from sayane.bridge.runtime_config import resolve_runtime_backed_bridge_config

AuthDependency = Callable[..., None]


def register_capture_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register capture and important-terms preflight endpoints."""
    router = APIRouter()

    @router.post(
        "/capture",
        response_model=CaptureResponse,
        dependencies=[Depends(require_bearer)],
    )
    def post_capture(body: CaptureRequest) -> CaptureResponse:
        try:
            route_cfg, _, _ = resolve_runtime_backed_bridge_config(
                cfg,
                profile_id=body.profile_id,
                required_scope="candidate:write",
                error_message="Local Vault candidate write requires an active unlock session",
            )
            return save_capture(route_cfg, body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post(
        "/preflight/important-terms",
        response_model=ImportantTermsPreflightResponse,
        dependencies=[Depends(require_bearer)],
    )
    def post_preflight_important_terms(
        body: ImportantTermsPreflightRequest,
    ) -> ImportantTermsPreflightResponse:
        try:
            payload = preview_important_terms_diff(
                cfg,
                profile_id=body.profile_id,
                content=body.content,
            )
            return ImportantTermsPreflightResponse(**payload)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    app.include_router(router)
