"""Pydantic models for Omomuki Profile and Prompt IR."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    preferred_name: str | None = None
    roles: list[str] = Field(default_factory=list)


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


class OmomukiProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    kind: Literal["OmomukiProfile"]
    identity: Identity
    voice: Voice
    values: Values
    knowledge: Knowledge | None = None
    policy: Policy
    context_index: ContextIndex
    lineage: Lineage


class PromptIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "0.1.0"
    kind: Literal["PromptIR"] = "PromptIR"
    system: list[str]
    context: list[str]
    instruction: list[str]
    constraints: list[str]
    examples: list[dict[str, Any]] = Field(default_factory=list)
