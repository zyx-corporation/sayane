"""Context packet and compile route registration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query

from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CompileRequest, ContextPacketResponse
from sayane.bridge.service import compile_prompt

AuthDependency = Callable[..., None]


def register_context_packet_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register compile and context-packet endpoints."""
    router = APIRouter()

    @router.post(
        "/compile",
        response_model=ContextPacketResponse,
        dependencies=[Depends(require_bearer)],
    )
    def post_compile(body: CompileRequest) -> ContextPacketResponse:
        try:
            return compile_prompt(cfg, body)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get(
        "/context-packet",
        response_model=ContextPacketResponse,
        dependencies=[Depends(require_bearer)],
    )
    def get_context_packet(
        target: Annotated[str, Query()],
        profile_id: Annotated[str, Query(alias="profile")] = "default",
        instruction: Annotated[str | None, Query()] = None,
    ) -> ContextPacketResponse:
        request = CompileRequest(
            target=target,
            profile_id=profile_id,
            instruction=instruction,
        )
        try:
            return compile_prompt(cfg, request)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    app.include_router(router)
