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


def _tool_requirements_by_information(
    scenario: ReferenceScenario,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for tool_requirement in scenario.tool_requirements:
        grouped.setdefault(tool_requirement.information_requirement_id, []).append(
            tool_requirement.id
        )
    return grouped


def _feasibility_by_requirement(
    scenario: ReferenceScenario,
) -> dict[str, Any]:
    return {review.requirement_id: review for review in scenario.tool_feasibility}


def information_requirements_rows(scenario: ReferenceScenario) -> list[dict[str, Any]]:
    tool_by_info = _tool_requirements_by_information(scenario)
    rows: list[dict[str, Any]] = []
    for item in scenario.information_requirements:
        rows.append(
            {
                "id": item.id,
                "name": item.name,
                "required": item.required,
                "sensitivity": item.sensitivity,
                "behavior_rules": ", ".join(item.behavior_rule_ids),
                "tool_requirements": ", ".join(tool_by_info.get(item.id, [])),
                "description": item.description.strip(),
            }
        )
    return rows


def tool_requirements_rows(scenario: ReferenceScenario) -> list[dict[str, Any]]:
    feasibility_by_req = _feasibility_by_requirement(scenario)
    rows: list[dict[str, Any]] = []
    for item in scenario.tool_requirements:
        review = feasibility_by_req.get(item.id)
        rows.append(
            {
                "id": item.id,
                "suggested_tool_name": item.suggested_tool_name,
                "information_requirement": item.information_requirement_id,
                "access_mode": item.access_mode,
                "required_for_demo": item.required_for_demo,
                "required_for_production": item.required_for_production,
                "implementation_status": review.implementation_status if review else "",
                "purpose": item.purpose.strip(),
            }
        )
    return rows


def tool_feasibility_rows(scenario: ReferenceScenario) -> list[dict[str, Any]]:
    tool_by_id = {item.id: item for item in scenario.tool_requirements}
    rows: list[dict[str, Any]] = []
    for review in scenario.tool_feasibility:
        tool_requirement = tool_by_id.get(review.requirement_id)
        blocker = ""
        if tool_requirement and tool_requirement.required_for_production and not review.production_ready:
            blocker = review.production_strategy
        rows.append(
            {
                "requirement_id": review.requirement_id,
                "suggested_tool_name": review.suggested_tool_name,
                "implementation_status": review.implementation_status,
                "feasibility_status": review.feasibility_status,
                "demo_ready": review.demo_ready,
                "production_ready": review.production_ready,
                "mvp_strategy": review.mvp_strategy,
                "production_strategy": review.production_strategy,
                "blocker": blocker,
                "risks": "; ".join(review.risks),
            }
        )
    return rows


def production_readiness_blocked(scenario: ReferenceScenario) -> bool:
    tool_by_id = {item.id: item for item in scenario.tool_requirements}
    for review in scenario.tool_feasibility:
        tool_requirement = tool_by_id.get(review.requirement_id)
        if (
            tool_requirement is not None
            and tool_requirement.required_for_production
            and not review.production_ready
        ):
            return True
    return False


def failure_packet_summary(scenario: ReferenceScenario) -> dict[str, str]:
    packet = scenario.failure_packet_v0
    return {
        "id": packet.id,
        "failed_rule": packet.failed_behavior_rule_id or "",
        "severity": packet.severity or "",
        "version": packet.agent_version_id or "v0-baseline",
        "observed_behavior": packet.observed_behavior or "",
        "expected_behavior": packet.expected_behavior or "",
        "recommended_fix": packet.recommended_fix or "",
    }


def fix_plan_sections(scenario: ReferenceScenario) -> dict[str, list[str]]:
    plan = scenario.fix_plan_v1
    return {
        "Rules addressed": plan.behavior_rule_ids_addressed,
        "Graph changes": plan.graph_changes,
        "Tool changes": plan.tool_changes,
        "Prompt changes": plan.prompt_changes,
        "Non-goals": plan.non_goals,
        "Regression risks": plan.regression_risks,
    }


def comparison_metric_rows(scenario: ReferenceScenario) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric_id, delta in scenario.comparison_v0_v1.score_deltas.items():
        if hasattr(delta, "baseline"):
            rows.append(
                {
                    "metric": metric_id,
                    "baseline": delta.baseline,
                    "candidate": delta.candidate,
                    "delta": delta.delta,
                }
            )
        else:
            rows.append({"metric": metric_id, "baseline": delta, "candidate": "", "delta": ""})
    return rows


def compare_versions_story(scenario: ReferenceScenario) -> list[str]:
    comparison = scenario.comparison_v0_v1
    gate = scenario.gate_result_v1
    lines = [
        f"{comparison.baseline_version_id} guessed the root cause.",
        (
            f"{comparison.candidate_version_id} separated facts, hypotheses, and unknowns."
        ),
    ]
    for row in comparison_metric_rows(scenario):
        if row.get("delta") not in (None, ""):
            lines.append(
                f"{row['metric'].replace('_', ' ').title()} improved from "
                f"{row['baseline']} to {row['candidate']} (Δ {row['delta']})."
            )
    if comparison.resolved_failure_packet_ids:
        lines.append(
            "Resolved failures: " + ", ".join(comparison.resolved_failure_packet_ids) + "."
        )
    if gate.overall_status == "pass_for_demo_not_production":
        lines.append(
            "Production readiness remains blocked because required tools are mock/local."
        )
    return lines


def trace_link_rows(scenario: ReferenceScenario) -> list[dict[str, str]]:
    links = [scenario.trace_link_v0, scenario.trace_link_v1]
    rows: list[dict[str, str]] = []
    for link in links:
        rows.append(
            {
                "id": link.id,
                "provider": link.provider,
                "external_trace_id": link.external_trace_id,
                "external_url": link.external_url or "",
                "agent_version_id": link.agent_version_id or "",
                "scenario_id": link.scenario_id or "",
            }
        )
    return rows
