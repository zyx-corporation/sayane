"""RDE vNext authorization layer types (provisional / confirmed dispositions).

These models do not implement the full RDE vNext rule set. They establish
guardrails against treating evaluation output as objective fact, treating user
consent as sufficient authorization, institutional scope self-expansion,
profiling reuse of accountability logs, and irreversible PoP-UID linkage.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EvaluatorType = Literal["self_agent", "independent_rde", "user", "policy", "council"]
StakeType = Literal["self_interest", "neutral", "third_party_advocate"]
AuthorityType = Literal["advisory", "primary", "final", "veto"]
ConflictType = Literal["none", "low", "high"]
DispositionStatus = Literal["provisional", "confirmed"]
ConvenienceBias = Literal["none", "low", "high", "unknown"]
MirrorDisposition = Literal["mirror"]
InstitutionalInterest = Literal["destructive_deviation_only"]
DelegatedTo = Literal["human_mediation"]
WitnessStrength = Literal["minimal", "internal", "external"]
StorageMode = Literal["encrypted"]
DisclosureAudience = Literal["third_party", "regulator", "self_defense", "auditor"]
AccountabilityPurpose = Literal["accountability", "exculpation"]

FORBIDDEN_ACCOUNTABILITY_PURPOSES = frozenset(
    {
        "judgment",
        "profiling",
        "prediction",
        "scoring",
        "ranking",
        "recommendation",
    },
)


class EvaluatorPosition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stake: StakeType | None = None
    authority: AuthorityType = "advisory"
    jurisdiction: list[str] = Field(default_factory=list)


class EvaluatorDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: EvaluatorType
    identity: str
    position: EvaluatorPosition | None = None
    conflict_of_interest: ConflictType = "none"


class EvaluationSeparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    generator_id: str
    evaluator_id: str
    is_separated: bool = False

    @model_validator(mode="after")
    def _derive_is_separated(self) -> EvaluationSeparation:
        separated = self.generator_id.strip() != self.evaluator_id.strip()
        if self.is_separated != separated:
            return self.model_copy(update={"is_separated": separated})
        return self


class PolicyProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legislator: str = "sayane.default"
    revisable: bool = True
    last_revised: str | None = None


class CumulativeDrift(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected: bool = False
    direction: str = ""
    window: str = ""


class UserAuthorizationAudit(BaseModel):
    """R6: user consent is audited, mirrored, not vetoed by the system."""

    model_config = ConfigDict(extra="forbid")

    convenience_bias: ConvenienceBias = "unknown"
    reuse_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    cumulative_drift: CumulativeDrift = Field(default_factory=CumulativeDrift)
    disposition: MirrorDisposition = "mirror"
    status: DispositionStatus = "provisional"
    recorded_at: datetime
    actor_id: str = "local_user"
    action: str = "approve_requested"


class AccountabilityScope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institutional_interest: InstitutionalInterest = "destructive_deviation_only"
    in_scope: bool = False
    delegated_to: DelegatedTo = "human_mediation"
    threshold_note: str = ""


class TamperEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    append_only: bool = True
    witness_strength: WitnessStrength = "minimal"


class AccountabilityStorage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: StorageMode = "encrypted"


class AccountabilityDisclosure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    principle: Literal["need_to_know"] = "need_to_know"
    audience: DisclosureAudience = "auditor"
    procedure_required: bool = True


class AccountabilityProportionality(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str = ""
    retention: str = ""


class AccountabilityVerifiability(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proof_of_existence: bool = True
    selective_disclosure: bool = True


class AccountabilityLog(BaseModel):
    """R7: institutional accountability record with bounded scope."""

    model_config = ConfigDict(extra="forbid")

    scope: AccountabilityScope = Field(default_factory=AccountabilityScope)
    recorded: bool = False
    tamper_evidence: TamperEvidence = Field(default_factory=TamperEvidence)
    storage: AccountabilityStorage = Field(default_factory=AccountabilityStorage)
    disclosure: AccountabilityDisclosure = Field(default_factory=AccountabilityDisclosure)
    purpose_binding: list[AccountabilityPurpose] = Field(
        default_factory=lambda: ["accountability"],
    )
    proportionality: AccountabilityProportionality = Field(
        default_factory=AccountabilityProportionality,
    )
    verifiability: AccountabilityVerifiability = Field(
        default_factory=AccountabilityVerifiability,
    )
    created_at: datetime | None = None
    event: str = ""


class AuthorizationFeatureFlags(BaseModel):
    """Feature flags — PoP-UID linkage is deferred and disabled by default."""

    model_config = ConfigDict(extra="forbid")

    pop_uid_linkage_enabled: bool = False
    enforce_authorization_guards: bool = True
    legacy_approve_compat: bool = True
