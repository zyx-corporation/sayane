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


class CompileRequest(BaseModel):
    target: str
    profile_id: str = "default"
    instruction: str | None = None


class ContextPacketResponse(BaseModel):
    target: str
    format: str
    payload: dict[str, Any]
    profile_id: str
