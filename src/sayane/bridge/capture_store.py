"""Persist capture payloads as candidate updates (not profile merge)."""

from typing import Literal

from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CaptureRequest, CaptureResponse
from sayane.bridge.service import resolve_profile_path
from sayane.core.candidate import CaptureMetadata
from sayane.core.loader import load_profile
from sayane.core.profile_quality import capture_content_warnings
from sayane.storage.candidates import create_from_capture


def save_capture(config: BridgeConfig, request: CaptureRequest) -> CaptureResponse:
    locale = request.locale
    if not locale:
        try:
            profile = load_profile(
                resolve_profile_path(config, request.profile_id),
            )
            locale = profile.voice.default_language
        except Exception:
            locale = None

    warnings = list(request.capture_warnings)
    if not request.section:
        warnings = warnings + capture_content_warnings(request.content)

    source_kind: Literal["selection", "clipboard", "page"] = "page"
    if request.capture_source in ("selection", "clipboard", "page"):
        source_kind = request.capture_source
    elif request.user_selected or (request.source or "").strip().lower() == "selection":
        source_kind = "selection"
    elif (request.source or "").strip().lower() == "clipboard":
        source_kind = "clipboard"

    capture_meta = CaptureMetadata(
        user_selected=request.user_selected or source_kind in ("selection", "clipboard"),
        capture_source=source_kind,
        capture_confidence=request.capture_confidence,
        requires_review=request.requires_review,
        capture_warnings=warnings,
        extractor=request.extractor,
    )

    candidate = create_from_capture(
        config,
        content=request.content,
        source_type=request.source or "capture",
        source_url=request.source_url,
        section=request.section,
        profile_id=request.profile_id,
        locale=locale,
        raw_content=request.raw_content,
        capture_meta=capture_meta,
    )
    candidate_path = config.candidates_dir / f"{candidate.id}.json"
    return CaptureResponse(
        id=candidate.id,
        path=str(candidate_path),
        warnings=warnings,
    )
