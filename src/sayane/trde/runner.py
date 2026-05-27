"""T-RDE semantic audit runner."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sayane.trde.models import ImplicitAddition, SemanticMap, SemanticSummary

ViolationType = Literal["UNINTENDED_DEVIATION", "UNAPPROVED_TRANSFORMATION"]


@dataclass(frozen=True)
class Violation:
    stage: str
    element: str
    severity: float
    description: str
    type: ViolationType


@dataclass(frozen=True)
class TRDEResult:
    passed: bool
    violations: list[Violation]
    summary: SemanticSummary


@dataclass(frozen=True)
class ImplicitRiskItem:
    description: str
    justification: str
    risk: Literal["medium", "high"]
    stage: str
    action: Literal["REQUIRES_EXPLICIT_APPROVAL"] = "REQUIRES_EXPLICIT_APPROVAL"


@dataclass(frozen=True)
class ImplicitRiskReport:
    total_implicits: int
    flagged_count: int
    items: list[ImplicitRiskItem]


@dataclass(frozen=True)
class CoverageItem:
    id: str
    description: str


@dataclass(frozen=True)
class CoverageReport:
    total_intents: int
    implemented_count: int
    preserved_count: int
    implementation_rate: float
    preservation_rate: float
    unimplemented: list[CoverageItem]


class TRDERunner:
    """Audit a semantic map for unintended meaning drift.

    This runner is deliberately deterministic and does not call an LLM. LLM-based
    cross validation can be layered on top, but the release gate must have a
    local, testable baseline.
    """

    def __init__(self, semantic_map: SemanticMap) -> None:
        self.semantic_map = semantic_map

    def audit_deviations(self) -> TRDEResult:
        """Detect deviations and unapproved transformations."""
        violations: list[Violation] = []

        for dm in self.semantic_map.delta_ms:
            stage = f"{dm.from_stage} → {dm.to_stage}"
            if dm.change_type == "deviation":
                violations.append(
                    Violation(
                        stage=stage,
                        element=dm.element,
                        severity=dm.severity,
                        description=dm.description,
                        type="UNINTENDED_DEVIATION",
                    ),
                )
            elif dm.change_type == "transformation" and not dm.approved:
                violations.append(
                    Violation(
                        stage=stage,
                        element=dm.element,
                        severity=dm.severity,
                        description=dm.description,
                        type="UNAPPROVED_TRANSFORMATION",
                    ),
                )

        summary = self.semantic_map.summary or self.semantic_map.computed_summary()
        return TRDEResult(passed=not violations, violations=violations, summary=summary)

    def audit_implicit_assumptions(self) -> ImplicitRiskReport:
        """Report medium/high-risk implicit additions that require approval."""
        flagged: list[ImplicitAddition] = [
            item for item in self.semantic_map.implicit_additions if item.risk != "low"
        ]
        items = [
            ImplicitRiskItem(
                description=item.description,
                justification=item.justification,
                risk=item.risk,
                stage=item.affected_stage,
            )
            for item in flagged
            if item.risk in ("medium", "high")
        ]
        return ImplicitRiskReport(
            total_implicits=len(self.semantic_map.implicit_additions),
            flagged_count=len(items),
            items=items,
        )

    def measure_coverage(self) -> CoverageReport:
        """Measure design-intent implementation and preservation coverage."""
        total = len(self.semantic_map.intent_elements)
        implemented = [
            item for item in self.semantic_map.intent_elements if item.status != "not_implemented"
        ]
        preserved = [item for item in self.semantic_map.intent_elements if item.status == "preserved"]
        unimplemented = [
            CoverageItem(id=item.id, description=item.description)
            for item in self.semantic_map.intent_elements
            if item.status == "not_implemented"
        ]
        return CoverageReport(
            total_intents=total,
            implemented_count=len(implemented),
            preserved_count=len(preserved),
            implementation_rate=len(implemented) / total if total else 0.0,
            preservation_rate=len(preserved) / total if total else 0.0,
            unimplemented=unimplemented,
        )
