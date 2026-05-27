from pathlib import Path

from sayane.trde import QualityGate, TRDERunner, evaluate_quality_gate, load_semantic_map

FIXTURES = Path(__file__).parent / "fixtures" / "trde"


def test_trde_detects_unintended_deviation_and_high_risk_implicit() -> None:
    semantic_map = load_semantic_map(FIXTURES / "todo-app.semantic.yaml")
    runner = TRDERunner(semantic_map)

    deviations = runner.audit_deviations()
    implicits = runner.audit_implicit_assumptions()
    coverage = runner.measure_coverage()
    gate = evaluate_quality_gate(coverage, deviations, implicits)

    assert not deviations.passed
    assert any(v.type == "UNINTENDED_DEVIATION" for v in deviations.violations)
    assert implicits.flagged_count == 1
    assert implicits.items[0].risk == "high"
    assert coverage.implementation_rate == 0.8
    assert not gate.passed
    assert any("semantic violations" in reason for reason in gate.reasons)
    assert any("high-risk implicit" in reason for reason in gate.reasons)


def test_trde_passes_when_sayane_design_principles_are_preserved() -> None:
    semantic_map = load_semantic_map(FIXTURES / "sayane-principle.semantic.yaml")
    runner = TRDERunner(semantic_map)

    deviations = runner.audit_deviations()
    implicits = runner.audit_implicit_assumptions()
    coverage = runner.measure_coverage()
    gate = evaluate_quality_gate(coverage, deviations, implicits)

    assert deviations.passed
    assert implicits.flagged_count == 0
    assert coverage.implementation_rate == 1.0
    assert coverage.preservation_rate == 1.0
    assert gate.passed


def test_trde_quality_gate_thresholds_are_configurable() -> None:
    semantic_map = load_semantic_map(FIXTURES / "todo-app.semantic.yaml")
    runner = TRDERunner(semantic_map)

    deviations = runner.audit_deviations()
    implicits = runner.audit_implicit_assumptions()
    coverage = runner.measure_coverage()
    gate = evaluate_quality_gate(
        coverage,
        deviations,
        implicits,
        QualityGate(
            min_coverage_rate=0.8,
            min_preservation_rate=0.5,
            max_deviation_severity=0.9,
            max_high_risk_implicits=1,
        ),
    )

    # Even permissive thresholds must not hide actual semantic violations.
    assert not gate.passed
    assert any("semantic violations" in reason for reason in gate.reasons)
