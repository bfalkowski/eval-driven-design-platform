from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.edd.evidence import RunEvidence


class ExperimentRunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class JudgeConfig(BaseModel):
    judge_id: str = Field(default="mock", min_length=1, max_length=128)
    version: str = Field(default="1", min_length=1, max_length=64)
    rubric_id: str | None = Field(default=None, max_length=128)


class EvalSpec(BaseModel):
    eval_spec_id: UUID
    tenant_id: str
    name: str
    description: str | None = None
    version: str
    rubric: str
    pass_threshold: float = Field(ge=0, le=100)
    judge_config: JudgeConfig
    created_at: datetime
    updated_at: datetime


class CreateEvalSpecRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2000)
    version: str = Field(default="1", min_length=1, max_length=64)
    rubric: str = Field(min_length=1, max_length=10_000)
    pass_threshold: float = Field(default=70.0, ge=0, le=100)
    judge_config: JudgeConfig = Field(default_factory=JudgeConfig)


class UpdateEvalSpecRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2000)
    version: str | None = Field(default=None, min_length=1, max_length=64)
    rubric: str | None = Field(default=None, min_length=1, max_length=10_000)
    pass_threshold: float | None = Field(default=None, ge=0, le=100)
    judge_config: JudgeConfig | None = None


class EvalSpecResponse(EvalSpec):
    request_id: str


class EvalSpecListResponse(BaseModel):
    eval_specs: list[EvalSpec]
    request_id: str


class EvalCase(BaseModel):
    eval_case_id: UUID
    tenant_id: str
    eval_spec_id: UUID
    name: str
    input_payload: dict[str, Any]
    notes: str | None = None
    source: str
    langfuse_trace_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateEvalCaseRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    eval_spec_id: UUID
    name: str = Field(min_length=1, max_length=256)
    input_payload: dict[str, Any]
    notes: str | None = Field(default=None, max_length=5000)
    source: str = Field(default="manual", min_length=1, max_length=64)
    langfuse_trace_id: str | None = Field(default=None, max_length=256)


class UpdateEvalCaseRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    input_payload: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, min_length=1, max_length=64)
    langfuse_trace_id: str | None = Field(default=None, max_length=256)


class EvalCaseResponse(EvalCase):
    request_id: str


class EvalCaseListResponse(BaseModel):
    eval_cases: list[EvalCase]
    request_id: str


class ExperimentRunIngest(BaseModel):
    source: str
    external_run_id: str
    subject_id: str | None = None
    suite_id: str | None = None
    schema_version: str | None = None
    idempotency_key: str | None = None
    gate_status: str | None = None
    gate_explanation: str | None = None
    behavior_status: str | None = None
    tool_status: str | None = None
    production_status: str | None = None
    overall_status: str | None = None
    readiness_explanation: str | None = None
    tool_mode_summary: str | None = None
    target_id: str | None = None
    eval_contract_ref_id: str | None = None
    producer: dict[str, Any] | None = None
    scenario_ids: list[str] = Field(default_factory=list)
    eval_summary: dict[str, Any] | None = None
    failure_packet: dict[str, Any] | None = None
    fix_plan: dict[str, Any] | None = None
    comparison: dict[str, Any] | None = None
    gate_result: dict[str, Any] | None = None
    evidence: RunEvidence | None = None
    outputs: dict[str, Any] = Field(default_factory=dict)
    artifact_paths: dict[str, Any] = Field(default_factory=dict)


class ExperimentRun(BaseModel):
    experiment_run_id: UUID
    tenant_id: str
    eval_spec_id: UUID
    candidate_version: str
    status: ExperimentRunStatus
    result_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    ingest: ExperimentRunIngest | None = None


class CreateExperimentRunRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    eval_spec_id: UUID
    candidate_version: str = Field(min_length=1, max_length=128)
    eval_case_ids: list[UUID] | None = None


class ExperimentRunResponse(ExperimentRun):
    request_id: str


class ExperimentRunListResponse(BaseModel):
    experiment_runs: list[ExperimentRun]
    request_id: str


class ExperimentRunSummary(BaseModel):
    experiment_run_id: UUID
    tenant_id: str
    eval_spec_id: UUID
    candidate_version: str
    status: ExperimentRunStatus
    result_count: int
    passed_count: int
    failed_count: int
    pass_rate: float
    average_score: float


