"""Build Candidate proposals from captured content (heuristic)."""

import re

import yaml

from sayane.core.candidate import CandidateProposal, CaptureMetadata
from sayane.core.models import SayaneProfile
from sayane.evaluators.capture_parse import (
    SECTION_REVIEW_REQUIRED,
    build_no_effective_proposal,
    build_proposal_for_yaml_content,
)
from sayane.evaluators.capture_classify import (
    ClassificationResult,
    classify_structured_capture,
)
from sayane.evaluators.capture_cleaning import display_summary_from_text
from sayane.evaluators.sections import infer_proposal_section

_MAX_ITEMS = 5
_MIN_TOKEN_LEN = 3
_BULLET_RE = re.compile(r"^[\s]*[-*•]\s+(.+)$")
_MARKDOWN_HEADING_RE = re.compile(r"^#+\s")
_BARE_YAML_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*:\s*$", re.IGNORECASE)
_YAML_KEY_VALUE_RE = re.compile(r"^[a-z][a-z0-9_]*:\s+.+", re.IGNORECASE)


def build_proposal_from_content(
    content: str,
    section: str | None = None,
    profile: SayaneProfile | None = None,
    *,
    capture_meta: CaptureMetadata | None = None,
) -> CandidateProposal:
    """Extract a section-targeted proposal from raw capture text."""
    yaml_proposal = build_proposal_for_yaml_content(content, profile, capture_meta)
    if yaml_proposal is not None:
        if yaml_proposal.operation in ("parse_failed", "parse_failed_or_no_effective_update"):
            yaml_proposal.parse_error = yaml_proposal.summary
        return yaml_proposal

    if capture_meta and capture_meta.capture_confidence == "low" and profile is not None:
        classified = classify_structured_capture(content, profile)
        if classified and (classified.is_mixed or classified.already_present):
            return _proposal_from_classification(classified, capture_meta)

    project_items = _extract_structured_items(content)
    communication_items = _extract_communication_items(content)
    inferred_section = infer_proposal_section(
        content,
        structured_items=project_items,
        communication_items=communication_items,
    )
    target = section or inferred_section

    if profile is not None and project_items and not section:
        classified = classify_structured_capture(content, profile)
        if classified and classified.is_mixed:
            return _proposal_from_classification(classified, capture_meta)

    operation = "add"
    already_present: list[dict[str, str]] = []
    proposal_items = communication_items if communication_items else project_items
    items = _extract_items(content, target)
    summary = _build_display_summary(content, capture_meta)
    if target == "major_projects" and profile is not None and project_items:
        classified = classify_structured_capture(content, profile)
        if classified:
            if classified.is_mixed:
                return _proposal_from_classification(classified, capture_meta)
            proposal_items = [
                {"name": i.name, **({"summary": i.summary} if i.summary else {})}
                for i in classified.new_items()
                if i.section == "major_projects"
            ]
            already_present = list(classified.already_present)
            resolved_section = target
            if not proposal_items and already_present:
                path_blob = " ".join(e.get("path", "") for e in already_present)
                if "major_projects" not in path_blob:
                    resolved_section = "knowledge.concepts"
                    if len({e.get("path", "").split("[")[0] for e in already_present}) > 1:
                        resolved_section = "mixed_sections"
            items = []
            operation = "add_or_update"
            if not proposal_items:
                operation = "no_op_or_duplicate"
            proposal = CandidateProposal(
                section=resolved_section,
                operation=operation,
                add=items,
                items=proposal_items,
                already_present=already_present,
                summary=summary,
            )
            if capture_meta and capture_meta.capture_confidence == "low":
                if proposal.operation != "no_op_or_duplicate":
                    proposal.operation = "no_op_or_duplicate"
                    proposal.items = []
                    proposal.add = []
            return proposal
    if target == "major_projects":
        items = []
        operation = "add_or_update"
        if profile is not None:
            proposal_items, already_present = _split_existing_projects(
                profile,
                proposal_items,
            )
            if not proposal_items:
                operation = "no_op_or_duplicate"
    elif target == "communication_mode":
        items = []
        operation = "add_or_update"
        if profile is not None:
            proposal_items, already_present = _split_existing_communication(
                profile,
                proposal_items,
            )
            if not proposal_items:
                operation = "no_op_or_duplicate"
    elif communication_items:
        # Keep structured path/value data even when explicit section override exists.
        items = []
    proposal = CandidateProposal(
        section=target,
        operation=operation,
        add=items,
        items=proposal_items,
        already_present=already_present,
        summary=summary,
    )
    if capture_meta and capture_meta.capture_confidence == "low":
        if proposal.operation != "no_op_or_duplicate" and (proposal.items or proposal.add):
            proposal.operation = "no_op_or_duplicate"
            proposal.already_present = proposal.already_present or proposal.items
            proposal.items = []
            proposal.add = []

    if (
        proposal.section == "major_projects"
        and not proposal.add
        and not proposal.items
        and not proposal.already_present
    ):
        return build_no_effective_proposal(
            "No effective profile update inferred; section unknown",
        )

    return proposal


