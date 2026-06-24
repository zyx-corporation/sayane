"""Resident app-facing Bridge route registration."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from sayane.bridge import candidate_api
from sayane.bridge.auth import clear_ui_session, issue_ui_session, verify_token, verify_ui_session
from sayane.bridge.candidate_api import CandidateOperationError
from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import (
    AppCaptureClipboardRequest,
    ApproveCandidateRequest,
    EvaluateCandidateRequest,
    RejectCandidateRequest,
    ReviseCandidateRequest,
)

AuthDependency = Callable[..., None]


def register_resident_app_routes(
    app: FastAPI,
    cfg: BridgeConfig,
    require_bearer: AuthDependency,
) -> None:
    """Register resident app-facing overview endpoints."""
    router = APIRouter()
    ui_cookie_name = "sayane_bridge_ui_session"
    ui_locale_cookie_name = "sayane_bridge_ui_locale"

    def _reviewable_candidate_queue() -> dict[str, object]:
        from sayane.app.app_candidate_views import build_app_candidate_queue

        items = [
            item
            for item in candidate_api.list_candidates(cfg)
            if item.get("status") in {"pending", "evaluated"}
        ]
        return build_app_candidate_queue(items)

    def _candidate_detail_payload(candidate_id: str) -> dict[str, object]:
        from sayane.app.app_candidate_views import build_app_candidate_detail

        payload = candidate_api.get_candidate(cfg, candidate_id)
        payload["review_surface"] = "resident_app_bridge"
        return build_app_candidate_detail(payload)

    def _candidate_detail_screen_state(candidate_id: str) -> dict[str, object]:
        from sayane.app import build_candidate_detail_screen_state

        return build_candidate_detail_screen_state(_candidate_detail_payload(candidate_id))

    def _candidate_diff_payload(candidate_id: str) -> dict[str, object]:
        from sayane.app.app_candidate_views import build_app_candidate_diff

        payload = candidate_api.get_diff(cfg, candidate_id)
        payload["review_surface"] = "resident_app_bridge"
        return build_app_candidate_diff(payload)

    def _daemon_overview_payload(*, host: str, port: int) -> dict[str, object]:
        from sayane.app.capabilities import create_local_capability_token
        from sayane.app.ui import build_daemon_overview_preview

        payload = build_daemon_overview_preview(
            cfg.home / "run",
            capability=create_local_capability_token(["ui"]),
            host=host,
            port=port,
        )
        payload["preflight_report"] = _daemon_preflight_payload()
        return payload

    def _daemon_panel_screen_state() -> dict[str, object]:
        from sayane.app import build_daemon_panel_screen_state

        payload = _daemon_overview_payload(host=cfg.host, port=cfg.port)
        payload["operator_phase_status"] = _operator_phase_status_payload()
        return build_daemon_panel_screen_state(payload)

    def _operator_phase_status_payload() -> dict[str, object]:
        from sayane.app import build_daemon_operator_phase_status

        return build_daemon_operator_phase_status(
            cfg.home / "run",
            host=cfg.host,
            port=cfg.port,
        ).public_metadata()

    def _daemon_packaging_status_payload() -> dict[str, object]:
        from sayane.app import build_daemon_packaging_status

        return build_daemon_packaging_status(
            cfg.home / "run",
            host=cfg.host,
            port=cfg.port,
        ).public_metadata()

    def _daemon_service_targets_status_payload() -> dict[str, object]:
        from sayane.app import build_daemon_service_targets_status

        return build_daemon_service_targets_status(
            cfg.home / "run",
            host=cfg.host,
            port=cfg.port,
        ).public_metadata()

    def _daemon_service_control_boundary_payload() -> dict[str, object]:
        from sayane.app import build_daemon_service_control_boundary

        return build_daemon_service_control_boundary(
            cfg.home / "run",
            host=cfg.host,
            port=cfg.port,
        ).public_metadata()

    def _daemon_supervision_status_payload() -> dict[str, object]:
        from sayane.app import build_daemon_supervision_status

        return build_daemon_supervision_status(
            cfg.home / "run",
            host=cfg.host,
            port=cfg.port,
        ).public_metadata()

    def _daemon_recovery_consent_status_payload() -> dict[str, object]:
        from sayane.app import build_daemon_recovery_consent_status

        return build_daemon_recovery_consent_status(
            cfg.home / "run",
            host=cfg.host,
            port=cfg.port,
        ).public_metadata()

    def _daemon_preflight_payload() -> dict[str, object]:
        from sayane.app import build_implementation_gate_preflight_report, build_preflight_event_record

        report = build_implementation_gate_preflight_report()
        payload = report.public_metadata()
        payload["event_record"] = build_preflight_event_record(report).public_metadata()
        return payload

    def _redirect_url(path: str, *, notice: str | None = None, error: str | None = None) -> str:
        query = urlencode({k: v for k, v in {"notice": notice, "error": error}.items() if v})
        return f"{path}?{query}" if query else path

    def _resolve_ui_locale(request: Request) -> str:
        from sayane.bridge.resident_app_html import normalize_bootstrap_locale

        requested_locale = request.query_params.get("locale")
        if requested_locale:
            return normalize_bootstrap_locale(requested_locale)
        cookie_locale = request.cookies.get(ui_locale_cookie_name)
        if cookie_locale:
            return normalize_bootstrap_locale(cookie_locale)
        return normalize_bootstrap_locale(request.headers.get("accept-language"))

    def _translated_feedback(
        *,
        locale: str,
        notice: str | None = None,
        error: str | None = None,
    ) -> tuple[str | None, str | None]:
        from sayane.bridge.resident_app_html import translate_bootstrap_feedback

        return (
            translate_bootstrap_feedback(notice, locale),
            translate_bootstrap_feedback(error, locale),
        )

    def _set_ui_cookie(
        response: HTMLResponse | RedirectResponse,
        token: str,
        *,
        locale: str,
    ) -> None:
        response.set_cookie(
            ui_cookie_name,
            token,
            httponly=True,
            samesite="strict",
            max_age=cfg.ui_session_ttl_seconds,
        )
        response.set_cookie(ui_locale_cookie_name, locale, httponly=False, samesite="strict")

    def _clear_ui_cookies(response: JSONResponse | RedirectResponse) -> None:
        response.delete_cookie(ui_cookie_name)
        response.delete_cookie(ui_locale_cookie_name)

    def _html_response(content: str, *, token: str, locale: str) -> HTMLResponse:
        response = HTMLResponse(content=content)
        _set_ui_cookie(response, token, locale=locale)
        return response

    def _redirect_response(
        path: str,
        *,
        token: str,
        locale: str,
        notice: str | None = None,
        error: str | None = None,
    ) -> RedirectResponse:
        response = RedirectResponse(
            url=_redirect_url(path, notice=notice, error=error),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        _set_ui_cookie(response, token, locale=locale)
        return response

    def _valid_ui_session_cookie(request: Request) -> str | None:
        cookie_token = request.cookies.get(ui_cookie_name)
        if cookie_token and verify_ui_session(cfg, cookie_token):
            return cookie_token
        return None

    def _valid_bootstrap_bearer(request: Request) -> str | None:
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()
            if verify_token(cfg, token):
                return token
        return None

    def _valid_bootstrap_query_token(request: Request) -> str | None:
        token = request.query_params.get("bootstrap_token")
        if token and verify_token(cfg, token):
            return token
        return None

    def _valid_bootstrap_token(token: str | None) -> str | None:
        if token and verify_token(cfg, token):
            return token
        return None

    def establish_ui_session(request: Request) -> str:
        existing = _valid_ui_session_cookie(request)
        bootstrap_bearer = _valid_bootstrap_bearer(request)
        bootstrap_query = _valid_bootstrap_query_token(request)
        if bootstrap_bearer or bootstrap_query:
            return issue_ui_session(cfg)
        if existing:
            return existing
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bootstrap bearer or valid resident app UI session",
        )

    def require_ui_session(request: Request) -> str:
        cookie_token = _valid_ui_session_cookie(request)
        if cookie_token:
            return cookie_token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid resident app UI session",
        )

    @router.get(
        "/app/contract",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_contract() -> dict[str, object]:
        from sayane.app.app_contract import build_app_contract

        return build_app_contract()

    @router.get(
        "/app/overview",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_overview() -> dict[str, object]:
        from sayane.app.app_overview import build_app_overview
        from sayane.app.runtime import build_resident_runtime

        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
        )
        return build_app_overview(runtime)

    @router.get(
        "/app/screen-state/home",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_home_screen_state() -> dict[str, object]:
        from sayane.app import build_app_overview, build_home_screen_state, build_resident_runtime

        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
        )
        return build_home_screen_state(build_app_overview(runtime))

    @router.get(
        "/app/operator-phase-status",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_operator_phase_status() -> dict[str, object]:
        return _operator_phase_status_payload()

    @router.get(
        "/app/daemon-packaging-status",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_packaging_status() -> dict[str, object]:
        return _daemon_packaging_status_payload()

    @router.get(
        "/app/daemon-service-targets-status",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_service_targets_status() -> dict[str, object]:
        return _daemon_service_targets_status_payload()

    @router.get(
        "/app/daemon-service-control-boundary",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_service_control_boundary() -> dict[str, object]:
        return _daemon_service_control_boundary_payload()

    @router.get(
        "/app/daemon-supervision-status",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_supervision_status() -> dict[str, object]:
        return _daemon_supervision_status_payload()

    @router.get(
        "/app/daemon-recovery-consent-status",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_recovery_consent_status() -> dict[str, object]:
        return _daemon_recovery_consent_status_payload()

    @router.get(
        "/app/daemon-preflight",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_preflight() -> dict[str, object]:
        return _daemon_preflight_payload()

    @router.get(
        "/app/ui",
        response_class=HTMLResponse,
    )
    def get_app_ui(
        request: Request,
        token: str = Depends(establish_ui_session),
    ) -> HTMLResponse:
        from sayane.app.app_contract import build_app_contract
        from sayane.app.app_overview import build_app_overview
        from sayane.app.runtime import build_resident_runtime
        from sayane.bridge.resident_app_html import render_resident_app_home

        locale = _resolve_ui_locale(request)
        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
        )
        notice, error = _translated_feedback(
            locale=locale,
            notice=request.query_params.get("notice"),
            error=request.query_params.get("error"),
        )
        html = render_resident_app_home(
            build_app_contract(),
            build_app_overview(runtime),
            locale=locale,
            notice=notice,
            error=error,
        )
        return _html_response(html, token=token, locale=locale)

    @router.post("/app/ui/bootstrap")
    def post_app_ui_bootstrap(
        request: Request,
        bootstrap_token: str = Form(...),
    ) -> RedirectResponse:
        if not _valid_bootstrap_token(bootstrap_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            )
        locale = _resolve_ui_locale(request)
        token = issue_ui_session(cfg)
        return _redirect_response("/app/ui", token=token, locale=locale)

    @router.post("/app/ui-action/session/logout")
    def post_app_ui_action_session_logout(
        _token: str = Depends(require_ui_session),
    ) -> JSONResponse:
        clear_ui_session(cfg)
        response = JSONResponse({"status": "logged_out"})
        _clear_ui_cookies(response)
        return response

    @router.get("/app/ui-state/contract")
    def get_app_ui_contract_state(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        from sayane.app.app_contract import build_app_contract

        return build_app_contract()

    @router.get("/app/ui-state/home")
    def get_app_ui_home_state(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        from sayane.app import build_app_overview, build_home_screen_state, build_resident_runtime

        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
        )
        return build_home_screen_state(build_app_overview(runtime))

    @router.get("/app/ui-state/operator-phase-status")
    def get_app_ui_operator_phase_status(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _operator_phase_status_payload()

    @router.get("/app/ui-state/daemon-packaging-status")
    def get_app_ui_daemon_packaging_status(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_packaging_status_payload()

    @router.get("/app/ui-state/daemon-service-targets-status")
    def get_app_ui_daemon_service_targets_status(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_service_targets_status_payload()

    @router.get("/app/ui-state/daemon-service-control-boundary")
    def get_app_ui_daemon_service_control_boundary(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_service_control_boundary_payload()

    @router.get("/app/ui-state/daemon-supervision-status")
    def get_app_ui_daemon_supervision_status(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_supervision_status_payload()

    @router.get("/app/ui-state/daemon-recovery-consent-status")
    def get_app_ui_daemon_recovery_consent_status(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_recovery_consent_status_payload()

    @router.get("/app/ui-state/daemon-preflight")
    def get_app_ui_daemon_preflight(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_preflight_payload()

    @router.get("/app/ui-state/candidates")
    def get_app_ui_candidate_queue_state(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        from sayane.app import build_candidate_queue_screen_state

        return build_candidate_queue_screen_state(_reviewable_candidate_queue())

    @router.get("/app/ui-state/candidates/{candidate_id}")
    def get_app_ui_candidate_detail_state(
        candidate_id: str,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            return _candidate_detail_screen_state(candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/app/ui-state/candidates/{candidate_id}/diff")
    def get_app_ui_candidate_diff_state(
        candidate_id: str,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            return _candidate_diff_payload(candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/app/ui-state/candidates/{candidate_id}/lineage")
    def get_app_ui_candidate_lineage_state(
        candidate_id: str,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            return candidate_api.get_candidate_lineage(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/app/ui-state/daemon")
    def get_app_ui_daemon_state(
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        return _daemon_panel_screen_state()

    @router.get(
        "/app/ui/candidates",
        response_class=HTMLResponse,
    )
    def get_app_ui_candidates(
        request: Request,
        token: str = Depends(require_ui_session),
    ) -> HTMLResponse:
        from sayane.bridge.resident_app_html import render_resident_app_candidate_queue

        locale = _resolve_ui_locale(request)
        notice, error = _translated_feedback(
            locale=locale,
            notice=request.query_params.get("notice"),
            error=request.query_params.get("error"),
        )
        html = render_resident_app_candidate_queue(
            _reviewable_candidate_queue(),
            locale=locale,
            notice=notice,
            error=error,
        )
        return _html_response(html, token=token, locale=locale)

    @router.get(
        "/app/ui/candidates/{candidate_id}",
        response_class=HTMLResponse,
    )
    def get_app_ui_candidate_detail(
        candidate_id: str,
        request: Request,
        token: str = Depends(require_ui_session),
    ) -> HTMLResponse:
        from sayane.bridge.resident_app_html import render_resident_app_candidate_detail

        try:
            locale = _resolve_ui_locale(request)
            notice, error = _translated_feedback(
                locale=locale,
                notice=request.query_params.get("notice"),
                error=request.query_params.get("error"),
            )
            payload = _candidate_detail_payload(candidate_id)
            html = render_resident_app_candidate_detail(
                payload,
                diff_path=f"/app/ui/candidates/{candidate_id}/diff",
                locale=locale,
                notice=notice,
                error=error,
            )
            return _html_response(html, token=token, locale=locale)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/app/ui/candidates/{candidate_id}/diff",
        response_class=HTMLResponse,
    )
    def get_app_ui_candidate_diff(
        candidate_id: str,
        request: Request,
        token: str = Depends(require_ui_session),
    ) -> HTMLResponse:
        from sayane.bridge.resident_app_html import render_resident_app_candidate_diff

        try:
            locale = _resolve_ui_locale(request)
            notice, error = _translated_feedback(
                locale=locale,
                notice=request.query_params.get("notice"),
                error=request.query_params.get("error"),
            )
            payload = _candidate_diff_payload(candidate_id)
            html = render_resident_app_candidate_diff(
                candidate_id,
                payload,
                locale=locale,
                notice=notice,
                error=error,
            )
            return _html_response(html, token=token, locale=locale)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/app/ui/daemon",
        response_class=HTMLResponse,
    )
    def get_app_ui_daemon_panel(
        request: Request,
        token: str = Depends(require_ui_session),
    ) -> HTMLResponse:
        from sayane.bridge.resident_app_html import render_resident_app_daemon_panel

        locale = _resolve_ui_locale(request)
        notice, error = _translated_feedback(
            locale=locale,
            notice=request.query_params.get("notice"),
            error=request.query_params.get("error"),
        )
        payload = _daemon_overview_payload(host=cfg.host, port=cfg.port)
        return _html_response(
            render_resident_app_daemon_panel(
                payload,
                locale=locale,
                notice=notice,
                error=error,
            ),
            token=token,
            locale=locale,
        )

    @router.post("/app/ui/capture-clipboard")
    def post_app_ui_capture_clipboard(
        request: Request,
        content: str = Form(...),
        profile_id: str = Form("default"),
        locale: str | None = Form(None),
        token: str = Depends(require_ui_session),
    ) -> RedirectResponse:
        from sayane.app.runtime import build_resident_runtime

        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
            profile_id=profile_id,
        )
        resolved_locale = locale or _resolve_ui_locale(request)
        candidate = runtime.service.capture_clipboard_as_candidate(
            content,
            capability=runtime.capabilities["capture"],
            config=cfg,
            locale=resolved_locale,
        )
        return _redirect_response(
            f"/app/ui/candidates/{candidate.id}",
            token=token,
            locale=resolved_locale,
            notice="Pending candidate created from clipboard.",
        )

    @router.post("/app/ui-action/capture-clipboard")
    def post_app_ui_action_capture_clipboard(
        request: Request,
        body: AppCaptureClipboardRequest,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        from sayane.app.runtime import build_resident_runtime

        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
            profile_id=body.profile_id,
        )
        candidate = runtime.service.capture_clipboard_as_candidate(
            body.content,
            capability=runtime.capabilities["capture"],
            config=cfg,
            locale=body.locale or _resolve_ui_locale(request),
        )
        payload = candidate.model_dump(mode="json")
        payload["capture_surface"] = "resident_app_bridge"
        return payload

    @router.post("/app/ui/candidates/{candidate_id}/evaluate")
    def post_app_ui_candidate_evaluate(
        candidate_id: str,
        request: Request,
        level: int = Form(1),
        token: str = Depends(require_ui_session),
    ) -> RedirectResponse:
        locale = _resolve_ui_locale(request)
        try:
            candidate_api.post_evaluate(cfg, candidate_id, level=level)
        except FileNotFoundError as exc:
            return _redirect_response("/app/ui/candidates", token=token, locale=locale, error=str(exc))
        except CandidateOperationError as exc:
            return _redirect_response(
                f"/app/ui/candidates/{candidate_id}",
                token=token,
                locale=locale,
                error=str(exc),
            )
        return _redirect_response(
            f"/app/ui/candidates/{candidate_id}",
            token=token,
            locale=locale,
            notice="Candidate evaluated.",
        )

    @router.post("/app/ui-action/candidates/{candidate_id}/evaluate")
    def post_app_ui_action_candidate_evaluate(
        candidate_id: str,
        body: EvaluateCandidateRequest,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            payload = candidate_api.post_evaluate(cfg, candidate_id, level=body.level)
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(status_code=400, detail=exc.to_payload()) from exc

    @router.post("/app/ui/candidates/{candidate_id}/approve")
    def post_app_ui_candidate_approve(
        candidate_id: str,
        request: Request,
        force_critical: str | None = Form(None),
        override_reason: str | None = Form(None),
        token: str = Depends(require_ui_session),
    ) -> RedirectResponse:
        locale = _resolve_ui_locale(request)
        try:
            candidate_api.post_approve(
                cfg,
                candidate_id,
                force_critical=force_critical == "true",
                override_reason=override_reason or None,
            )
        except FileNotFoundError as exc:
            return _redirect_response("/app/ui/candidates", token=token, locale=locale, error=str(exc))
        except CandidateOperationError as exc:
            return _redirect_response(
                f"/app/ui/candidates/{candidate_id}",
                token=token,
                locale=locale,
                error=str(exc),
            )
        except ValueError as exc:
            return _redirect_response(
                f"/app/ui/candidates/{candidate_id}",
                token=token,
                locale=locale,
                error=str(exc),
            )
        return _redirect_response("/app/ui/candidates", token=token, locale=locale, notice="Candidate approved.")

    @router.post("/app/ui-action/candidates/{candidate_id}/approve")
    def post_app_ui_action_candidate_approve(
        candidate_id: str,
        body: ApproveCandidateRequest,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            explicit = (
                body.explicit_confirmation.model_dump(mode="json")
                if body.explicit_confirmation
                else None
            )
            payload = candidate_api.post_approve(
                cfg,
                candidate_id,
                force_critical=body.force_critical,
                override_reason=body.override_reason,
                explicit_confirmation=explicit,
            )
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(status_code=400, detail=exc.to_payload()) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/app/ui/candidates/{candidate_id}/reject")
    def post_app_ui_candidate_reject(
        candidate_id: str,
        request: Request,
        reason: str | None = Form(None),
        token: str = Depends(require_ui_session),
    ) -> RedirectResponse:
        locale = _resolve_ui_locale(request)
        try:
            candidate_api.post_reject(cfg, candidate_id, reason=reason or None)
        except FileNotFoundError as exc:
            return _redirect_response("/app/ui/candidates", token=token, locale=locale, error=str(exc))
        except CandidateOperationError as exc:
            return _redirect_response(
                f"/app/ui/candidates/{candidate_id}",
                token=token,
                locale=locale,
                error=str(exc),
            )
        return _redirect_response("/app/ui/candidates", token=token, locale=locale, notice="Candidate rejected.")

    @router.post("/app/ui-action/candidates/{candidate_id}/reject")
    def post_app_ui_action_candidate_reject(
        candidate_id: str,
        body: RejectCandidateRequest,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            payload = candidate_api.post_reject(cfg, candidate_id, reason=body.reason)
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(status_code=400, detail=exc.to_payload()) from exc

    @router.post("/app/ui/candidates/{candidate_id}/revise")
    def post_app_ui_candidate_revise(
        candidate_id: str,
        request: Request,
        edited_text: str = Form(...),
        target_section: str | None = Form(None),
        change_reason: str | None = Form(None),
        token: str = Depends(require_ui_session),
    ) -> RedirectResponse:
        locale = _resolve_ui_locale(request)
        try:
            payload = candidate_api.post_revise(
                cfg,
                candidate_id,
                edited_text=edited_text,
                target_section=target_section or None,
                change_reason=change_reason or None,
            )
        except FileNotFoundError as exc:
            return _redirect_response("/app/ui/candidates", token=token, locale=locale, error=str(exc))
        return _redirect_response(
            f"/app/ui/candidates/{payload['id']}",
            token=token,
            locale=locale,
            notice="Revised candidate created.",
        )

    @router.post("/app/ui-action/candidates/{candidate_id}/revise")
    def post_app_ui_action_candidate_revise(
        candidate_id: str,
        body: ReviseCandidateRequest,
        _token: str = Depends(require_ui_session),
    ) -> dict[str, object]:
        try:
            payload = candidate_api.post_revise(
                cfg,
                candidate_id,
                edited_text=body.edited_text,
                target_section=body.target_section,
                change_reason=body.change_reason,
            )
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post(
        "/app/capture-clipboard",
        dependencies=[Depends(require_bearer)],
    )
    def post_capture_clipboard(body: AppCaptureClipboardRequest) -> dict[str, object]:
        from sayane.app.runtime import build_resident_runtime

        runtime = build_resident_runtime(
            home=cfg.home,
            host=cfg.host,
            port=cfg.port,
            profile_id=body.profile_id,
        )
        candidate = runtime.service.capture_clipboard_as_candidate(
            body.content,
            capability=runtime.capabilities["capture"],
            config=cfg,
            locale=body.locale,
        )
        payload = candidate.model_dump(mode="json")
        payload["capture_surface"] = "resident_app_bridge"
        return payload

    @router.get(
        "/app/candidates",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_candidates() -> dict[str, object]:
        return _reviewable_candidate_queue()

    @router.get(
        "/app/screen-state/candidates",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_candidate_queue_screen_state() -> dict[str, object]:
        from sayane.app import build_candidate_queue_screen_state

        return build_candidate_queue_screen_state(_reviewable_candidate_queue())

    @router.get(
        "/app/candidates/{candidate_id}",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_candidate(candidate_id: str) -> dict[str, object]:
        try:
            return _candidate_detail_payload(candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/app/screen-state/candidates/{candidate_id}",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_candidate_detail_screen_state(candidate_id: str) -> dict[str, object]:
        try:
            return _candidate_detail_screen_state(candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/app/candidates/{candidate_id}/diff",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_candidate_diff(candidate_id: str) -> dict[str, object]:
        try:
            return _candidate_diff_payload(candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/app/candidates/{candidate_id}/lineage",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_candidate_lineage(candidate_id: str) -> dict[str, object]:
        try:
            return candidate_api.get_candidate_lineage(cfg, candidate_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post(
        "/app/candidates/{candidate_id}/evaluate",
        dependencies=[Depends(require_bearer)],
    )
    def post_app_candidate_evaluate(
        candidate_id: str,
        body: EvaluateCandidateRequest,
    ) -> dict[str, object]:
        try:
            payload = candidate_api.post_evaluate(cfg, candidate_id, level=body.level)
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(status_code=400, detail=exc.to_payload()) from exc

    @router.post(
        "/app/candidates/{candidate_id}/approve",
        dependencies=[Depends(require_bearer)],
    )
    def post_app_candidate_approve(
        candidate_id: str,
        body: ApproveCandidateRequest,
    ) -> dict[str, object]:
        try:
            explicit = (
                body.explicit_confirmation.model_dump(mode="json")
                if body.explicit_confirmation
                else None
            )
            payload = candidate_api.post_approve(
                cfg,
                candidate_id,
                force_critical=body.force_critical,
                override_reason=body.override_reason,
                explicit_confirmation=explicit,
            )
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(status_code=400, detail=exc.to_payload()) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post(
        "/app/candidates/{candidate_id}/reject",
        dependencies=[Depends(require_bearer)],
    )
    def post_app_candidate_reject(
        candidate_id: str,
        body: RejectCandidateRequest,
    ) -> dict[str, object]:
        try:
            payload = candidate_api.post_reject(cfg, candidate_id, reason=body.reason)
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except CandidateOperationError as exc:
            raise HTTPException(status_code=400, detail=exc.to_payload()) from exc

    @router.post(
        "/app/candidates/{candidate_id}/revise",
        dependencies=[Depends(require_bearer)],
    )
    def post_app_candidate_revise(
        candidate_id: str,
        body: ReviseCandidateRequest,
    ) -> dict[str, object]:
        try:
            payload = candidate_api.post_revise(
                cfg,
                candidate_id,
                edited_text=body.edited_text,
                target_section=body.target_section,
                change_reason=body.change_reason,
            )
            payload["review_surface"] = "resident_app_bridge"
            return payload
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get(
        "/app/daemon-overview",
        dependencies=[Depends(require_bearer)],
    )
    def get_daemon_overview(
        host: str = "127.0.0.1",
        port: int = 38741,
    ) -> dict[str, object]:
        return _daemon_overview_payload(host=host, port=port)

    @router.get(
        "/app/screen-state/daemon",
        dependencies=[Depends(require_bearer)],
    )
    def get_app_daemon_panel_screen_state() -> dict[str, object]:
        return _daemon_panel_screen_state()

    app.include_router(router)
