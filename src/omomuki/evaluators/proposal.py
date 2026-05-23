"""Build Candidate proposals from captured content (heuristic)."""

import re

from omomuki.core.candidate import CandidateProposal
from omomuki.evaluators.sections import infer_proposal_section

_MAX_ITEMS = 5
_MIN_TOKEN_LEN = 3
_BULLET_RE = re.compile(r"^[\s]*[-*•]\s+(.+)$")


def build_proposal_from_content(content: str, section: str | None = None) -> CandidateProposal:
    """Extract a section-targeted proposal from raw capture text."""
    target = section or infer_proposal_section(content)
    items = _extract_items(content, target)
    summary = content.strip()[:240] if content.strip() else None
    return CandidateProposal(section=target, add=items, summary=summary)


def _extract_items(content: str, section: str) -> list[str]:
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    items: list[str] = []

    for line in lines:
        bullet = _BULLET_RE.match(line)
        candidate = bullet.group(1).strip() if bullet else line
        if section.startswith("policy."):
            candidate = _strip_policy_prefix(candidate)
        if len(candidate) >= _MIN_TOKEN_LEN and candidate not in items:
            items.append(candidate[:120])
        if len(items) >= _MAX_ITEMS:
            break

    if not items and content.strip():
        items.append(content.strip()[:120])

    return items


def _strip_policy_prefix(line: str) -> str:
    for prefix in ("avoid:", "prefer:", "Avoid:", "Prefer:"):
        if line.startswith(prefix):
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
