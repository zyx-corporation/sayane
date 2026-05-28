"""Build Candidate proposals from captured content (heuristic)."""

import re

from sayane.core.candidate import CandidateProposal
from sayane.evaluators.sections import infer_proposal_section

_MAX_ITEMS = 5
_MIN_TOKEN_LEN = 3
_BULLET_RE = re.compile(r"^[\s]*[-*•]\s+(.+)$")
_MARKDOWN_HEADING_RE = re.compile(r"^#+\s")
_BARE_YAML_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*:\s*$", re.IGNORECASE)
_YAML_KEY_VALUE_RE = re.compile(r"^[a-z][a-z0-9_]*:\s+.+", re.IGNORECASE)


def build_proposal_from_content(content: str, section: str | None = None) -> CandidateProposal:
    """Extract a section-targeted proposal from raw capture text."""
    target = section or infer_proposal_section(content)
    items = _extract_items(content, target)
    summary = content.strip()[:240] if content.strip() else None
    return CandidateProposal(section=target, add=items, summary=summary)


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
            return line[len(prefix) :].strip()
    return line


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
