"""Candidate Update models (pre-merge profile changes)."""

from datetime import datetime
from typing import Literal

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from sayane.core.evaluation_notes import EvaluationNote, coerce_notes
from sayane.core.authorization import (
    AccountabilityLog,
    EvaluatorDescriptor,
    EvaluationSeparation,
    PolicyProvenance,
    UserAuthorizationAudit,
)

DispositionStatus = Literal["provisional", "confirmed"]

RDEClass = Literal[
    "Preserved",
    "Authorized Transformation",
    "Inferred Extension",
    "Unresolved Gap",
    "Suspicious Drift",
    "Critical Distortion",
]

CandidateStatus = Literal["pending", "evaluated", "approved", "rejected"]
CandidateEvaluationStatus = Literal["not_started", "completed", "judge_failed"]
CaptureConfidence = Literal["high", "low"]
CaptureSource = Literal["selection", "clipboard", "page"]


class CandidateEvaluationError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    message: str
    provider: str | None = None
    status_code: int | None = None


class CandidateSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    uri: str | None = None
    captured_at: datetime


class CaptureMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_selected: bool = False
    capture_source: CaptureSource = "page"
    capture_confidence: CaptureConfidence = "high"
    requires_review: bool = False
    capture_warnings: list[str] = Field(default_factory=list)
    extractor: str | None = None
    parse_error: str | None = None

    @model_validator(mode="before")
    @classmethod
    def infer_capture_source(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        src = data.get("capture_source")
        if data.get("capture_source") in ("selection", "clipboard", "page"):
            return data
        if data.get("user_selected"):
            data["capture_source"] = "selection"
        else:
            data["capture_source"] = "page"
        return data


class CandidateProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section: str = "knowledge.concepts"
    operation: str = "add"
    add: list[str] = Field(default_factory=list)
    items: list[dict[str, str]] = Field(default_factory=list)
    remove: list[dict[str, str]] = Field(default_factory=list)
    already_present: list[dict[str, str]] = Field(default_factory=list)
    summary: str | None = None
    parse_error: str | None = None


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
    notes: list[EvaluationNote] = Field(default_factory=list)
    uib: UIBScores | None = None

    @field_validator("notes", mode="before")
    @classmethod
    def _coerce_notes(cls, value: Any) -> list[EvaluationNote]:
        return coerce_notes(value) if isinstance(value, list) else []


class CandidateEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: int = Field(default=1, ge=0, le=3)
    rde_class: RDEClass
    notes: list[EvaluationNote] = Field(default_factory=list)
    uib: UIBScores
    evaluated_at: datetime
    llm_review: LLMReview | None = None
    evaluator: EvaluatorDescriptor | None = None
    separation: EvaluationSeparation | None = None
    policy_provenance: PolicyProvenance | None = None
    disposition_status: DispositionStatus = "provisional"

    @field_validator("notes", mode="before")
    @classmethod
    def _coerce_notes(cls, value: Any) -> list[EvaluationNote]:
        return coerce_notes(value) if isinstance(value, list) else []

    @model_validator(mode="after")
    def _legacy_provisional_when_evaluator_missing(self) -> Self:
        if self.evaluator is None:
            object.__setattr__(self, "disposition_status", "provisional")
        return self


class CandidateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "0.1.0"
    kind: Literal["CandidateUpdate"] = "CandidateUpdate"
    id: str
    status: CandidateStatus = "pending"
    evaluation_status: CandidateEvaluationStatus = "not_started"
    evaluation_error: CandidateEvaluationError | None = None
    locale: str | None = None
    target_profile_id: str = "default"
    content: str
    raw_capture: str | None = None
    cleaned_capture: str | None = None
    display_summary: str | None = None
    capture_meta: CaptureMetadata | None = None
    source: CandidateSource
    proposal: CandidateProposal
    evaluation: CandidateEvaluation | None = None
    generator_id: str | None = None
    supplemental_evaluations: list[CandidateEvaluation] = Field(default_factory=list)
    user_authorization_audits: list[UserAuthorizationAudit] = Field(default_factory=list)
    accountability_logs: list[AccountabilityLog] = Field(default_factory=list)
