"""Import portable context bundles as reviewable Candidates (#143).

Import must not directly merge into canonical context.
The safe flow is: parse → diff → generate Candidates → review → approve.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from sayane.core.candidate import (
    CandidateProposal,
    CandidateSource,
    CandidateStoragePolicy,
    CandidateUpdate,
    CaptureMetadata,
)
from sayane.core.models import SayaneProfile
from sayane.core.export import SCOPE_SECTIONS

# --- Import metadata ---


class ImportMetadata:
    """Metadata attached to each imported candidate for lineage tracking."""

    def __init__(
        self,
        import_id: str,
        source_path: str | None = None,
        source_format: str = "yaml",
        source_target: str | None = None,
        source_scopes: list[str] | None = None,
    ) -> None:
        self.import_id = import_id
        self.source_path = source_path
        self.source_format = source_format
        self.source_target = source_target
        self.source_scopes = source_scopes or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "source_path": self.source_path,
            "source_format": self.source_format,
            "source_target": self.source_target,
            "source_scopes": self.source_scopes,
            "imported_at": datetime.now(UTC).isoformat(),
        }


# --- Bundle parsing ---

def parse_bundle(path: Path) -> dict[str, Any] | None:
    """Parse a portable context bundle (YAML, JSON, or Markdown)."""
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()

    if stripped.startswith("{"):
        return json.loads(text)

    # YAML: try first, since YAML comments start with #
    try:
        parsed = yaml.safe_load(text)
        if isinstance(parsed, dict) and parsed:
            return parsed
    except yaml.YAMLError:
        pass

    # Markdown: parse sections if not YAML
    if stripped.startswith("# "):
        return _parse_markdown_bundle(text)

    return None


def _parse_markdown_bundle(text: str) -> dict[str, Any]:
    """Extract key-value pairs from markdown sections for import."""
    result: dict[str, Any] = {}
    current_section: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped[3:].strip().lower()
            continue
        if stripped.startswith("- ") and current_section:
            value = stripped[2:].strip()
            if current_section == "identity":
                if "identity" not in result:
                    result["identity"] = {}
                if value.startswith("Name: "):
                    result["identity"]["name"] = value[6:]
                elif value.startswith("Preferred name: "):
                    result["identity"]["preferred_name"] = value[16:]
                elif value.startswith("Roles: "):
                    result["identity"]["roles"] = [r.strip() for r in value[7:].split(",")]
            elif current_section in ("key concepts", "important terms"):
                key = "knowledge" if current_section == "key concepts" else "important_terms"
                result.setdefault(key, []).append(value)
    return result


_IMPORTABLE_SECTIONS = frozenset({
    "identity",
    "voice",
    "communication_mode",
    "values",
    "knowledge",
    "policy",
    "major_projects",
    "important_terms",
    # A2 round-trip extended sections
    "interaction",
    "writing",
    "technical",
    "principles",
    "execution_context",
})

# --- Import hygiene: placeholder / empty detection (#156) ---

_PLACEHOLDER_IDENTITY_VALUES: frozenset[str] = frozenset({
    "example user",
    "example",
    "developer",
    "test user",
    "sample user",
    "test",
    "sample",
})


def _is_placeholder_value(value: object) -> bool:
    """Check if a string value is a known placeholder/fixture value."""
    if not isinstance(value, str):
        return False
    return value.strip().lower() in _PLACEHOLDER_IDENTITY_VALUES


def _contains_placeholder_identity(proposed: dict[str, Any]) -> bool:
    """Check if identity dict contains only placeholder values."""
    name = proposed.get("name", "")
    preferred = proposed.get("preferred_name", "")
    if _is_placeholder_value(name) or _is_placeholder_value(preferred):
        return True
    roles = proposed.get("roles", [])
    if roles and all(_is_placeholder_value(r) for r in roles if isinstance(r, str)):
        return True
    return False


def _is_empty_proposal(value: object) -> bool:
    """Check if a proposed value is empty and should be skipped."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, dict) and not value:
        return True
    if isinstance(value, list) and not value:
        return True
    return False


