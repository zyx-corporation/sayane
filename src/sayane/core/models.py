"""Pydantic models for Sayane Profile and Prompt IR."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CorrectionPolicy = Literal[
    "replace_deprecated_with_canonical",
    "warn_and_preserve_context",
    "block_export",
]


class CanonicalTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    term: str
    expansion: str
    description: str | None = None
    deprecated: list[str] = Field(default_factory=list)
    correction_policy: CorrectionPolicy = "replace_deprecated_with_canonical"


class CanonicalTermRef(BaseModel):
    """Resolved canonical term attached to Prompt IR for adapters."""

    model_config = ConfigDict(extra="forbid")

    term: str
    expansion: str
    description: str | None = None
    deprecated: list[str] = Field(default_factory=list)


class SayaneProjectProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    kind: Literal["SayaneProjectProfile"]
    canonical_terms: list[CanonicalTerm] = Field(default_factory=list)


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    preferred_name: str | None = None
    roles: list[str] = Field(default_factory=list)


class Organization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = ""


class Voice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_language: str | None = None
    tone: list[str] = Field(default_factory=list)


class Values(BaseModel):
    model_config = ConfigDict(extra="forbid")

    core: list[str] = Field(default_factory=list)


class Knowledge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concepts: list[str] = Field(default_factory=list)


class MajorProject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    summary: str | None = None


class CommunicationMode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant_name_for_chatgpt: str | None = None
    preferred_address: str | None = None
    intimate_address: str | None = None
    collaboration_style: list[str] = Field(default_factory=list)


class ResponsePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    avoid: list[str] = Field(default_factory=list)
    prefer: list[str] = Field(default_factory=list)


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    response: ResponsePolicy | None = None


class ContextIndex(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entrypoint: str | None = None
    handoff: str | None = None
    entries: list[str] = Field(default_factory=list)


class Lineage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    updated_at: datetime


class SayaneProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    kind: Literal["SayaneProfile"]
    identity: Identity
    organization: Organization | None = None
    voice: Voice
    values: Values
    knowledge: Knowledge | None = None
    major_projects: list[MajorProject] = Field(default_factory=list)
    communication_mode: CommunicationMode | None = None
    policy: Policy
    context_index: ContextIndex
    lineage: Lineage
    canonical_terms: list[CanonicalTerm] = Field(default_factory=list)
    important_terms: list[str] = Field(default_factory=list)


class PromptIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "0.1.0"
    kind: Literal["PromptIR"] = "PromptIR"
    system: list[str]
    context: list[str]
    instruction: list[str]
    constraints: list[str]
    examples: list[dict[str, Any]] = Field(default_factory=list)
    canonical_terms: list[CanonicalTermRef] = Field(default_factory=list)
    export_notes: list[str] = Field(default_factory=list)
    export_blocked: bool = False
