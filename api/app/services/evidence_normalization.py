from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.edd.evidence import (
    Comparison,
    ComparisonMetricDelta,
    FailurePacket,
    FixPlan,
    RunEvidence,
    VersionGateSummary,
)
from app.domain.edd.trace_link import TraceLink


def normalize_run_evidence(
    *,
    experiment_run_id: UUID | str | None = None,
    agent_version_id: str | None = None,
    failure_packet: dict[str, Any] | None = None,
    fix_plan: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
    gate_result: dict[str, Any] | None = None,
    trace_links: list[dict[str, Any]] | None = None,
) -> RunEvidence:
    run_id = str(experiment_run_id) if experiment_run_id is not None else None
    normalized_trace_links = normalize_trace_links(
        trace_links,
        experiment_run_id=run_id,
        agent_version_id=agent_version_id,
    )
    return RunEvidence(
        failure_packet=normalize_failure_packet(
            failure_packet,
            experiment_run_id=run_id,
            agent_version_id=agent_version_id,
        )
        if failure_packet
        else None,
        fix_plan=normalize_fix_plan(fix_plan) if fix_plan else None,
        comparison=normalize_comparison(comparison) if comparison else None,
        gate_result=normalize_gate_result(gate_result) if gate_result else None,
        trace_links=normalized_trace_links,
    )


def normalize_failure_packet(
    payload: dict[str, Any],
    *,
    experiment_run_id: str | None = None,
    agent_version_id: str | None = None,
) -> FailurePacket | None:
    if not payload:
        return None

    packet_id = _string(payload.get("id"))
    if not packet_id:
        failure_type = _string(payload.get("failure_type"))
        packet_id = f"fp-{failure_type}" if failure_type else "ingest-failure"

    trace_evidence = payload.get("trace_evidence") or {}
    trace_link_ids: list[str] = []
    if isinstance(trace_evidence, dict):
        for key in ("langfuse_trace_id", "platform_run_id", "trace_id"):
            value = _string(trace_evidence.get(key))
            if value:
                trace_link_ids.append(value)
    for item in payload.get("trace_link_ids") or []:
        value = _string(item)
        if value:
            trace_link_ids.append(value)

    failed_rule = _string(payload.get("failed_behavior_rule_id") or payload.get("failed_rule"))

    return FailurePacket(
        id=packet_id,
        experiment_run_id=experiment_run_id or _string(payload.get("experiment_run_id")),
        agent_version_id=agent_version_id
        or _string(payload.get("agent_version_id") or payload.get("version")),
        scenario_id=_string(payload.get("scenario_id")),
        failed_behavior_rule_id=failed_rule,
        severity=_string(payload.get("severity")),
        observed_behavior=_string(payload.get("observed_behavior")),
        expected_behavior=_string(payload.get("expected_behavior")),
        suspected_cause=_string(payload.get("suspected_cause")),
        recommended_fix=_string(payload.get("recommended_fix")),
        trace_link_ids=trace_link_ids,
        status=_string(payload.get("status")) or "open",
        failure_type=_string(payload.get("failure_type")),
        summary=_string(payload.get("summary")),
    )


def normalize_fix_plan(payload: dict[str, Any]) -> FixPlan | None:
    if not payload:
        return None

    plan_id = _string(payload.get("id"))
    if not plan_id:
        return None

    addressed = payload.get("behavior_rule_ids_addressed") or payload.get(
        "failed_rules_addressed"
    ) or []
    failure_packet_ids = list(payload.get("failure_packet_ids") or [])
    if not failure_packet_ids:
        single = _string(payload.get("failure_packet_id"))
        if single:
            failure_packet_ids = [single]

    return FixPlan(
        id=plan_id,
        source_version_id=_string(
            payload.get("source_version_id") or payload.get("source_version")
        ),
        target_version_label=_string(
            payload.get("target_version_label") or payload.get("target_version")
        ),
        failure_packet_ids=_string_list(failure_packet_ids),
        behavior_rule_ids_addressed=_string_list(addressed),
        graph_changes=_string_list(payload.get("graph_changes")),
        prompt_changes=_string_list(payload.get("prompt_changes")),
        tool_changes=_string_list(payload.get("tool_changes")),
        non_goals=_string_list(payload.get("non_goals")),
        regression_risks=_string_list(payload.get("regression_risks")),
        status=_string(payload.get("status")) or "draft",
    )


