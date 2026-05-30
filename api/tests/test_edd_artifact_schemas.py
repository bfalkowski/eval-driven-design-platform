from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.edd.agent import Agent, AgentTarget
from app.domain.edd.artifacts import load_graph_design_bundle, load_yaml_document
from app.domain.edd.eval_contract import EvalContract
from app.domain.edd.requirements import (
    InformationRequirement,
    ToolBinding,
    ToolFeasibilityReview,
    ToolRequirement,
)
from app.domain.edd.rules import BehaviorRule

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_DIR = REPO_ROOT / "examples" / "customer_escalation_triage"


@pytest.fixture(name="reference_artifacts")
def fixture_reference_artifacts() -> dict[str, object]:
    agent_target_doc = load_yaml_document(SCENARIO_DIR / "agent-target.yaml")
    behavior_rules_doc = load_yaml_document(SCENARIO_DIR / "behavior-rules.yaml")
    eval_contract_doc = load_yaml_document(SCENARIO_DIR / "eval-contract.yaml")
    information_doc = load_yaml_document(SCENARIO_DIR / "information-requirements.yaml")
    tool_requirements_doc = load_yaml_document(SCENARIO_DIR / "tool-requirements.yaml")
    tool_feasibility_doc = load_yaml_document(SCENARIO_DIR / "tool-feasibility.yaml")
    tool_bindings_doc = load_yaml_document(SCENARIO_DIR / "tool-bindings.yaml")

    agent = Agent.model_validate(agent_target_doc["agent"])
    agent_target = AgentTarget.model_validate(agent_target_doc["agent_target"])
    behavior_rules = [
        BehaviorRule.model_validate(item) for item in behavior_rules_doc["behavior_rules"]
    ]
    eval_contract = EvalContract.model_validate(eval_contract_doc["eval_contract"])
    information_requirements = [
        InformationRequirement.model_validate(item)
        for item in information_doc["information_requirements"]
    ]
    tool_requirements = [
        ToolRequirement.model_validate(item) for item in tool_requirements_doc["tool_requirements"]
    ]
    tool_feasibility = [
        ToolFeasibilityReview.model_validate(item)
        for item in tool_feasibility_doc["tool_feasibility"]
    ]
    tool_bindings = [
        ToolBinding.model_validate(item) for item in tool_bindings_doc["tool_bindings"]
    ]
    graph_design_v0, graph_nodes_v0 = load_graph_design_bundle(
        SCENARIO_DIR / "graph-design-v0.yaml"
    )
    graph_design_v1, graph_nodes_v1 = load_graph_design_bundle(
        SCENARIO_DIR / "graph-design-v1.yaml"
    )

    return {
        "agent": agent,
        "agent_target": agent_target,
        "behavior_rules": behavior_rules,
        "eval_contract": eval_contract,
        "information_requirements": information_requirements,
        "tool_requirements": tool_requirements,
        "tool_feasibility": tool_feasibility,
        "tool_bindings": tool_bindings,
        "graph_design_v0": graph_design_v0,
        "graph_nodes_v0": graph_nodes_v0,
        "graph_design_v1": graph_design_v1,
        "graph_nodes_v1": graph_nodes_v1,
    }


def test_reference_yaml_files_validate(reference_artifacts: dict[str, object]) -> None:
    assert reference_artifacts["agent"].id == "customer-escalation-triage-agent"
    assert reference_artifacts["agent_target"].id == "customer-escalation-triage-target-v1"
    assert len(reference_artifacts["behavior_rules"]) == 6
    assert len(reference_artifacts["information_requirements"]) == 6
    assert len(reference_artifacts["tool_requirements"]) == 6
    assert len(reference_artifacts["tool_feasibility"]) == 6
    assert len(reference_artifacts["tool_bindings"]) == 6


def test_reference_artifact_cross_references(reference_artifacts: dict[str, object]) -> None:
    agent = reference_artifacts["agent"]
    agent_target = reference_artifacts["agent_target"]
    behavior_rules = reference_artifacts["behavior_rules"]
    eval_contract = reference_artifacts["eval_contract"]
    information_requirements = reference_artifacts["information_requirements"]
    tool_requirements = reference_artifacts["tool_requirements"]
    tool_feasibility = reference_artifacts["tool_feasibility"]
    tool_bindings = reference_artifacts["tool_bindings"]

    assert agent_target.agent_id == agent.id

    rule_ids = {rule.id for rule in behavior_rules}
    assert all(rule.agent_target_id == agent_target.id for rule in behavior_rules)

    assert eval_contract.agent_target_id == agent_target.id
    for metric in eval_contract.metrics:
        assert set(metric.behavior_rule_ids).issubset(rule_ids)

    info_ids = {item.id for item in information_requirements}
    assert all(item.agent_target_id == agent_target.id for item in information_requirements)

    tool_req_ids = {item.id for item in tool_requirements}
    for tool_requirement in tool_requirements:
        assert tool_requirement.information_requirement_id in info_ids

    for review in tool_feasibility:
        assert review.requirement_id in tool_req_ids
        matching = next(item for item in tool_requirements if item.id == review.requirement_id)
        assert review.suggested_tool_name == matching.suggested_tool_name
        assert review.production_ready is False

    for binding in tool_bindings:
        assert binding.requirement_id in tool_req_ids
        assert binding.active_implementation
        assert binding.mode in {"mock", "local", "live"}


