from __future__ import annotations

from pathlib import Path

import pytest

from components.edd_reference import ReferenceScenario, load_reference_scenario, resolve_reference_scenario_dir
from components.edd_views import (
    behavior_rules_rows,
    compare_versions_story,
    comparison_metric_rows,
    design_context_rows,
    eval_gates_rows,
    eval_metrics_rows,
    failure_packet_summary,
    fix_plan_sections,
    graph_design_diff,
    graph_node_rows,
    information_requirements_rows,
    production_readiness_blocked,
    target_detail_sections,
    tool_feasibility_rows,
    tool_requirements_rows,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = REPO_ROOT / "examples" / "customer_escalation_triage"


@pytest.fixture(name="reference_scenario")
def fixture_reference_scenario() -> ReferenceScenario:
    return load_reference_scenario(SCENARIO_DIR)


def test_resolve_reference_scenario_dir_finds_repo_examples() -> None:
    assert resolve_reference_scenario_dir() == SCENARIO_DIR


def test_load_reference_scenario(reference_scenario: ReferenceScenario) -> None:
    assert reference_scenario.agent.id == "customer-escalation-triage-agent"
    assert reference_scenario.agent_target.id == "customer-escalation-triage-target-v1"
    assert len(reference_scenario.behavior_rules) == 6
    assert len(reference_scenario.information_requirements) == 6
    assert len(reference_scenario.tool_requirements) == 6
    assert len(reference_scenario.tool_feasibility) == 6
    assert reference_scenario.eval_contract.id == "customer-escalation-triage-eval-contract-v1"
    assert len(reference_scenario.eval_contract.metrics) == 5
    assert len(reference_scenario.eval_contract.gates) == 5
    assert reference_scenario.failure_packet_v0.id == "fp-v0-unsupported-root-cause"
    assert reference_scenario.fix_plan_v1.id == "fix-v1-evidence-first-triage"
    assert reference_scenario.comparison_v0_v1.id == "compare-v0-v1-escalation-triage"
    assert reference_scenario.gate_result_v1.overall_status == "pass_for_demo_not_production"


def test_design_context_rows(reference_scenario: ReferenceScenario) -> None:
    rows = dict(design_context_rows(reference_scenario))
    assert rows["Agent"] == "Customer Escalation Triage Agent"
    assert rows["Target"] == "customer-escalation-triage-target-v1"
    assert rows["Eval Contract"] == "customer-escalation-triage-eval-contract-v1"


def test_target_detail_sections(reference_scenario: ReferenceScenario) -> None:
    sections = target_detail_sections(reference_scenario)
    assert "Purpose" in sections
    assert len(sections["Primary goals"]) >= 5
    assert len(sections["Non-goals"]) >= 4


def test_behavior_rules_rows(reference_scenario: ReferenceScenario) -> None:
    rows = behavior_rules_rows(reference_scenario)
    rule_ids = {row["id"] for row in rows}
    assert "separate_facts_from_hypotheses" in rule_ids
    assert all(row["severity"] for row in rows)


def test_eval_contract_view_rows(reference_scenario: ReferenceScenario) -> None:
    metrics = eval_metrics_rows(reference_scenario)
    gates = eval_gates_rows(reference_scenario)
    assert any(row["id"] == "diagnostic_grounding" for row in metrics)
    assert any(row["id"] == "must_separate_facts_and_hypotheses" for row in gates)


def test_graph_node_rows(reference_scenario: ReferenceScenario) -> None:
    rows = graph_node_rows(reference_scenario.graph_design_v1)
    node_ids = {row["id"] for row in rows}
    assert "separate_facts_hypotheses_unknowns" in node_ids
    assert any(row["tool_mode"] == "mock" for row in rows)


def test_graph_design_diff(reference_scenario: ReferenceScenario) -> None:
    diff = graph_design_diff(reference_scenario.graph_design_v0, reference_scenario.graph_design_v1)
    assert "single_pass_response" in diff["removed_nodes"]
    assert "normalize_evidence" in diff["added_nodes"]


def test_information_requirements_rows(reference_scenario: ReferenceScenario) -> None:
    rows = information_requirements_rows(reference_scenario)
    trace_row = next(row for row in rows if row["id"] == "trace_evidence")
    assert "evidence_first_diagnosis" in trace_row["behavior_rules"]
    assert trace_row["tool_requirements"] == "trace_evidence_source"
    assert trace_row["sensitivity"] == "confidential"


def test_tool_requirements_rows(reference_scenario: ReferenceScenario) -> None:
    rows = tool_requirements_rows(reference_scenario)
    trace_row = next(row for row in rows if row["id"] == "trace_evidence_source")
    assert trace_row["suggested_tool_name"] == "fetch_trace_summary"
    assert trace_row["information_requirement"] == "trace_evidence"
    assert trace_row["implementation_status"] == "mock_only"


def test_tool_feasibility_rows(reference_scenario: ReferenceScenario) -> None:
    rows = tool_feasibility_rows(reference_scenario)
    trace_row = next(row for row in rows if row["requirement_id"] == "trace_evidence_source")
    assert trace_row["demo_ready"] is True
    assert trace_row["production_ready"] is False
    assert trace_row["blocker"] == "langfuse_api_connector"
    assert production_readiness_blocked(reference_scenario) is True


def test_failure_packet_summary(reference_scenario: ReferenceScenario) -> None:
    summary = failure_packet_summary(reference_scenario)
    assert summary["id"] == "fp-v0-unsupported-root-cause"
    assert summary["failed_rule"] == "separate_facts_from_hypotheses"
    assert summary["severity"] == "critical"
    assert "prompt change" in summary["observed_behavior"].lower()


def test_fix_plan_sections(reference_scenario: ReferenceScenario) -> None:
    sections = fix_plan_sections(reference_scenario)
    assert "separate_facts_from_hypotheses" in sections["Rules addressed"]
    assert any("normalize_evidence" in item for item in sections["Graph changes"])


def test_compare_versions_story(reference_scenario: ReferenceScenario) -> None:
    rows = comparison_metric_rows(reference_scenario)
    assert any(row["metric"] == "diagnostic_grounding" for row in rows)
    story = compare_versions_story(reference_scenario)
    assert any("fp-v0-unsupported-root-cause" in line for line in story)
    assert any("mock/local" in line.lower() for line in story)
