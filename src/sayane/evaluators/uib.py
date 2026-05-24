"""Heuristic UIB checklist scores (0.0–1.0)."""

from sayane.core.candidate import CandidateProposal, UIBScores

_UNCERTAINTY = ("maybe", "perhaps", "might", "推測", "不明", "?", "possibly")


def score_uib(content: str, proposal: CandidateProposal) -> UIBScores:
    lower = content.lower()
    length = len(content.strip())

    ud = 0.85 if any(m in lower for m in _UNCERTAINTY) else 0.55
    mi = 0.9 if length < 400 else 0.65 if length < 2000 else 0.45
    ch = 0.7 if len(proposal.add) > 1 else 0.5
    dt = 0.75 if proposal.section else 0.5
    vp = 0.8 if not proposal.section.startswith(("identity", "values", "policy")) else 0.35
    fg = 0.75 if length > 0 else 0.4

    return UIBScores(UD=ud, MI=mi, CH=ch, DT=dt, VP=vp, FG=fg)
