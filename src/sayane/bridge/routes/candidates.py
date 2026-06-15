"""Candidate lifecycle route registration."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from sayane.bridge import candidate_api
from sayane.bridge.candidate_api import CandidateOperationError
from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import (
    ApproveCandidateRequest,
    EvaluateCandidateRequest,
    RejectCandidateRequest,
    ReviseCandidateRequest,
)
from sayane.storage.candidates import load_candidate

AuthDependency = Callable[..., None]


def register_candidate_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register candidate lifecycle endpoints."""
    router = APIRouter()

    @router.get("/candidates", dependencies=[Depends(require_bearer)])
    def get_candidates() -> list[dict]:
        return candidate_api.list_candidates(cfg)

    @router.get("/candidates/{candidate_id}", dependencies=[Depends(require_bearer)])
    def get_candidate(candidate_id: str) -> dict:
        try:
            return candidate_api.get_candidate(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post(
        "/candidates/{candidate_id}/evaluate",
        dependencies=[Depends(require_bearer)],
    )
    def post_candidate_evaluate(
        candidate_id: str,
        body: EvaluateCandidateRequest,
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

    @router.post(
        "/candidates/{candidate_id}/approve",
        dependencies=[Depends(require_bearer)],
    )
    def post_candidate_approve(
        candidate_id: str,
        body: ApproveCandidateRequest,
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

    @router.post(
        "/candidates/{candidate_id}/reject",
        dependencies=[Depends(require_bearer)],
    )
    def post_candidate_reject(
        candidate_id: str,
        body: RejectCandidateRequest,
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

    @router.post(
        "/candidates/{candidate_id}/revise",
        dependencies=[Depends(require_bearer)],
    )
    def post_candidate_revise(
        candidate_id: str,
        body: ReviseCandidateRequest,
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

    @router.get("/candidates/{candidate_id}/diff", dependencies=[Depends(require_bearer)])
    def get_candidate_diff(candidate_id: str) -> dict:
        try:
            load_candidate(cfg, candidate_id)
            return candidate_api.get_diff(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    app.include_router(router)