def _build_display_summary(
    content: str,
    capture_meta: CaptureMetadata | None,
) -> str | None:
    if capture_meta and capture_meta.capture_confidence == "low":
        return display_summary_from_text(content)
    stripped = content.strip()
    if not stripped:
        return None
    if len(stripped) > 400:
        return display_summary_from_text(stripped)
    return stripped


def _proposal_from_classification(
    classified: ClassificationResult,
    capture_meta: CaptureMetadata | None,
) -> CandidateProposal:
    new_items = classified.new_items()
    low_confidence = bool(
        capture_meta and capture_meta.capture_confidence == "low",
    )
    payload_items: list[dict[str, str]] = []
    if new_items and not low_confidence:
        payload_items = [
            {
                "section": item.section,
                "name": item.name,
                **({"summary": item.summary} if item.summary else {}),
            }
            for item in new_items
        ]
    elif new_items and low_confidence:
        payload_items = [
            {
                "section": item.section,
                "name": item.name,
                **({"summary": item.summary} if item.summary else {}),
            }
            for item in new_items
        ]
    summary = classified.display_summary or display_summary_from_text(
        ", ".join(i.name for i in new_items[:5]),
    )
    operation = "no_op_or_duplicate"
    if new_items and not low_confidence:
        operation = "add_or_update"
    return CandidateProposal(
        section="mixed_sections",
        operation=operation,
        add=[],
        items=payload_items,
        already_present=classified.already_present,
        summary=summary,
    )


def _is_noise_line(line: str) -> bool:
    if _MARKDOWN_HEADING_RE.match(line):
        return True
    if _BARE_YAML_KEY_RE.match(line):
        return True
    return False


def _extract_items(content: str, section: str) -> list[str]:
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    items: list[str] = []

    for line in lines:
        if _is_noise_line(line):
            continue
        bullet = _BULLET_RE.match(line)
        candidate = bullet.group(1).strip() if bullet else line
        if not bullet and _YAML_KEY_VALUE_RE.match(line):
            _, _, value = line.partition(":")
            candidate = value.strip()
        if section.startswith("policy."):
            candidate = _strip_policy_prefix(candidate)
        if len(candidate) < _MIN_TOKEN_LEN or candidate in items:
            continue
        items.append(candidate[:120])
        if len(items) >= _MAX_ITEMS:
            break

    if not items and content.strip():
        compact = " ".join(
            ln.strip()
            for ln in content.splitlines()
            if ln.strip() and not _is_noise_line(ln.strip())
        )
        if len(compact) >= _MIN_TOKEN_LEN:
            items.append(compact[:120])

    return items


def _strip_policy_prefix(line: str) -> str:
    lowered = line.lower()
    for prefix in ("avoid:", "prefer:"):
        if lowered.startswith(prefix):
            return line[len(prefix):].strip()
    return line


