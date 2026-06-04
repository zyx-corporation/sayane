"""Local Bridge API request/response models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProfileSummary(BaseModel):
    id: str
    path: str
    name: str | None = None
    default_language: str | None = None


class CaptureRequest(BaseModel):
    content: str = Field(min_length=1, description="Cleaned capture text for proposal.")
    raw_content: str | None = Field(
        default=None,
        description="Original capture before UI noise removal.",
    )
    source: str | None = None
    source_url: str | None = None
    profile_id: str = "default"
    locale: str | None = None
    user_selected: bool = False
    capture_source: Literal["selection", "clipboard", "page"] | None = None
    capture_confidence: Literal["high", "low"] = "high"
    requires_review: bool = False
    capture_warnings: list[str] = Field(default_factory=list)
    extractor: str | None = None
    section: str | None = Field(
        default=None,
        description=(
            "Optional Sayane profile section "
            "(overrides heuristic inference)."
        ),
    )


class CaptureResponse(BaseModel):
    id: str
    status: Literal["captured"] = "captured"
    path: str
    warnings: list[str] = Field(default_factory=list)


class CompileRequest(BaseModel):
    target: str
    profile_id: str = "default"
    instruction: str | None = None


class ContextPacketResponse(BaseModel):
    target: str
    format: str
    payload: dict[str, Any]
    profile_id: str


class EvaluateCandidateRequest(BaseModel):
    level: int = Field(default=1, ge=1, le=3)


class ExplicitConfirmationPayload(BaseModel):
    section: str
    checked: bool = True
    reason: str
    confirmed_at: str | None = None


class ApproveCandidateRequest(BaseModel):
    force_critical: bool = False
    override_reason: str | None = None
    explicit_confirmation: ExplicitConfirmationPayload | None = None


class RejectCandidateRequest(BaseModel):
    reason: str | None = None


class ImportantTermsPreflightRequest(BaseModel):
    content: str = Field(min_length=1)
    profile_id: str = "default"


class ImportantTermsPreflightResponse(BaseModel):
    section: Literal["important_terms"] = "important_terms"
    total: int = Field(ge=0)
    existing_count: int = Field(ge=0)
    added_count: int = Field(ge=0)
    removed_count: int = Field(ge=0)


class ReviseCandidateRequest(BaseModel):
    edited_text: str = Field(min_length=1)
    target_section: str | None = None
    change_reason: str | None = None
