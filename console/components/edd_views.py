from __future__ import annotations

from typing import Any

from components.edd_reference import ReferenceScenario


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