def test_tool_requirement_is_distinct_from_feasibility_and_binding(
    reference_artifacts: dict[str, object],
) -> None:
    tool_requirements = reference_artifacts["tool_requirements"]
    tool_feasibility = reference_artifacts["tool_feasibility"]
    tool_bindings = reference_artifacts["tool_bindings"]

    tool_req_ids = {item.id for item in tool_requirements}
    binding_nodes = {item.graph_node for item in tool_bindings}
    assert tool_req_ids.isdisjoint(binding_nodes)
    assert all(item.suggested_tool_name for item in tool_requirements)
    assert all(item.implementation_status for item in tool_feasibility)
    assert all(item.active_implementation for item in tool_bindings)


def test_graph_design_yaml_files_validate(reference_artifacts: dict[str, object]) -> None:
    graph_design_v0 = reference_artifacts["graph_design_v0"]
    graph_nodes_v0 = reference_artifacts["graph_nodes_v0"]
    graph_design_v1 = reference_artifacts["graph_design_v1"]
    graph_nodes_v1 = reference_artifacts["graph_nodes_v1"]

    assert graph_design_v0.id == "customer-escalation-triage-graph-v0"
    assert graph_design_v1.id == "customer-escalation-triage-graph-v1"
    assert len(graph_nodes_v0) == 2
    assert len(graph_nodes_v1) == 16
    assert graph_design_v1.source_version == "v0-baseline"
    assert graph_design_v1.fix_plan_id == "fix-v1-evidence-first-triage"


def test_graph_design_cross_references(reference_artifacts: dict[str, object]) -> None:
    agent_target = reference_artifacts["agent_target"]
    eval_contract = reference_artifacts["eval_contract"]
    behavior_rules = reference_artifacts["behavior_rules"]
    information_requirements = reference_artifacts["information_requirements"]
    tool_requirements = reference_artifacts["tool_requirements"]
    tool_bindings = reference_artifacts["tool_bindings"]
    graph_design_v1 = reference_artifacts["graph_design_v1"]
    graph_nodes_v1 = reference_artifacts["graph_nodes_v1"]

    rule_ids = {rule.id for rule in behavior_rules}
    info_ids = {item.id for item in information_requirements}
    tool_req_ids = {item.id for item in tool_requirements}
    binding_nodes = {item.graph_node for item in tool_bindings}

    assert graph_design_v1.agent_target_id == agent_target.id
    assert graph_design_v1.eval_contract_id == eval_contract.id

    node_ids = {node.id for node in graph_nodes_v1}
    assert set(graph_design_v1.flow_order).issubset(node_ids)

    for node in graph_nodes_v1:
        assert set(node.behavior_rule_ids).issubset(rule_ids)
        assert set(node.information_requirement_ids).issubset(info_ids)
        assert set(node.tool_requirement_ids).issubset(tool_req_ids)
        if node.active_tool_binding:
            assert node.tool_mode in {"mock", "local", "live"}

    assert binding_nodes.issubset(node_ids)
    assert "separate_facts_hypotheses_unknowns" in node_ids
    separate_node = next(
        node for node in graph_nodes_v1 if node.id == "separate_facts_hypotheses_unknowns"
    )
    assert "fp-v0-unsupported-root-cause" in separate_node.failure_packets_addressed


def test_graph_design_v0_to_v1_diff(reference_artifacts: dict[str, object]) -> None:
    graph_nodes_v0 = reference_artifacts["graph_nodes_v0"]
    graph_nodes_v1 = reference_artifacts["graph_nodes_v1"]

    v0_ids = {node.id for node in graph_nodes_v0}
    v1_ids = {node.id for node in graph_nodes_v1}
    added = v1_ids - v0_ids
    removed = v0_ids - v1_ids

    assert "single_pass_response" in removed
    assert "normalize_evidence" in added
    assert "separate_facts_hypotheses_unknowns" in added
    assert "collect_trace_evidence" in added
