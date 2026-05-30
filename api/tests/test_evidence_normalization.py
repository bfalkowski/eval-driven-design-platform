from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.edd.artifacts import load_yaml_document
from app.domain.edd.evidence import Comparison, FixPlan, VersionGateSummary
from app.services.evidence_normalization import (
    normalize_comparison,
    normalize_failure_packet,
    normalize_fix_plan,
    normalize_run_evidence,
    normalize_trace_link,
    normalize_trace_links,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = REPO_ROOT / "examples" / "customer_escalation_triage"


@pytest.fixture(name="evidence_artifacts")
def fixture_evidence_artifacts() -> dict[str, object]:
    failure_doc = load_yaml_document(SCENARIO_DIR / "failure-packet-v0.yaml")
    fix_plan_doc = load_yaml_document(SCENARIO_DIR / "fix-plan-v1.yaml")
    comparison_doc = load_yaml_document(SCENARIO_DIR / "comparison-v0-v1.yaml")
    gate_doc = load_yaml_document(SCENARIO_DIR / "gate-result-v1.yaml")

    fix_plan = normalize_fix_plan(fix_plan_doc["fix_plan"])
    comparison = normalize_comparison(comparison_doc["comparison"])
    assert fix_plan is not None
    assert comparison is not None

    failure_packet = normalize_failure_packet(failure_doc["failure_packet"])
    assert failure_packet is not None

    return {
        "failure_packet": failure_packet,
        "fix_plan": FixPlan.model_validate(fix_plan.model_dump()),
        "comparison": Comparison.model_validate(comparison.model_dump()),
        "gate_result": VersionGateSummary.model_validate(gate_doc["gate_result"]),
    }


def test_reference_evidence_yaml_files_validate(evidence_artifacts: dict[str, object]) -> None:
    failure = evidence_artifacts["failure_packet"]
    assert failure.id == "fp-v0-unsupported-root-cause"
    assert failure.failed_behavior_rule_id == "separate_facts_from_hypotheses"
    assert failure.trace_link_ids == ["trace_v0_abc123", "run_v0_001"]

    fix_plan = evidence_artifacts["fix_plan"]
    assert fix_plan.id == "fix-v1-evidence-first-triage"
    assert "separate_facts_from_hypotheses" in fix_plan.behavior_rule_ids_addressed

    comparison = evidence_artifacts["comparison"]
    assert comparison.id == "compare-v0-v1-escalation-triage"
    assert "fp-v0-unsupported-root-cause" in comparison.resolved_failure_packet_ids
    delta = comparison.score_deltas["diagnostic_grounding"]
    assert delta.baseline == 2
    assert delta.candidate == 5
    assert delta.delta == 3

    gate = evidence_artifacts["gate_result"]
    assert gate.overall_status == "pass_for_demo_not_production"


def test_normalize_failure_packet_legacy_blob() -> None:
    packet = normalize_failure_packet(
        {"failure_type": "overfitting", "summary": "High overfitting risk."},
        agent_version_id="v0-baseline",
    )
    assert packet is not None
    assert packet.id == "fp-overfitting"
    assert packet.failure_type == "overfitting"


def test_normalize_run_evidence_from_reference_docs() -> None:
    failure_doc = load_yaml_document(SCENARIO_DIR / "failure-packet-v0.yaml")
    fix_plan_doc = load_yaml_document(SCENARIO_DIR / "fix-plan-v1.yaml")
    comparison_doc = load_yaml_document(SCENARIO_DIR / "comparison-v0-v1.yaml")
    gate_doc = load_yaml_document(SCENARIO_DIR / "gate-result-v1.yaml")

    evidence = normalize_run_evidence(
        experiment_run_id="00000000-0000-0000-0000-000000000001",
        agent_version_id="v0-baseline",
        failure_packet=failure_doc["failure_packet"],
        fix_plan=fix_plan_doc["fix_plan"],
        comparison=comparison_doc["comparison"],
        gate_result=gate_doc["gate_result"],
    )

    assert evidence.failure_packet is not None
    assert evidence.fix_plan is not None
    assert evidence.comparison is not None
    assert evidence.gate_result is not None
    assert evidence.failure_packet.experiment_run_id == "00000000-0000-0000-0000-000000000001"


def test_normalize_trace_link_from_reference_yaml() -> None:
    trace_doc = load_yaml_document(SCENARIO_DIR / "trace-link-v0.yaml")
    links = normalize_trace_links(
        trace_doc["trace_links"],
        agent_version_id="v0-baseline",
    )
    assert len(links) == 1
    assert links[0].id == "trace-link-v0-001"
    assert links[0].external_trace_id == "trace_v0_abc123"
    assert links[0].provider == "langfuse"


def test_normalize_trace_link_generates_id_from_external_trace_id() -> None:
    link = normalize_trace_link({"external_trace_id": "trace_v0_abc123"})
    assert link is not None
    assert link.id == "trace-link-trace_v0_abc123"
