"""YAML / persona capture parsing and parse-failure handling.

This module is kept as a compatibility facade for callers that import public
capture parsing helpers from ``sayane.evaluators.capture_parse``.
"""

from __future__ import annotations

from typing import Any

from sayane.core.candidate import CandidateProposal, CaptureMetadata
from sayane.core.models import SayaneProfile
from sayane.evaluators.important_terms_classifier import (
    OPERATION_NO_EFFECTIVE,
    OPERATION_PARSE_FAILED,
    SECTION_REVIEW_REQUIRED,
    build_no_effective_proposal,
    build_parse_failed_proposal,
    classify_important_terms_yaml,
)
from sayane.evaluators.important_terms_fragment import (
    extract_important_terms_fragment,
    normalize_scalar,
)
from sayane.evaluators.persona_yaml_classifier import (
    classify_persona_yaml,
    collect_yaml_scalars,
    walk_profile_values,
)
from sayane.evaluators.yaml_detection import (
    PERSONA_ROOT_KEYS,
    detect_yaml_syntax_error,
    looks_like_yaml_capture,
    persona_document_keys,
    top_level_yaml_keys,
    try_parse_yaml,
)

# Backward-compatible aliases for older tests and internal imports.
_PERSONA_ROOT_KEYS = PERSONA_ROOT_KEYS
_normalize_scalar = normalize_scalar
_extract_important_terms_fragment = extract_important_terms_fragment
_walk_profile_values = walk_profile_values
_collect_yaml_scalars = collect_yaml_scalars


def build_proposal_for_yaml_content(
    content: str,
    profile: SayaneProfile | None,
    capture_meta: CaptureMetadata | None,
) -> CandidateProposal | None:
    """Build a CandidateProposal from YAML-like captured content.

    Returns ``None`` when the content should be handled by non-YAML capture
    proposal logic.
    """
    del capture_meta
    fragment_terms = extract_important_terms_fragment(content)
    if fragment_terms:
        return classify_important_terms_yaml({"important_terms": fragment_terms}, profile)
    if not looks_like_yaml_capture(content):
        return None
    parsed, err = try_parse_yaml(content)
    if err:
        return build_parse_failed_proposal(err)
    if not isinstance(parsed, dict):
        return build_parse_failed_proposal("YAML parse failed: root must be a mapping")
    keys = top_level_yaml_keys(parsed)
    if "important_terms" in keys and len(keys) == 1:
        return classify_important_terms_yaml(parsed, profile)
    if "persona" in keys or "person" in keys:
        return classify_persona_yaml(parsed, profile)
    return None


__all__ = [
    "SECTION_REVIEW_REQUIRED",
    "OPERATION_PARSE_FAILED",
    "OPERATION_NO_EFFECTIVE",
    "looks_like_yaml_capture",
    "detect_yaml_syntax_error",
    "try_parse_yaml",
    "top_level_yaml_keys",
    "persona_document_keys",
    "build_parse_failed_proposal",
    "build_no_effective_proposal",
    "classify_persona_yaml",
    "classify_important_terms_yaml",
    "build_proposal_for_yaml_content",
]
