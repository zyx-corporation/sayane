"""T-RDE semantic map models.

T-RDE is intentionally separate from Candidate RDE. Candidate RDE judges whether a
candidate update may be merged. T-RDE audits meaning preservation and drift across
Raw / Edited / Normalize / Interpret / Export / Live.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

Stage = Literal["raw", "edited", "normalize", "interpret", "export", "live"]
IntentStatus = Literal["preserved", "transformed", "deviated", "not_implemented"]
ChangeType = Literal["preservation", "transformation", "deviation"]
RiskLevel = Literal["low", "medium", "high"]


class IntentElement(BaseModel):
    """A design-intent element and its implementation / output mapping."""

    id: str
    description: str
    mapped_to: str | None = None
    status: IntentStatus
    transform_reason: str | None = None

    @model_validator(mode="after")
    def validate_mapping(self) -> "IntentElement":
        if self.status == "not_implemented" and self.mapped_to is not None:
            raise ValueError("not_implemented intent must not have mapped_to")
        if self.status == "transformed" and not self.transform_reason:
            raise ValueError("transformed intent requires transform_reason")
        return self


class ImplicitAddition(BaseModel):
    """An assumption or feature added without explicit user/design intent."""

    description: str
    justification: str
    risk: RiskLevel
    affected_stage: Stage


class DeltaM(BaseModel):
    """Meaning change between two stages."""

    from_stage: Stage
    to_stage: Stage
    element: str
    change_type: ChangeType
    description: str = ""
    severity: float = Field(ge=0.0, le=1.0)
    approved: bool

    @model_validator(mode="after")
    def validate_approval(self) -> "DeltaM":
        if self.change_type == "preservation" and self.severity != 0.0:
            raise ValueError("preservation must have severity 0.0")
        return self


class SemanticSummary(BaseModel):
    preserved_count: int = Field(ge=0)
    transformed_count: int = Field(ge=0)
    deviated_count: int = Field(ge=0)
    not_implemented_count: int = Field(ge=0)
    implicit_additions_count: int = Field(ge=0)
    max_severity: float = Field(ge=0.0, le=1.0)


class SemanticMap(BaseModel):
    """Full T-RDE semantic map.

    This map is the auditable artifact. It should be kept outside opaque browser
    state such as e2e/user-data.
    """

    intent_elements: list[IntentElement]
    implicit_additions: list[ImplicitAddition] = Field(default_factory=list)
    delta_ms: list[DeltaM] = Field(default_factory=list)
    summary: SemanticSummary | None = None

    def computed_summary(self) -> SemanticSummary:
        preserved = sum(1 for e in self.intent_elements if e.status == "preserved")
        transformed = sum(1 for e in self.intent_elements if e.status == "transformed")
        deviated = sum(1 for e in self.intent_elements if e.status == "deviated")
        not_implemented = sum(1 for e in self.intent_elements if e.status == "not_implemented")
        max_severity = max((dm.severity for dm in self.delta_ms), default=0.0)
        return SemanticSummary(
            preserved_count=preserved,
            transformed_count=transformed,
            deviated_count=deviated,
            not_implemented_count=not_implemented,
            implicit_additions_count=len(self.implicit_additions),
            max_severity=max_severity,
        )
