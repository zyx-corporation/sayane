"""LLM-as-a-Judge for RDE review (Level 2+)."""

import json
import re
import urllib.error
import urllib.request
from typing import Any

from sayane.core.candidate import CandidateProposal, LLMReview, RDEClass, UIBScores
from sayane.core.models import SayaneProfile
from sayane.evaluators.judge_config import JudgeConfig

_UIB_KEYS = ("UD", "MI", "CH", "DT", "VP", "FG")
_DEFAULT_UIB_AXIS = 0.5

_RDE_CLASSES: tuple[RDEClass, ...] = (
    "Preserved",
    "Authorized Transformation",
    "Inferred Extension",
    "Unresolved Gap",
    "Suspicious Drift",
    "Critical Distortion",
)

_JUDGE_PROMPT = """You are an RDE reviewer for Sayane profile updates (T-RDE v1.1a operational subset).

This review is a tentative heuristic — not an objective truth determination.
The human reviewer makes the final approve/reject decision.

Given the current profile summary, captured content, and merge proposal,
respond with JSON only (no markdown fences):

{{
  "rde_class": one of {rde_classes},
  "notes": ["short reason", ...],
  "uib": {{
    "UD": 0.0-1.0, "MI": 0.0-1.0, "CH": 0.0-1.0,
    "DT": 0.0-1.0, "VP": 0.0-1.0, "FG": 0.0-1.0
  }}
}}

Rules (T-RDE v1.1a aligned):
- Prefer Unresolved Gap or Suspicious Drift when uncertain; never classify as Preserved by guess.
- Never treat LLM inference or implicit additions as verified user facts.
- Critical Distortion: secrets, critical profile fields, value inversion, or irreversible risk.
- Value-destructive or responsibility-shifting changes → Suspicious Drift or Critical Distortion
  (regardless of how small the diff appears).
- High UD / CH scores when competing interpretations or hidden assumptions exist.
"""


def review_with_llm(
    config: JudgeConfig,
    level: int,
    profile: SayaneProfile,
    content: str,
    proposal: CandidateProposal,
) -> LLMReview:
    """Call OpenAI-compatible chat completions API."""
    profile_summary = _profile_summary(profile)
    user_msg = (
        f"Profile:\n{profile_summary}\n\n"
        f"Captured content:\n{content[:4000]}\n\n"
        f"Proposal section: {proposal.section}\n"
        f"Proposal add: {json.dumps(proposal.add, ensure_ascii=False)}\n"
        f"Summary: {proposal.summary or ''}"
    )
    prompt = _JUDGE_PROMPT.format(rde_classes=", ".join(_RDE_CLASSES))
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.2,
    }
    url = f"{config.base_url}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.timeout_sec) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM judge request failed: {exc}") from exc

    text = body["choices"][0]["message"]["content"]
    parsed = _parse_judge_json(text)
    return LLMReview(
        model=config.model,
        level=level,
        rde_class=parsed.get("rde_class"),
        notes=parsed.get("notes", []),
        uib=parsed.get("uib"),
    )


def _profile_summary(profile: SayaneProfile) -> str:
    concepts = profile.knowledge.concepts if profile.knowledge else []
    return json.dumps(
        {
            "identity": profile.identity.name,
            "values": profile.values.core[:8],
            "tone": profile.voice.tone[:8],
            "concepts": concepts[:12],
        },
        ensure_ascii=False,
    )


def _parse_judge_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    data = json.loads(text)
    rde = data.get("rde_class")
    if rde not in _RDE_CLASSES:
        raise ValueError(f"Invalid rde_class from judge: {rde}")
    notes = data.get("notes") or []
    if not isinstance(notes, list):
        notes = [str(notes)]
    uib_raw = data.get("uib")
    uib = _coerce_uib_scores(uib_raw) if isinstance(uib_raw, dict) else None
    return {"rde_class": rde, "notes": [str(n) for n in notes], "uib": uib}


def _coerce_uib_scores(raw: dict[str, Any]) -> UIBScores:
    """Fill missing UIB axes (small models often return partial JSON)."""
    values: dict[str, float] = {}
    for key in _UIB_KEYS:
        val = raw.get(key, _DEFAULT_UIB_AXIS)
        try:
            num = float(val)
        except (TypeError, ValueError):
            num = _DEFAULT_UIB_AXIS
        values[key] = max(0.0, min(1.0, num))
    return UIBScores(**values)
