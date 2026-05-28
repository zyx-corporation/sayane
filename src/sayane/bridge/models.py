"""Local Bridge API request/response models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProfileSummary(BaseModel):
    id: str
    path: str
    name: str | None = None


class CaptureRequest(BaseModel):
    content: str = Field(min_length=1)
    source: str | None = None
    source_url: str | None = None


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


class ApproveCandidateRequest(BaseModel):
    force_critical: bool = False


class RejectCandidateRequest(BaseModel):
    reason: str | None = None
