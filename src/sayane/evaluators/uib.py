"""Heuristic UIB checklist scores (0.0–1.0)."""

from sayane.core.candidate import CandidateProposal, UIBScores
from sayane.evaluators.heuristic_match import (
    contains_any_phrase,
    contains_any_word,
)

_UNCERTAINTY_PHRASES = (
    "not sure",
    "i think",
)
_UNCERTAINTY_WORDS = (
    "maybe",
    "perhaps",
    "might",
    "possibly",
    "uncertain",
    "uncertainty",
    "推測",
    "不明",
)


def _signals_uncertainty(content: str) -> bool:
    return (
        contains_any_phrase(content, _UNCERTAINTY_PHRASES)
        or contains_any_word(content, _UNCERTAINTY_WORDS)
    )


def score_uib(content: str, proposal: CandidateProposal) -> UIBScores:
    length = len(content.strip())
    proposal_count = (
        len(proposal.items) if proposal.items else len(proposal.add)
    )

    ud = 0.85 if _signals_uncertainty(content) else 0.55
    mi = 0.9 if length < 400 else 0.65 if length < 2000 else 0.45
    ch = 0.7 if proposal_count > 1 else 0.5
    dt = 0.75 if proposal.section else 0.5
    vp = (
        0.8
        if not proposal.section.startswith(("identity", "values", "policy"))
        else 0.35
    )
    fg = 0.75 if length > 0 else 0.4

    return UIBScores(UD=ud, MI=mi, CH=ch, DT=dt, VP=vp, FG=fg)