def _extract_structured_items(
    content: str,
    *,
    max_items: int | None = _MAX_ITEMS,
) -> list[dict[str, str]]:
    lines = [ln.rstrip() for ln in content.splitlines()]
    items: list[dict[str, str]] = []
    current_name: str | None = None
    current_summary: str | None = None
    saw_project_shape = False

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("major_projects:") or line.startswith("projects:"):
            saw_project_shape = True
            continue
        if line.startswith("- name:") or line.startswith("name:"):
            if current_name:
                item = {"name": current_name}
                if current_summary:
                    item["summary"] = current_summary
                items.append(item)
            current_name = line.split(":", 1)[1].strip().strip('"')
            current_summary = None
            saw_project_shape = True
            continue
        if line.startswith("summary:") and current_name:
            current_summary = line.split(":", 1)[1].strip().strip('"')
            saw_project_shape = True

    if current_name:
        item = {"name": current_name}
        if current_summary:
            item["summary"] = current_summary
        items.append(item)

    if saw_project_shape and items:
        if max_items is None:
            return items
        return items[:max_items]
    return []


def _normalize_summary(summary: str | None) -> str:
    if not summary:
        return ""
    return " ".join(summary.strip().lower().split())


def _split_existing_projects(
    profile: SayaneProfile,
    items: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    existing_by_name: dict[str, str] = {
        p.name.strip().lower(): _normalize_summary(p.summary)
        for p in profile.major_projects
        if p.name.strip()
    }
    add_items: list[dict[str, str]] = []
    already_present: list[dict[str, str]] = []
    for item in items:
        name = item.get("name", "").strip()
        if not name:
            continue
        summary = item.get("summary")
        key = name.lower()
        if key not in existing_by_name:
            add_items.append(item)
            continue
        existing_summary = existing_by_name[key]
        if existing_summary == _normalize_summary(summary):
            already_present.append(item)
        else:
            add_items.append(item)
    return add_items, already_present


def _extract_communication_items(content: str) -> list[dict[str, str]]:
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError:
        return []
    if not isinstance(parsed, dict):
        return []
    root = parsed.get("communication_mode")
    if not isinstance(root, dict):
        return []

    out: list[dict[str, str]] = []
    for key in (
        "assistant_name_for_chatgpt",
        "preferred_address",
        "intimate_address",
    ):
        value = root.get(key)
        if isinstance(value, str) and value.strip():
            out.append(
                {
                    "path": f"communication_mode.{key}",
                    "value": value.strip(),
                },
            )

    styles = root.get("collaboration_style")
    if isinstance(styles, list):
        for style in styles:
            if isinstance(style, str) and style.strip():
                out.append(
                    {
                        "path": "communication_mode.collaboration_style",
                        "value": style.strip(),
                    },
                )
                if len(out) >= 20:
                    break
    return out


def _split_existing_communication(
    profile: SayaneProfile,
    items: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    mode = profile.communication_mode
    if mode is None:
        return items, []
    existing: set[tuple[str, str]] = set()
    if mode.assistant_name_for_chatgpt:
        existing.add(
            (
                "communication_mode.assistant_name_for_chatgpt",
                mode.assistant_name_for_chatgpt.strip(),
            ),
        )
    if mode.preferred_address:
        existing.add(
            (
                "communication_mode.preferred_address",
                mode.preferred_address.strip(),
            ),
        )
    if mode.intimate_address:
        existing.add(
            (
                "communication_mode.intimate_address",
                mode.intimate_address.strip(),
            ),
        )
    for value in mode.collaboration_style:
        existing.add(("communication_mode.collaboration_style", value.strip()))

    add_items: list[dict[str, str]] = []
    already_present: list[dict[str, str]] = []
    for item in items:
        path = item.get("path", "").strip()
        value = item.get("value", "").strip()
        if not path or not value:
            continue
        if (path, value) in existing:
            already_present.append({"path": path, "value": value})
        else:
            add_items.append({"path": path, "value": value})
    return add_items, already_present


def extract_terms(content: str) -> list[str]:
    """Find capitalized or quoted terms for diff display."""
    quoted = re.findall(r'"([^"]{3,80})"', content)
    caps = re.findall(r"\b[A-Z][a-zA-Z]{2,30}\b", content)
    seen: set[str] = set()
    out: list[str] = []
    for term in quoted + caps:
        if term not in seen:
            seen.add(term)
            out.append(term)
    return out[:10]
