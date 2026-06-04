"""Persist capture payloads as candidate updates (not profile merge)."""

import re
from typing import Literal

from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CaptureRequest, CaptureResponse
from sayane.bridge.service import resolve_profile_path
from sayane.core.candidate import CaptureMetadata
from sayane.core.loader import load_profile
from sayane.core.profile_quality import capture_content_warnings
from sayane.evaluators.list_diff import parse_yaml_list_section
from sayane.storage.candidates import create_from_capture

IMPORTANT_TERMS_CLIPBOARD_WARN_COUNT = 8


def _clipboard_scope_warnings(content: str, source_kind: str) -> list[str]:
    """Warn when clipboard likely contains a full persona document, not a partial edit."""
    if source_kind != "clipboard":
        return []
    text = content.strip()
    if not text:
        return []
    line_count = len(text.splitlines())
    has_persona_root = bool(re.search(r"(?m)^persona\s*:", text))
    has_terms_only = bool(re.search(r"(?m)^important_terms\s*:", text)) and not has_persona_root
    if has_terms_only:
        warnings: list[str] = []
        terms = parse_yaml_list_section(text, "important_terms")
        if len(terms) > IMPORTANT_TERMS_CLIPBOARD_WARN_COUNT:
            warnings.append("clipboard_many_important_terms")
        return warnings
    if has_persona_root and line_count > 35:
        return ["full_persona_document_detected"]
    return []


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

    for w in _clipboard_scope_warnings(request.content, source_kind):
        if w not in warnings:
            warnings.append(w)

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
    from sayane.lineage.record import record_lineage_event

    record_lineage_event(
        config,
        candidate.target_profile_id,
        operation="capture_created",
        node_kind="capture",
        actor="system",
        capture_id=candidate.id,
        candidate_id=candidate.id,
        source_url=candidate.source.uri,
        source_kind=source_kind,
        metadata={"section": candidate.proposal.section},
    )
    record_lineage_event(
        config,
        candidate.target_profile_id,
        operation="candidate_generated",
        node_kind="candidate",
        actor="bridge",
        capture_id=candidate.id,
        candidate_id=candidate.id,
        source_url=candidate.source.uri,
        source_kind=source_kind,
        metadata={"section": candidate.proposal.section},
    )
    candidate_path = config.candidates_dir / f"{candidate.id}.json"
    return CaptureResponse(
        id=candidate.id,
        path=str(candidate_path),
        warnings=warnings,
    )
