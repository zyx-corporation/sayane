"""FastAPI application for Sayane Local Bridge."""

from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

from sayane.bridge import candidate_api
from sayane.bridge.candidate_api import CandidateOperationError
from sayane.bridge.auth import verify_token
from sayane.bridge.capture_store import save_capture
from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import (
    ApproveCandidateRequest,
    CaptureRequest,
    CaptureResponse,
    CompileRequest,
    ContextPacketResponse,
    EvaluateCandidateRequest,
    ImportantTermsPreflightRequest,
    ImportantTermsPreflightResponse,
    RejectCandidateRequest,
    ReviseCandidateRequest,
    ProfileSummary,
    RejectCandidateRequest,
)
from sayane.bridge.preflight import preview_important_terms_diff
from sayane.bridge.service import compile_prompt, list_profiles
from sayane.core.build_info import get_build_info
from sayane.storage.candidates import load_candidate


def create_app(config: BridgeConfig | None = None) -> FastAPI:
    cfg = config or BridgeConfig()
    build = get_build_info()
    app = FastAPI(
        title="Sayane Local Bridge",
        version=build.version,
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
        return {"status": "ok", **build.as_dict()}

    @app.get("/profiles", response_model=list[ProfileSummary])
    def get_profiles(
        _: Annotated[None, Depends(require_bearer)],
    ) -> list[ProfileSummary]:
        return list_profiles(cfg)

    @app.post("/capture", response_model=CaptureResponse)
    def post_capture(
        body: CaptureRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> CaptureResponse:
        try:
            return save_capture(cfg, body)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/preflight/important-terms",
        response_model=ImportantTermsPreflightResponse,
    )
    def post_preflight_important_terms(
        body: ImportantTermsPreflightRequest,
        _: Annotated[None, Depends(require_bearer)],
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

    @app.get("/export")
    def get_export(
        format: str = Query(default="markdown"),
        scope: str = Query(default="identity,interaction"),
        target: str = Query(default="generic"),
        profile_id: str = Query(default="default"),
        _: Annotated[None, Depends(require_bearer)] = None,
    ) -> dict:
        """Export profile context in yaml, markdown, or prompt format."""
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

    @app.get("/candidates")
    def get_candidates(
        _: Annotated[None, Depends(require_bearer)],
    ) -> list[dict]:
        return candidate_api.list_candidates(cfg)

    @app.get("/candidates/{candidate_id}")
    def get_candidate(
        candidate_id: str,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            return candidate_api.get_candidate(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/candidates/{candidate_id}/evaluate")
    def post_candidate_evaluate(
        candidate_id: str,
        body: EvaluateCandidateRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            return candidate_api.post_evaluate(cfg, candidate_id, level=body.level)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(
                status_code=400,
                detail=exc.to_payload(),
            ) from exc

    @app.post("/candidates/{candidate_id}/approve")
    def post_candidate_approve(
        candidate_id: str,
        body: ApproveCandidateRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            explicit = (
                body.explicit_confirmation.model_dump(mode="json")
                if body.explicit_confirmation
                else None
            )
            return candidate_api.post_approve(
                cfg,
                candidate_id,
                force_critical=body.force_critical,
                override_reason=body.override_reason,
                explicit_confirmation=explicit,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(
                status_code=400,
                detail=exc.to_payload(),
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/candidates/{candidate_id}/reject")
    def post_candidate_reject(
        candidate_id: str,
        body: RejectCandidateRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            return candidate_api.post_reject(cfg, candidate_id, reason=body.reason)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(
                status_code=400,
                detail=exc.to_payload(),
            ) from exc

    @app.post("/candidates/{candidate_id}/revise")
    def post_candidate_revise(
        candidate_id: str,
        body: ReviseCandidateRequest,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            return candidate_api.post_revise(
                cfg,
                candidate_id,
                edited_text=body.edited_text,
                target_section=body.target_section,
                change_reason=body.change_reason,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/candidates/{candidate_id}/diff")
    def get_candidate_diff(
        candidate_id: str,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            load_candidate(cfg, candidate_id)
            return candidate_api.get_diff(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/candidates/{candidate_id}/lineage")
    def get_candidate_lineage(
        candidate_id: str,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            return candidate_api.get_candidate_lineage(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/captures/{capture_id}/lineage")
    def get_capture_lineage(
        capture_id: str,
        _: Annotated[None, Depends(require_bearer)],
    ) -> dict:
        try:
            return candidate_api.get_capture_lineage(cfg, capture_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

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
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return app