def import_bundle_as_candidates(
    bundle: dict[str, Any],
    profile: SayaneProfile,
) -> list[dict[str, Any]]:
    """Compare bundle sections against stored profile and return candidate drafts.

    Each returned dict has:
    - section: target profile section
    - current_value: value from profile (None if new)
    - proposed_value: value from bundle
    - action: 'add' | 'update' | 'skipped_placeholder' | 'skipped_empty'

    Placeholder identity values and empty proposals are skipped (#156).
    """
    candidates: list[dict[str, Any]] = []
    profile_dict = profile.model_dump(mode="json")

    for key in bundle:
        if key not in _IMPORTABLE_SECTIONS:
            continue
        proposed = bundle[key]
        existing = profile_dict.get(key)

        # Skip empty proposals (#156)
        if _is_empty_proposal(proposed):
            continue

        # Skip placeholder identity updates (#156)
        if key == "identity" and isinstance(proposed, dict) and _contains_placeholder_identity(proposed):
            continue

        if existing is None and proposed:
            candidates.append({
                "section": key,
                "current_value": None,
                "proposed_value": proposed,
                "action": "add",
            })
        elif isinstance(existing, list) and isinstance(proposed, list):
            # List sections: diff
            existing_set = {str(v).strip().lower() if isinstance(v, str) else str(v) for v in existing}
            add = [v for v in proposed if str(v).strip().lower() not in existing_set]
            if add:
                candidates.append({
                    "section": key,
                    "current_value": existing,
                    "proposed_value": add,
                    "action": "add",
                })
        elif isinstance(existing, dict) and isinstance(proposed, dict):
            # Dict sections: merge check
            diff: dict[str, Any] = {}
            for k, v in proposed.items():
                if k not in existing or existing[k] != v:
                    diff[k] = v
            if diff:
                candidates.append({
                    "section": key,
                    "current_value": existing,
                    "proposed_value": diff,
                    "action": "update",
                })
        elif existing != proposed:
            candidates.append({
                "section": key,
                "current_value": existing,
                "proposed_value": proposed,
                "action": "update",
            })

    return candidates


# --- Candidate creation from import ---


def create_import_candidates(
    bundle: dict[str, Any],
    profile: SayaneProfile,
    *,
    import_meta: ImportMetadata,
    target_profile_id: str = "default",
) -> list[CandidateUpdate]:
    """Generate CandidateUpdate records from an imported bundle.

    Each candidate is saved with import metadata and storage policy.
    Does NOT merge into profile — only creates pending candidates.
    """
    drafts = import_bundle_as_candidates(bundle, profile)
    candidates: list[CandidateUpdate] = []
    now = datetime.now(UTC)

    for draft in drafts:
        section = draft["section"]
        proposed = draft["proposed_value"]
        content = json.dumps(proposed, ensure_ascii=False)
        proposal = CandidateProposal(
            section=section,
            operation="bundle_imported",
            add=[],
            items=[{"section": section, "name": k, "value": str(v)}
                   for k, v in (proposed.items() if isinstance(proposed, dict) else {})]
            if isinstance(proposed, dict)
            else [{"section": section, "name": str(v)} for v in (proposed if isinstance(proposed, list) else [proposed])],
            summary=f"Imported from {import_meta.source_path or 'bundle'}: {section}",
        )
        candidate = CandidateUpdate(
            id=uuid4().hex,
            status="pending",
            target_profile_id=target_profile_id,
            content=content,
            raw_capture=content,
            cleaned_capture=content,
            display_summary=f"[Import] {section}: {draft['action']}",
            source=CandidateSource(
                type=f"bundle_import/{import_meta.source_format}",
                uri=import_meta.source_path,
                captured_at=now,
            ),
            proposal=proposal,
            storage_policy=CandidateStoragePolicy(
                storage_kind="profile_ir",
                target_path=section,
                prompt_export=_infer_prompt_export(section),
                sensitivity=_infer_sensitivity(section),
            ),
            parent_capture_id=import_meta.import_id,
            generator_id="sayane.bundle_import",
        )
        candidates.append(candidate)

    return candidates


def _infer_prompt_export(section: str) -> str:
    if section in ("identity.contact",):
        return "never"
    if section in ("major_projects", "execution_context", "knowledge"):
        return "on_demand"
    return "default"


def _infer_sensitivity(section: str) -> str:
    if section in ("identity.contact",):
        return "private"
    if section in ("values", "policy"):
        return "internal"
    return "internal"


def import_bundle_with_semantic_review(
    bundle: dict[str, Any],
    profile: SayaneProfile,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Import bundle as candidates and run semantic review pass (Phase 6).

    Returns (candidates, review_result) where review_result contains
    per-candidate flags/warnings and cross-candidate overlap warnings.
    Does NOT auto-approve, auto-reject, or modify candidates.
    """
    from sayane.core.semantic_review import run_semantic_review

    candidates = import_bundle_as_candidates(bundle, profile)
    review = run_semantic_review(candidates)

    review_dict = {
        "candidate_flags": review.candidate_flags,
        "candidate_warnings": review.candidate_warnings,
        "overlap_warnings": review.overlap_warnings,
    }
    return candidates, review_dict
