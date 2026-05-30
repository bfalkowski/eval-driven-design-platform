from __future__ import annotations

from app.services.readiness_evaluation import compute_gate, evaluate_readiness


def test_evaluate_readiness_behavior_pass_without_tool_metadata() -> None:
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=88.0,
        failure_packet=None,
    )
    assert evaluation.behavior_status == "pass"
    assert evaluation.tool_status == "not_declared"
    assert evaluation.production_status == "not_evaluated"
    assert evaluation.overall_status == "pass"
    assert evaluation.gate_status == "pass"


def test_evaluate_readiness_pass_for_demo_not_production() -> None:
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=88.0,
        failure_packet=None,
        tool_mode_summary="mock_local",
        production_ready=False,
    )
    assert evaluation.behavior_status == "pass"
    assert evaluation.tool_status == "mock_local"
    assert evaluation.production_status == "blocked"
    assert evaluation.overall_status == "pass_for_demo_not_production"
    assert evaluation.gate_status == "pass"
    assert "pass_for_demo_not_production" in evaluation.gate_explanation


def test_evaluate_readiness_infers_tool_mode_from_bindings() -> None:
    bindings = [
        {"mode": "mock", "requirement_id": "trace_evidence_source"},
        {"mode": "local", "requirement_id": "customer_report_source"},
    ]
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=90.0,
        failure_packet=None,
        tool_bindings=bindings,
        production_ready=False,
    )
    assert evaluation.tool_status == "mock_local"
    assert evaluation.overall_status == "pass_for_demo_not_production"


def test_evaluate_readiness_structured_failure_includes_rule_id() -> None:
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=95.0,
        failure_packet={
            "id": "fp-v0-unsupported-root-cause",
            "failed_rule": "separate_facts_from_hypotheses",
        },
    )
    assert evaluation.behavior_status == "fail"
    assert "separate_facts_from_hypotheses" in evaluation.gate_explanation


def test_evaluate_readiness_failure_packet_fails_all_dimensions() -> None:
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=95.0,
        failure_packet={"failure_type": "unsupported_root_cause"},
    )
    assert evaluation.behavior_status == "fail"
    assert evaluation.overall_status == "fail"
    assert evaluation.gate_status == "fail"


def test_evaluate_readiness_rejects_conflicting_production_ready_flag() -> None:
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=95.0,
        failure_packet=None,
        tool_mode_summary="mock_only",
        production_ready=True,
    )
    assert evaluation.production_status == "blocked"
    assert evaluation.overall_status == "pass_for_demo_not_production"


def test_compute_gate_preserves_legacy_pass_fail_values() -> None:
    status, _ = compute_gate(pass_threshold=70.0, overall_score=77.3, failure_packet=None)
    assert status == "pass"
    status, _ = compute_gate(pass_threshold=80.0, overall_score=77.3, failure_packet=None)
    assert status == "fail"
    status, explanation = compute_gate(
        pass_threshold=70.0,
        overall_score=90.0,
        failure_packet={"failure_type": "overfitting"},
    )
    assert status == "fail"
    assert "overfitting" in explanation


def test_reference_scenario_tool_bindings_block_production() -> None:
    bindings = [
        {"mode": "local", "requirement_id": "customer_report_source"},
        {"mode": "mock", "requirement_id": "trace_evidence_source"},
        {"mode": "local", "requirement_id": "eval_history_source"},
        {"mode": "mock", "requirement_id": "recent_changes_source"},
        {"mode": "mock", "requirement_id": "tool_health_source"},
        {"mode": "local", "requirement_id": "customer_context_source"},
    ]
    evaluation = evaluate_readiness(
        pass_threshold=70.0,
        overall_score=92.0,
        failure_packet=None,
        tool_mode_summary="mock_local",
        production_ready=False,
        tool_bindings=bindings,
    )
    assert evaluation.overall_status == "pass_for_demo_not_production"
    assert evaluation.production_status == "blocked"
