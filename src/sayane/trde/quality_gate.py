"""T-RDE quality gate."""

from __future__ import annotations

from dataclasses import dataclass

from sayane.trde.runner import CoverageReport, ImplicitRiskReport, TRDEResult


@dataclass(frozen=True)
class QualityGate:
    min_coverage_rate: float = 0.8
    min_preservation_rate: float = 0.5
    max_deviation_severity: float = 0.6
    max_high_risk_implicits: int = 0


@dataclass(frozen=True)
class QualityGateResult:
    passed: bool
    reasons: list[str]


def evaluate_quality_gate(
    coverage: CoverageReport,
    deviations: TRDEResult,
    implicits: ImplicitRiskReport,
    gate: QualityGate | None = None,
) -> QualityGateResult:
    """Evaluate T-RDE quality gate.

    The gate must fail on meaning drift even if UI/API tests are green.
    """
    active_gate = gate or QualityGate()
    reasons: list[str] = []

    if coverage.implementation_rate < active_gate.min_coverage_rate:
        reasons.append(
            "implementation coverage "
            f"{coverage.implementation_rate:.2f} < {active_gate.min_coverage_rate:.2f}",
        )

    if coverage.preservation_rate < active_gate.min_preservation_rate:
        reasons.append(
            "meaning preservation "
            f"{coverage.preservation_rate:.2f} < {active_gate.min_preservation_rate:.2f}",
        )

    if not deviations.passed:
        reasons.append(f"semantic violations detected: {len(deviations.violations)}")

    max_violation_severity = max((item.severity for item in deviations.violations), default=0.0)
    if max_violation_severity > active_gate.max_deviation_severity:
        reasons.append(
            "max deviation severity "
            f"{max_violation_severity:.2f} > {active_gate.max_deviation_severity:.2f}",
        )

    high_risk_count = sum(1 for item in implicits.items if item.risk == "high")
    if high_risk_count > active_gate.max_high_risk_implicits:
        reasons.append(
            f"high-risk implicit additions {high_risk_count} > "
            f"{active_gate.max_high_risk_implicits}",
        )

    return QualityGateResult(passed=not reasons, reasons=reasons)
