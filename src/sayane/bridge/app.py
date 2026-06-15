"""FastAPI application for Sayane Local Bridge."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from sayane.bridge.auth import create_bearer_dependency
from sayane.bridge.config import BridgeConfig
from sayane.bridge.routes.all import register_bridge_routes
from sayane.core.build_info import get_build_info


def create_app(config: BridgeConfig | None = None) -> FastAPI:
    cfg = config or BridgeConfig()
    build = get_build_info()
    app = FastAPI(
        title="Sayane Local Bridge",
        version=build.version,
        docs_url="/docs" if False else None,
        redoc_url=None,
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", **build.as_dict()}

    require_bearer = create_bearer_dependency(cfg)
    register_bridge_routes(app, cfg, require_bearer)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return app
