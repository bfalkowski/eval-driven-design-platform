from __future__ import annotations

from typing import Any

from components.edd_reference import GraphDesignBundle, ReferenceScenario


def design_context_rows(scenario: ReferenceScenario) -> list[tuple[str, str]]:
    return [
        ("Agent", scenario.agent.name),
        ("Target", scenario.agent_target.id),
        ("Eval Contract", scenario.eval_contract.id),
        ("Target Version", scenario.agent_target.version),
        ("Contract Version", scenario.eval_contract.version),
        ("Source", str(scenario.scenario_dir)),
    ]


def target_detail_sections(scenario: ReferenceScenario) -> dict[str, list[str]]:
    target = scenario.agent_target
    return {
        "Purpose": [target.purpose.strip()],
        "Intended users": target.intended_users,
        "Primary goals": target.primary_goals,
        "Non-goals": target.non_goals,
        "Risk areas": target.risk_areas,
    }


def behavior_rules_rows(scenario: ReferenceScenario) -> list[dict[str, str]]:
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "severity": rule.severity,
            "category": rule.category,
            "description": rule.description.strip(),
        }
        for rule in scenario.behavior_rules
    ]


def eval_metrics_rows(scenario: ReferenceScenario) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in scenario.eval_contract.metrics:
        rows.append(
            {
                "id": metric.id,
                "name": metric.name,
                "scale": f"{metric.scale_min:g}-{metric.scale_max:g}",
                "behavior_rules": ", ".join(metric.behavior_rule_ids),
                "rubric": metric.rubric.strip(),
            }
        )
    return rows


def eval_gates_rows(scenario: ReferenceScenario) -> list[dict[str, str]]:
    return [
        {
            "id": gate.id,
            "name": gate.name,
            "type": gate.gate_type,
            "category": gate.category,
            "condition": gate.condition,
        }
        for gate in scenario.eval_contract.gates
    ]


def graph_node_rows(bundle: GraphDesignBundle) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node in bundle.nodes:
        rows.append(
            {
                "id": node.id,
                "purpose": node.purpose.strip(),
                "behavior_rules": ", ".join(node.behavior_rule_ids),
                "information_requirements": ", ".join(node.information_requirement_ids),
                "tool_requirements": ", ".join(node.tool_requirement_ids),
                "tool_mode": node.tool_mode or "",
                "active_tool_binding": node.active_tool_binding or "",
                "production_blocker": node.production_blocker is True,
                "failure_packets": ", ".join(node.failure_packets_addressed),
            }
        )
    return rows


def graph_design_summary(bundle: GraphDesignBundle) -> dict[str, str]:
    design = bundle.design
    return {
        "id": design.id,
        "version": design.version,
        "name": design.name,
        "description": design.description.strip(),
        "source_version": design.source_version or "",
        "fix_plan_id": design.fix_plan_id or "",
        "status": design.status,
        "node_count": str(len(bundle.nodes)),
    }


def graph_design_diff(
    baseline: GraphDesignBundle,
    candidate: GraphDesignBundle,
) -> dict[str, list[str]]:
    baseline_ids = {node.id for node in baseline.nodes}
    candidate_ids = {node.id for node in candidate.nodes}
    return {
        "added_nodes": sorted(candidate_ids - baseline_ids),
        "removed_nodes": sorted(baseline_ids - candidate_ids),
        "shared_nodes": sorted(baseline_ids & candidate_ids),
    }
