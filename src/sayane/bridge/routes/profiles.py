"""Profile route registration."""

from __future__ import annotations

from typing import Annotated, Callable

from fastapi import APIRouter, Depends, FastAPI

from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import ProfileSummary
from sayane.bridge.service import list_profiles

AuthDependency = Callable[..., None]


def register_profile_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register profile endpoints."""
    router = APIRouter()

    @router.get("/profiles", response_model=list[ProfileSummary])
    def get_profiles(
        _: Annotated[None, Depends(require_bearer)],
    ) -> list[ProfileSummary]:
        return list_profiles(cfg)

    app.include_router(router)