class ExperimentRunSummaryResponse(ExperimentRunSummary):
    request_id: str


class QualityGateEvaluation(BaseModel):
    experiment_run_id: UUID
    eval_spec_id: UUID
    candidate_version: str
    gate_status: str
    gate_explanation: str
    evaluation_source: str
    pass_threshold: float
    average_score: float | None = None
    behavior_status: str | None = None
    tool_status: str | None = None
    production_status: str | None = None
    overall_status: str | None = None
    readiness_explanation: str | None = None
    ingest_source: str | None = None
    external_run_id: str | None = None


class QualityGateResponse(QualityGateEvaluation):
    request_id: str


class RunEvidenceResponse(RunEvidence):
    experiment_run_id: UUID
    request_id: str


class EvaluationResult(BaseModel):
    evaluation_result_id: UUID
    tenant_id: str
    experiment_run_id: UUID
    eval_case_id: UUID
    candidate_version: str
    score: float = Field(ge=0, le=100)
    passed: bool
    langfuse_trace_id: str | None = None
    langfuse_score_id: str | None = None
    scaffold_output: dict[str, Any]
    judge_breakdown: dict[str, Any]
    created_at: datetime


class EvaluationResultResponse(EvaluationResult):
    request_id: str


class EvaluationResultListResponse(BaseModel):
    evaluation_results: list[EvaluationResult]
    request_id: str


class LangfuseHealthResponse(BaseModel):
    enabled: bool
    configured: bool
    status: str
    host: str
    reachable: bool
    authenticated: bool | None = None
    project_count: int | None = None
    project_name: str | None = None
    message: str
    request_id: str


class LangfuseTracePreview(BaseModel):
    trace_id: str
    name: str | None = None
    timestamp: str | None = None
    input_preview: str | None = None
    has_observations: bool


class LangfuseTraceResponse(BaseModel):
    trace: LangfuseTracePreview
    request_id: str


class ImportLangfuseTraceRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    eval_spec_id: UUID
    trace_id: str = Field(min_length=1, max_length=256)
    name: str | None = Field(default=None, min_length=1, max_length=256)
    notes: str | None = Field(default=None, max_length=5000)


class RunIngestEnvelope(BaseModel):
    schema_version: str = Field(min_length=1, max_length=16)
    source: str = Field(min_length=1, max_length=64)
    run_id: str = Field(min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)
    candidate_version: str | None = Field(default=None, min_length=1, max_length=128)
    agent_version: str | None = Field(default=None, min_length=1, max_length=128)
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    agent: str | None = Field(default=None, min_length=1, max_length=128)
    suite_id: str | None = Field(default=None, min_length=1, max_length=128)
    suite: str | None = Field(default=None, min_length=1, max_length=128)
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    eval_spec_id: UUID | None = None
    scenario_ids: list[str] = Field(default_factory=list)
    started_at: str | None = Field(default=None, max_length=64)
    completed_at: str | None = Field(default=None, max_length=64)
    outputs: dict[str, Any] = Field(default_factory=dict)
    eval_summary: dict[str, Any] | None = None
    failure_packet: dict[str, Any] | None = None
    fix_plan: dict[str, Any] | None = None
    comparison: dict[str, Any] | None = None
    gate_result: dict[str, Any] | None = None
    trace_links: list[dict[str, Any]] | None = None
    artifact_paths: dict[str, Any] = Field(default_factory=dict)
    tool_mode_summary: str | None = Field(default=None, max_length=64)
    production_ready: bool | None = None
    tool_bindings: list[dict[str, Any]] | None = None
    producer: dict[str, Any] | None = None
    target_id: str | None = Field(default=None, max_length=128)
    eval_contract_ref_id: str | None = Field(default=None, max_length=128)


class RunIngestResponse(BaseModel):
    platform_run_id: UUID
    experiment_run_id: UUID
    external_run_id: str
    gate_status: str
    gate_explanation: str
    behavior_status: str | None = None
    tool_status: str | None = None
    production_status: str | None = None
    overall_status: str | None = None
    readiness_explanation: str | None = None
    experiment_run: ExperimentRun
    request_id: str | None = None
    lab_run_id: str | None = None
    trace_link_ids: list[str] | None = None


LabPublishEnvelope = RunIngestEnvelope
LabPublishResponse = RunIngestResponse