def normalize_comparison(payload: dict[str, Any]) -> Comparison | None:
    if not payload:
        return None

    comparison_id = _string(payload.get("id"))
    if not comparison_id:
        return None

    raw_deltas = payload.get("score_deltas") or payload.get("score_delta") or {}
    score_deltas: dict[str, ComparisonMetricDelta | dict[str, Any]] = {}
    if isinstance(raw_deltas, dict):
        for metric_id, value in raw_deltas.items():
            if isinstance(value, dict):
                normalized_value = dict(value)
                if "baseline" not in normalized_value and "v0" in normalized_value:
                    normalized_value["baseline"] = normalized_value.pop("v0")
                if "candidate" not in normalized_value and "v1" in normalized_value:
                    normalized_value["candidate"] = normalized_value.pop("v1")
                metric_delta = ComparisonMetricDelta.model_validate(normalized_value)
                score_deltas[str(metric_id)] = metric_delta
            else:
                score_deltas[str(metric_id)] = value

    resolved = payload.get("resolved_failure_packet_ids") or payload.get("resolved_failures") or []
    new_failures = payload.get("new_failure_packet_ids") or payload.get("new_failures") or []

    return Comparison(
        id=comparison_id,
        baseline_version_id=_string(payload.get("baseline_version_id")),
        candidate_version_id=_string(payload.get("candidate_version_id")),
        target_id=_string(payload.get("target_id")),
        eval_contract_id=_string(payload.get("eval_contract_id")),
        scenario_set_id=_string(payload.get("scenario_set_id")),
        score_deltas=score_deltas,
        resolved_failure_packet_ids=[str(item) for item in resolved if str(item).strip()],
        new_failure_packet_ids=[str(item) for item in new_failures if str(item).strip()],
        regression_warnings=[
            str(item) for item in payload.get("regression_warnings") or [] if str(item).strip()
        ],
        summary=_string(payload.get("summary")),
    )


def normalize_gate_result(payload: dict[str, Any]) -> VersionGateSummary | None:
    if not payload:
        return None

    return VersionGateSummary(
        agent_version_id=_string(payload.get("agent_version_id")),
        comparison_id=_string(payload.get("comparison_id")),
        behavior_gate_status=_string(payload.get("behavior_gate_status")),
        tool_readiness_status=_string(payload.get("tool_readiness_status")),
        production_readiness_status=_string(payload.get("production_readiness_status")),
        overall_status=_string(payload.get("overall_status")),
        behavior_gates={
            str(key): str(value)
            for key, value in (payload.get("behavior_gates") or {}).items()
            if str(value).strip()
        },
        tool_readiness_gates={
            str(key): str(value)
            for key, value in (payload.get("tool_readiness_gates") or {}).items()
            if str(value).strip()
        },
        blockers=[str(item) for item in payload.get("blockers") or [] if str(item).strip()],
    )


def normalize_trace_links(
    payload: list[dict[str, Any]] | None,
    *,
    experiment_run_id: str | None = None,
    agent_version_id: str | None = None,
) -> list[TraceLink]:
    if not payload:
        return []

    links: list[TraceLink] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        link = normalize_trace_link(
            item,
            experiment_run_id=experiment_run_id,
            agent_version_id=agent_version_id,
        )
        if link is not None:
            links.append(link)
    return links


def normalize_trace_link(
    payload: dict[str, Any],
    *,
    experiment_run_id: str | None = None,
    agent_version_id: str | None = None,
) -> TraceLink | None:
    external_trace_id = _string(
        payload.get("external_trace_id")
        or payload.get("trace_id")
        or payload.get("langfuse_trace_id")
    )
    if not external_trace_id:
        return None

    link_id = _string(payload.get("id"))
    if not link_id:
        link_id = f"trace-link-{external_trace_id}"

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    return TraceLink(
        id=link_id,
        provider=_string(payload.get("provider")) or "langfuse",
        external_trace_id=external_trace_id,
        external_url=_string(payload.get("external_url") or payload.get("url")),
        experiment_run_id=experiment_run_id or _string(payload.get("experiment_run_id")),
        operational_run_id=_string(payload.get("operational_run_id")),
        scenario_id=_string(payload.get("scenario_id")),
        agent_version_id=agent_version_id or _string(payload.get("agent_version_id")),
        metadata=dict(metadata),
    )


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if not value:
        return []
    return [str(item) for item in value if str(item).strip()]
