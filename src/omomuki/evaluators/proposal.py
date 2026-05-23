"""Build Candidate proposals from captured content (heuristic)."""

import re

from omomuki.core.candidate import CandidateProposal

_MAX_ITEMS = 5
_MIN_TOKEN_LEN = 3


def build_proposal_from_content(content: str) -> CandidateProposal:
    """Extract a minimal knowledge.concepts proposal from raw capture text."""
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    items: list[str] = []

    for line in lines[:10]:
        if len(line) >= _MIN_TOKEN_LEN and line not in items:
            items.append(line[:120])
        if len(items) >= _MAX_ITEMS:
            break

    if not items and content.strip():
        snippet = content.strip()[:120]
        items.append(snippet)

    summary = content.strip()[:240] if content.strip() else None
    return CandidateProposal(
        section="knowledge.concepts",
        add=items,
        summary=summary,
    )


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
