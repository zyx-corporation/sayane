"""Candidate Update models (pre-merge profile changes)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RDEClass = Literal[
    "Preserved",
    "Authorized Transformation",
    "Inferred Extension",
    "Unresolved Gap",
    "Suspicious Drift",
    "Critical Distortion",
]

CandidateStatus = Literal["pending", "evaluated", "approved", "rejected"]


class CandidateSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    uri: str | None = None
    captured_at: datetime


class CandidateProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section: str = "knowledge.concepts"
    add: list[str] = Field(default_factory=list)
    summary: str | None = None


class UIBScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    UD: float = Field(ge=0.0, le=1.0)
    MI: float = Field(ge=0.0, le=1.0)
    CH: float = Field(ge=0.0, le=1.0)
    DT: float = Field(ge=0.0, le=1.0)
    VP: float = Field(ge=0.0, le=1.0)
    FG: float = Field(ge=0.0, le=1.0)


class LLMReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    level: int = Field(ge=2, le=3)
    rde_class: RDEClass | None = None
    notes: list[str] = Field(default_factory=list)
    uib: UIBScores | None = None


class CandidateEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: int = Field(default=1, ge=0, le=3)
    rde_class: RDEClass
    notes: list[str] = Field(default_factory=list)
    uib: UIBScores
    evaluated_at: datetime
    llm_review: LLMReview | None = None


class CandidateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "0.1.0"
    kind: Literal["CandidateUpdate"] = "CandidateUpdate"
    id: str
    status: CandidateStatus = "pending"
    target_profile_id: str = "default"
    content: str
    source: CandidateSource
    proposal: CandidateProposal
    evaluation: CandidateEvaluation | None = None
