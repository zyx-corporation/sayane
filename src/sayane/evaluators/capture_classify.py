"""Classify capture lines into profile sections (heuristic)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from sayane.core.models import SayaneProfile

_ORG_RE = re.compile(
    r"(株式会社|有限会社|合同会社|Inc\.?|Corp\.?|LLC|Ltd\.?)",
    re.IGNORECASE,
)

CORE_CONCEPT_PATH = "core_concepts[].name"
ORGANIZATION_PATH = "organization.name"
MAJOR_PROJECT_PATH = "major_projects[].name"

_KNOWN_MAJOR_PROJECT_NAMES = frozenset(
    {
        "kotone",
        "kotonoha",
        "sayane",
        "kotomi",
        "awai commons",
        "openδm watch",
        "open\u0394m watch",
    },
)
_KNOWN_CORE_CONCEPT_NAMES = frozenset(
    {
        "rde",
        "δm",
        "制度詩学",
        "resonanceverse",
    },
)


@dataclass
class ClassifiedItem:
    section: str
    name: str
    summary: str | None = None
    path: str | None = None
    value: str | None = None


@dataclass
class ClassificationResult:
    items: list[ClassifiedItem] = field(default_factory=list)
    already_present: list[dict[str, str]] = field(default_factory=list)
    sections_seen: set[str] = field(default_factory=set)
    display_summary: str = ""

    @property
    def is_mixed(self) -> bool:
        return len(self.sections_seen) > 1

    def new_items(self) -> list[ClassifiedItem]:
        present_names = {
            (e.get("name") or "").strip().lower()
            for e in self.already_present
        }
        out: list[ClassifiedItem] = []
        for item in self.items:
            if item.name.strip().lower() in present_names:
                continue
            out.append(item)
        return out


def _normalize_name_key(name: str) -> str:
    folded = unicodedata.normalize("NFKC", name.strip())
    return folded.casefold()


def _looks_like_organization(name: str) -> bool:
    return bool(_ORG_RE.search(name))


def _profile_name_index(profile: SayaneProfile) -> dict[str, list[str]]:
    """Lowercase name -> profile paths where it already exists."""
    index: dict[str, list[str]] = {}
    for concept in profile.knowledge.concepts if profile.knowledge else []:
        key = _normalize_name_key(concept)
        if key:
            index.setdefault(key, []).append(CORE_CONCEPT_PATH)
    for term in profile.canonical_terms:
        key = _normalize_name_key(term.term)
        if key:
            index.setdefault(key, []).append(CORE_CONCEPT_PATH)
        exp = _normalize_name_key(term.expansion)
        if exp:
            index.setdefault(exp, []).append(CORE_CONCEPT_PATH)
    for project in profile.major_projects:
        key = _normalize_name_key(project.name)
        if key:
            index.setdefault(key, []).append(MAJOR_PROJECT_PATH)
    if profile.organization and profile.organization.name.strip():
        key = _normalize_name_key(profile.organization.name)
        index.setdefault(key, []).append(ORGANIZATION_PATH)
    identity_name = profile.identity.name.strip()
    if identity_name and not _looks_like_organization(identity_name):
        key = _normalize_name_key(identity_name)
        index.setdefault(key, []).append("identity.name")
    mode = profile.communication_mode
    if mode:
        for value in (
            mode.assistant_name_for_chatgpt,
            mode.preferred_address,
            mode.intimate_address,
            *mode.collaboration_style,
        ):
            if value and value.strip():
                key = _normalize_name_key(value)
                index.setdefault(key, []).append("communication_mode")
    return index


def _is_known_major_project(name: str, profile: SayaneProfile | None) -> bool:
    key = _normalize_name_key(name)
    if key in _KNOWN_MAJOR_PROJECT_NAMES:
        return True
    if profile:
        return any(
            _normalize_name_key(p.name) == key
            for p in profile.major_projects
            if p.name.strip()
        )
    return False


def _is_known_core_concept(name: str, profile: SayaneProfile | None) -> bool:
    key = _normalize_name_key(name)
    if key in _KNOWN_CORE_CONCEPT_NAMES:
        return True
    if profile and profile.knowledge:
        return any(
            _normalize_name_key(c) == key
            for c in profile.knowledge.concepts
            if c.strip()
        )
    return False


def _preferred_present_path(paths: list[str], name: str) -> str:
    if any("organization" in p for p in paths):
        return ORGANIZATION_PATH
    if any(
        "core_concepts" in p or "knowledge.concepts" in p or "canonical_terms" in p
        for p in paths
    ):
        return CORE_CONCEPT_PATH
    if any("major_projects" in p for p in paths):
        return MAJOR_PROJECT_PATH
    if any("identity" in p for p in paths):
        if _looks_like_organization(name):
            return ORGANIZATION_PATH
        return "identity.name"
    return paths[0]


def _section_from_paths(paths: list[str]) -> str:
    if any("organization" in p for p in paths):
        return "organization.name"
    if any(
        "core_concepts" in p or "knowledge.concepts" in p or "canonical_terms" in p
        for p in paths
    ):
        return "knowledge.concepts"
    if any("major_projects" in p for p in paths):
        return "major_projects"
    if any("identity" in p for p in paths):
        return "identity.name"
    if any("communication_mode" in p for p in paths):
        return "communication_mode"
    return paths[0].split("[")[0] if paths else "knowledge.concepts"


def _infer_section_for_name(
    name: str,
    profile_index: dict[str, list[str]],
    *,
    has_summary: bool,
    profile: SayaneProfile | None = None,
) -> str:
    key = _normalize_name_key(name)
    if not key:
        return "knowledge.concepts"
    if key in profile_index:
        return _section_from_paths(profile_index[key])
    if _looks_like_organization(name):
        return "organization.name"
    if _is_known_core_concept(name, profile):
        return "knowledge.concepts"
    if _is_known_major_project(name, profile):
        return "major_projects"
    if has_summary and len(name) <= 48 and _is_known_major_project(name, profile):
        return "major_projects"
    if len(name) <= 32:
        return "knowledge.concepts"
    return "knowledge.concepts"


def classify_structured_capture(
    content: str,
    profile: SayaneProfile | None,
) -> ClassificationResult | None:
    """Re-classify YAML-style project blocks that mix entity types."""
    from sayane.evaluators.proposal import _extract_structured_items

    raw_items = _extract_structured_items(content, max_items=None)
    if not raw_items:
        return None

    profile_index = _profile_name_index(profile) if profile else {}
    result = ClassificationResult()
    for item in raw_items:
        name = (item.get("name") or "").strip()
        if not name or is_ui_noise_name(name):
            continue
        summary = item.get("summary")
        section = _infer_section_for_name(
            name,
            profile_index,
            has_summary=bool(summary),
            profile=profile,
        )
        result.sections_seen.add(section)
        paths = profile_index.get(_normalize_name_key(name), [])
        if paths:
            result.already_present.append(
                {"path": _preferred_present_path(paths, name), "name": name},
            )
        else:
            result.items.append(
                ClassifiedItem(section=section, name=name, summary=summary),
            )
    if result.items or result.already_present:
        new_count = len(result.new_items())
        dup = len(result.already_present)
        result.display_summary = (
            f"Structured capture: {new_count} new, {dup} already in profile"
        )
    return result


def is_ui_noise_name(name: str) -> bool:
    from sayane.evaluators.capture_cleaning import is_ui_noise_line

    return is_ui_noise_line(name)
