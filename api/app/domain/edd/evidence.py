from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.domain.edd.trace_link import TraceLink


class FailurePacket(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    experiment_run_id: str | None = Field(default=None, max_length=128)
    agent_version_id: str | None = Field(default=None, max_length=128)
    scenario_id: str | None = Field(default=None, max_length=128)
    failed_behavior_rule_id: str | None = Field(default=None, max_length=128)
    severity: str | None = Field(default=None, max_length=64)
    observed_behavior: str | None = Field(default=None, max_length=5000)
    expected_behavior: str | None = Field(default=None, max_length=5000)
    suspected_cause: str | None = Field(default=None, max_length=5000)
    recommended_fix: str | None = Field(default=None, max_length=5000)
    trace_link_ids: list[str] = Field(default_factory=list)
    status: str = Field(default="open", max_length=64)
    failure_type: str | None = Field(default=None, max_length=128)
    summary: str | None = Field(default=None, max_length=5000)


class FixPlan(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    source_version_id: str | None = Field(default=None, max_length=128)
    target_version_label: str | None = Field(default=None, max_length=128)
    failure_packet_ids: list[str] = Field(default_factory=list)
    behavior_rule_ids_addressed: list[str] = Field(default_factory=list)
    graph_changes: list[str] = Field(default_factory=list)
    prompt_changes: list[str] = Field(default_factory=list)
    tool_changes: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    regression_risks: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", max_length=64)


class ComparisonMetricDelta(BaseModel):
    baseline: float | int | None = None
    candidate: float | int | None = None
    delta: float | int | None = None


class Comparison(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    baseline_version_id: str | None = Field(default=None, max_length=128)
    candidate_version_id: str | None = Field(default=None, max_length=128)
    target_id: str | None = Field(default=None, max_length=128)
    eval_contract_id: str | None = Field(default=None, max_length=128)
    scenario_set_id: str | None = Field(default=None, max_length=128)
    score_deltas: dict[str, ComparisonMetricDelta | dict[str, Any]] = Field(default_factory=dict)
    resolved_failure_packet_ids: list[str] = Field(default_factory=list)
    new_failure_packet_ids: list[str] = Field(default_factory=list)
    regression_warnings: list[str] = Field(default_factory=list)
    summary: str | None = Field(default=None, max_length=5000)


class VersionGateSummary(BaseModel):
    """Aggregate gate summary from a publish envelope (HLD-005 gate_result block)."""

    agent_version_id: str | None = Field(default=None, max_length=128)
    comparison_id: str | None = Field(default=None, max_length=128)
    behavior_gate_status: str | None = Field(default=None, max_length=64)
    tool_readiness_status: str | None = Field(default=None, max_length=64)
    production_readiness_status: str | None = Field(default=None, max_length=64)
    overall_status: str | None = Field(default=None, max_length=64)
    behavior_gates: dict[str, str] = Field(default_factory=dict)
    tool_readiness_gates: dict[str, str] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)


class RunEvidence(BaseModel):
    failure_packet: FailurePacket | None = None
    fix_plan: FixPlan | None = None
    comparison: Comparison | None = None
    gate_result: VersionGateSummary | None = None
    trace_links: list[TraceLink] = Field(default_factory=list)
