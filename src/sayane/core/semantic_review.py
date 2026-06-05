"""Semantic Review Layer for import candidates (Phase 6).

This is a post-process review pass that runs after candidate generation.
It does NOT auto-approve, auto-reject, or modify candidates.
It adds metadata: flags, warnings, overlap groups to assist human review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# --- Known Concept Hint Registry ---
#
# This is a review hint registry, NOT a source of truth.
# Hints suggest preferred/discouraged semantic placement.
# Automatic approval or rejection based on hints is forbidden.

@dataclass
class KnownConcept:
    term: str
    preferred_sections: list[str]
    discouraged_sections: list[str]
    warning_type: str = "unstable_placement"
    source_authority: str = "hint_only"


KNOWN_CONCEPTS: dict[str, KnownConcept] = {
    "rde": KnownConcept(
        term="RDE",
        preferred_sections=["principles", "evaluation_policy", "audit_methodology"],
        discouraged_sections=["technical", "technical.preferences", "casual_preferences"],
        warning_type="unstable_placement",
    ),
    "sayane": KnownConcept(
        term="Sayane",
        preferred_sections=["projects", "systems", "context_portability", "candidate_review"],
        discouraged_sections=["technical.preferences", "assistant_identity", "personality"],
        warning_type="unstable_placement",
    ),
    "context portability": KnownConcept(
        term="Context Portability",
        preferred_sections=["principles", "systems", "workflow"],
        discouraged_sections=["personality", "memory"],
        warning_type="boundary_sensitive",
    ),
    "δm": KnownConcept(
        term="ΔM",
        preferred_sections=["principles", "evaluation_policy", "audit_methodology"],
        discouraged_sections=["technical.preferences", "casual_preferences"],
        warning_type="unstable_placement",
    ),
    "kotone": KnownConcept(
        term="Kotone",
        preferred_sections=["projects", "systems", "design"],
        discouraged_sections=["assistant_identity", "personality", "memory"],
        warning_type="boundary_sensitive",
    ),
    "candidate review": KnownConcept(
        term="Candidate Review",
        preferred_sections=["principles", "workflow", "evaluation_policy"],
        discouraged_sections=["technical.preferences", "casual_preferences"],
        warning_type="boundary_sensitive",
    ),
}


# --- Token extraction ---

def _extract_tokens(value: Any, path: str = "") -> list[tuple[str, str]]:
    """Extract normalized comparable tokens from a candidate value.

    Returns list of (token, context_path) tuples.
    Token is lowercased and stripped.
    """
    tokens: list[tuple[str, str]] = []
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped:
            tokens.append((stripped, path))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            sub_path = f"{path}[{i}]" if path else f"[{i}]"
            tokens.extend(_extract_tokens(item, sub_path))
    elif isinstance(value, dict):
        for k, v in value.items():
            sub_path = f"{path}.{k}" if path else k
            tokens.extend(_extract_tokens(v, sub_path))
    return tokens


def extract_candidate_tokens(proposed: dict[str, Any] | list | str | None) -> list[tuple[str, str]]:
    """Extract tokens from a candidate's proposed value."""
    if proposed is None:
        return []
    return _extract_tokens(proposed)


# --- Duplicate concept detection ---

@dataclass
class OverlapWarning:
    type: str = "duplicate_concept"
    severity: str = "review_required"
    terms: list[str] = field(default_factory=list)
    candidate_indices: list[int] = field(default_factory=list)
    note: str = ""


def detect_concept_overlaps(candidates: list[dict[str, Any]]) -> list[OverlapWarning]:
    """Detect normalized tokens appearing in multiple candidates."""
    # Build term → candidate_index map
    term_to_candidates: dict[str, set[int]] = {}
    for i, c in enumerate(candidates):
        proposed = c.get("proposed_value")
        tokens = extract_candidate_tokens(proposed)
        for token, _path in tokens:
            if token not in term_to_candidates:
                term_to_candidates[token] = set()
            term_to_candidates[token].add(i)

    # Find terms appearing in multiple candidates
    overlaps: list[OverlapWarning] = []
    for term, indices in term_to_candidates.items():
        if len(indices) >= 2:
            overlaps.append(OverlapWarning(
                terms=[term],
                candidate_indices=sorted(indices),
                note=f"Same concept '{term}' appears in multiple sections. Review canonical placement before approval.",
            ))
    return overlaps


# --- Semantic placement analysis ---

