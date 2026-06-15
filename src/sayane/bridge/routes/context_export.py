"""Context export route registration."""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import APIRouter, Depends, FastAPI, Query

from sayane.bridge.config import BridgeConfig

AuthDependency = Callable[..., None]


def register_context_export_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register context export endpoints."""
    router = APIRouter()

    @router.get("/export")
    def get_context_export(
        format: str = Query(default="markdown"),
        scope: str = Query(default="identity,interaction"),
        target: str = Query(default="generic"),
        profile_id: str = Query(default="default"),
        _: Annotated[None, Depends(require_bearer)] = None,
    ) -> dict:
        from sayane.bridge.service import resolve_profile_path
        from sayane.core.export import export_markdown, export_prompt, export_yaml
        from sayane.core.loader import load_profile

        scopes = [s.strip() for s in scope.split(",") if s.strip()]
        profile = load_profile(resolve_profile_path(cfg, profile_id))
        if format == "yaml":
            text = export_yaml(profile, scopes)
        elif format == "prompt":
            text = export_prompt(profile, scopes, target)
        else:
            text = export_markdown(profile, scopes, target)
        return {"format": format, "target": target, "scopes": scopes, "text": text}

    app.include_router(router)
