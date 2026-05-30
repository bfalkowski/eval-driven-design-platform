from __future__ import annotations

from pathlib import Path

import pytest

from components.edd_reference import ReferenceScenario, load_reference_scenario, resolve_reference_scenario_dir
from components.edd_views import (
    behavior_rules_rows,
    design_context_rows,
    eval_gates_rows,
    eval_metrics_rows,
    graph_design_diff,
    graph_node_rows,
    target_detail_sections,
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
    assert reference_scenario.eval_contract.id == "customer-escalation-triage-eval-contract-v1"
    assert len(reference_scenario.eval_contract.metrics) == 5
    assert len(reference_scenario.eval_contract.gates) == 5


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