@dataclass
class PlacementWarning:
    type: str = "unstable_placement"
    term: str = ""
    current_section: str = ""
    preferred_sections: list[str] = field(default_factory=list)
    message: str = ""


def analyze_semantic_placement(
    proposed: dict[str, Any] | list | str | None,
    section: str,
) -> list[PlacementWarning]:
    """Check if known concepts appear in discouraged sections."""
    warnings: list[PlacementWarning] = []
    tokens = extract_candidate_tokens(proposed)

    for token, _path in tokens:
        concept = KNOWN_CONCEPTS.get(token)
        if concept is None:
            continue

        # Check if current section is discouraged
        section_key = section.lower()
        is_discouraged = any(
            section_key == ds.lower() or section_key.startswith(ds.lower())
            for ds in concept.discouraged_sections
        )
        if not is_discouraged:
            continue

        warnings.append(PlacementWarning(
            type=concept.warning_type,
            term=concept.term,
            current_section=section,
            preferred_sections=concept.preferred_sections,
            message=f"{concept.term} may be flattened if imported as a generic {section}.",
        ))

    return warnings


# --- Identity boundary check ---

BOUNDARY_SENSITIVE_SECTIONS: frozenset[str] = frozenset({
    "assistant_identity",
    "personality",
    "memory",
    "assistant_name",
})

BOUNDARY_PROTECTED_TERMS: frozenset[str] = frozenset({
    "sayane",
    "claude",
    "chatgpt",
    "gemini",
    "deepseek",
})


def check_identity_boundary(
    proposed: dict[str, Any] | list | str | None,
    section: str,
) -> list[PlacementWarning]:
    """Warn if boundary-protected terms appear in identity-sensitive sections."""
    warnings: list[PlacementWarning] = []
    section_key = section.lower()

    if section_key not in BOUNDARY_SENSITIVE_SECTIONS:
        return warnings

    tokens = extract_candidate_tokens(proposed)
    for token, _path in tokens:
        if token in BOUNDARY_PROTECTED_TERMS:
            warnings.append(PlacementWarning(
                type="boundary_sensitive",
                term=token,
                current_section=section,
                preferred_sections=["projects", "systems", "context_portability"],
                message=f"'{token}' should not be placed in {section}. This is an external context system, not an assistant name or identity.",
            ))

    return warnings


# --- Full semantic review pass ---

@dataclass
class SemanticReviewResult:
    """Result of semantic review on import candidates."""

    # Per-candidate flags and warnings
    candidate_flags: list[list[str]] = field(default_factory=list)
    candidate_warnings: list[list[dict[str, Any]]] = field(default_factory=list)
    # Cross-candidate overlap warnings
    overlap_warnings: list[dict[str, Any]] = field(default_factory=list)


def run_semantic_review(candidates: list[dict[str, Any]]) -> SemanticReviewResult:
    """Run full semantic review pass. Does NOT modify candidates."""
    result = SemanticReviewResult()

    # Per-candidate analysis
    for i, c in enumerate(candidates):
        flags: list[str] = []
        pwarnings: list[dict[str, Any]] = []

        section = c.get("section", "")
        proposed = c.get("proposed_value")

        # Placement warnings
        placement = analyze_semantic_placement(proposed, section)
        if placement:
            flags.append("review_required")
            flags.append("unstable_placement")
            for w in placement:
                pwarnings.append({
                    "type": w.type,
                    "term": w.term,
                    "current_section": w.current_section,
                    "preferred_sections": w.preferred_sections,
                    "message": w.message,
                })

        # Identity boundary warnings
        identity = check_identity_boundary(proposed, section)
        if identity:
            flags.append("review_required")
            flags.append("boundary_sensitive")
            for w in identity:
                pwarnings.append({
                    "type": w.type,
                    "term": w.term,
                    "current_section": w.current_section,
                    "message": w.message,
                })

        result.candidate_flags.append(flags)
        result.candidate_warnings.append(pwarnings)

    # Cross-candidate overlap detection
    overlaps = detect_concept_overlaps(candidates)
    for ow in overlaps:
        result.overlap_warnings.append({
            "type": ow.type,
            "severity": ow.severity,
            "terms": ow.terms,
            "candidate_indices": ow.candidate_indices,
            "note": ow.note,
        })
        # Add semantic_overlap flag to affected candidates
        for idx in ow.candidate_indices:
            if idx < len(result.candidate_flags):
                fl = result.candidate_flags[idx]
                if "semantic_overlap" not in fl:
                    fl.append("semantic_overlap")
                if "review_required" not in fl:
                    fl.append("review_required")

    return result
