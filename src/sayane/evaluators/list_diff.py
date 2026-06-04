"""List-section diff helpers (important_terms, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from sayane.core.candidate import CandidateProposal

LIST_DIFF_SECTIONS: tuple[str, ...] = (
    "important_terms",
    "tags",
    "keywords",
    "interests",
    "focus_terms",
)


@dataclass(frozen=True)
class ListDiff:
    added: list[str]
    removed: list[str]
    unchanged: list[str]

    @property
    def unchanged_count(self) -> int:
        return len(self.unchanged)

    def to_dict(self) -> dict[str, Any]:
        return {
            "added": self.added,
            "removed": self.removed,
            "unchanged": self.unchanged,
            "unchanged_count": self.unchanged_count,
        }


def diff_string_list(existing: list[str], proposed: list[str]) -> ListDiff:
    """Set-based list diff; order changes are ignored in v1."""
    normalize = lambda s: s.strip()  # noqa: E731

    def norm_key(s: str) -> str:
        return normalize(s).casefold()

    existing_map = {norm_key(v): normalize(v) for v in existing if normalize(v)}
    proposed_map = {norm_key(v): normalize(v) for v in proposed if normalize(v)}

    existing_keys = set(existing_map)
    proposed_keys = set(proposed_map)

    added = [proposed_map[k] for k in sorted(proposed_keys - existing_keys, key=str.lower)]
    removed = [existing_map[k] for k in sorted(existing_keys - proposed_keys, key=str.lower)]
    unchanged = [
        proposed_map[k] for k in sorted(existing_keys & proposed_keys, key=str.lower)
    ]
    return ListDiff(added=added, removed=removed, unchanged=unchanged)


def _normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_normalize_scalar(v) for v in value if v is not None)
    return str(value).strip()


def parse_yaml_list_section(content: str, section: str) -> list[str]:
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError:
        return []
    if not isinstance(parsed, dict):
        return []
    raw = parsed.get(section)
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for entry in raw:
        text = _normalize_scalar(entry)
        if text:
            out.append(text)
    return out


def important_terms_from_proposal(proposal: CandidateProposal) -> list[str]:
    """All terms referenced in capture classification."""
    names: list[str] = []
    for entry in proposal.items:
        name = (entry.get("name") or "").strip()
        if name:
            names.append(name)
    for entry in proposal.already_present:
        name = (entry.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def list_diff_for_important_terms(proposal: CandidateProposal) -> ListDiff:
    """Diff from proposal classification (added vs already_present)."""
    added = [
        (item.get("name") or "").strip()
        for item in proposal.items
        if (item.get("name") or "").strip()
    ]
    unchanged = [
        (item.get("name") or "").strip()
        for item in proposal.already_present
        if (item.get("name") or "").strip()
    ]
    return ListDiff(added=added, removed=[], unchanged=unchanged)


def important_terms_profile_diff(
    existing: list[str],
    proposed: list[str],
) -> ListDiff:
    """Compare capture list to profile.important_terms only (not other fields)."""
    return diff_string_list(existing, proposed)


def list_diff_operation(diff: ListDiff) -> str:
    if diff.added and diff.removed:
        return "list_update"
    if diff.added:
        return "list_add"
    if diff.removed:
        return "list_remove"
    return "list_unchanged"


def important_terms_display_summary(
    proposal: CandidateProposal,
    *,
    locale: str | None = None,
) -> str:
    diff = list_diff_for_important_terms(proposal)
    if diff.added:
        names = ", ".join(diff.added)
        if locale and str(locale).lower().startswith("ja"):
            return (
                f"important_terms に {len(diff.added)} 件の追加候補があります。"
                f"追加: {names}"
            )
        return f"important_terms: {len(diff.added)} term(s) to add — {names}"
    if diff.unchanged and not diff.added:
        if locale and str(locale).lower().startswith("ja"):
            return f"important_terms: 既存と一致 ({len(diff.unchanged)} 件)"
        return f"important_terms: all {len(diff.unchanged)} term(s) already in profile"
    return proposal.summary or "important_terms"


def important_terms_judge_payload(proposal: CandidateProposal) -> dict[str, Any]:
    diff = list_diff_for_important_terms(proposal)
    return {
        "section": "important_terms",
        "operation": list_diff_operation(diff),
        "added": diff.added,
        "removed": diff.removed,
        "unchanged_count": diff.unchanged_count,
    }
