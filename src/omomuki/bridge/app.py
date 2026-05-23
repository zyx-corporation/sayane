"""FastAPI application for Omomuki Local Bridge."""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from omomuki.bridge.auth import verify_token
from omomuki.bridge.capture_store import save_capture
from omomuki.bridge.config import BridgeConfig
from omomuki.bridge.models import (
    CaptureRequest,
    CaptureResponse,
    CompileRequest,
    ContextPacketResponse,
    ProfileSummary,
)
from omomuki.bridge.service import compile_prompt, list_profiles


def create_app(config: BridgeConfig | None = None) -> FastAPI:
    cfg = config or BridgeConfig()
    app = FastAPI(
        title="Omomuki Local Bridge",
        version="0.2.0",
        docs_url="/docs" if False else None,
        redoc_url=None,
    )

    def require_bearer(
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )
        token = authorization.removeprefix("Bearer ").strip()
        if not verify_token(cfg, token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/profiles", response_model=list[ProfileSummary])
    def get_profiles(_: Annotated[None, Depends(require_bearer)]) -> list[ProfileSummary]:
        return list_profiles(cfg)

    @app.post("/capture", response_model=CaptureResponse)
    def post_capture(
        body: CaptureRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> CaptureResponse:
        return save_capture(cfg, body)

    @app.post("/compile", response_model=ContextPacketResponse)
    def post_compile(
        body: CompileRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> ContextPacketResponse:
        try:
            return compile_prompt(cfg, body)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/context-packet", response_model=ContextPacketResponse)
    def get_context_packet(
        _: Annotated[None, Depends(require_bearer)],
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

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    return app
