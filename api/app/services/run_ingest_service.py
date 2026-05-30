from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.errors import BadRequestError, NotFoundError
from app.domain.models import (
    ExperimentRun,
    ExperimentRunIngest,
    ExperimentRunStatus,
    RunIngestEnvelope,
    RunIngestResponse,
)
from app.services.readiness_evaluation import compute_gate as _compute_gate
from app.services.readiness_evaluation import evaluate_readiness
from app.storage.base import EddRepository

INGEST_SCHEMA_VERSION = "1"
SOURCE_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class RunIngestService:
    def __init__(
        self,
        repository: EddRepository,
        *,
        default_eval_spec_id: UUID | None = None,
        allowed_sources: list[str] | None = None,
    ) -> None:
        self._repository = repository
        self._default_eval_spec_id = default_eval_spec_id
        self._allowed_sources = allowed_sources or []

    async def publish(
        self,
        *,
        tenant_id: str,
        envelope: RunIngestEnvelope,
    ) -> RunIngestResponse:
        normalized = normalize_envelope(envelope)
        _validate_envelope(normalized, allowed_sources=self._allowed_sources)

        if normalized.idempotency_key:
            existing = await _find_idempotent_run(
                self._repository,
                tenant_id=tenant_id,
                source=normalized.source,
                idempotency_key=normalized.idempotency_key,
            )
            if existing is not None:
                return _response_from_existing_run(existing)

        eval_spec_id = normalized.eval_spec_id or self._default_eval_spec_id
        if eval_spec_id is None:
            raise BadRequestError(
                "eval_spec_id is required "
                "(set on the envelope or APP_INGEST_DEFAULT_EVAL_SPEC_ID).",
            )

        try:
            spec = await self._repository.get_eval_spec(
                tenant_id=tenant_id,
                eval_spec_id=eval_spec_id,
            )
        except NotFoundError as exc:
            raise BadRequestError("eval_spec_id does not exist for this tenant.") from exc

        candidate_version = resolve_candidate_version(normalized)
        status = (
            ExperimentRunStatus.FAILED
            if normalized.failure_packet
            else ExperimentRunStatus.COMPLETED
        )
        completed_at = _parse_timestamp(normalized.completed_at) or datetime.now(UTC)
        result_count = _result_count(normalized)
        overall_score = extract_overall_score(normalized.eval_summary)
        readiness = evaluate_readiness(
            pass_threshold=spec.pass_threshold,
            overall_score=overall_score,
            failure_packet=normalized.failure_packet,
            tool_mode_summary=normalized.tool_mode_summary,
            production_ready=normalized.production_ready,
            tool_bindings=normalized.tool_bindings,
        )

        ingest = ExperimentRunIngest(
            source=normalized.source,
            external_run_id=normalized.run_id,
            subject_id=resolve_subject_id(normalized),
            suite_id=resolve_suite_id(normalized),
            schema_version=normalized.schema_version,
            idempotency_key=normalized.idempotency_key,
            gate_status=readiness.gate_status,
            gate_explanation=readiness.gate_explanation,
            behavior_status=readiness.behavior_status,
            tool_status=readiness.tool_status,
            production_status=readiness.production_status,
            overall_status=readiness.overall_status,
            readiness_explanation=readiness.readiness_explanation,
            tool_mode_summary=normalized.tool_mode_summary,
            target_id=normalized.target_id,
            eval_contract_ref_id=normalized.eval_contract_ref_id,
            producer=normalized.producer,
            scenario_ids=list(normalized.scenario_ids),
            eval_summary=normalized.eval_summary,
            failure_packet=normalized.failure_packet,
            outputs=dict(normalized.outputs),
            artifact_paths=dict(normalized.artifact_paths),
        )

        run = await self._repository.create_experiment_run(
            tenant_id=tenant_id,
            eval_spec_id=eval_spec_id,
            candidate_version=candidate_version,
            status=status,
            result_count=result_count,
            completed_at=completed_at,
            ingest=ingest,
        )
        return RunIngestResponse(
            platform_run_id=run.experiment_run_id,
            experiment_run_id=run.experiment_run_id,
            external_run_id=normalized.run_id,
            lab_run_id=normalized.run_id,
            gate_status=readiness.gate_status,
            gate_explanation=readiness.gate_explanation,
            behavior_status=readiness.behavior_status,
            tool_status=readiness.tool_status,
            production_status=readiness.production_status,
            overall_status=readiness.overall_status,
            readiness_explanation=readiness.readiness_explanation,
            experiment_run=run,
        )


def normalize_envelope(envelope: RunIngestEnvelope) -> RunIngestEnvelope:
    updates: dict[str, Any] = {}
    if not envelope.candidate_version and envelope.agent_version:
        updates["candidate_version"] = envelope.agent_version
    if not envelope.subject_id and envelope.agent:
        updates["subject_id"] = envelope.agent
    if not envelope.suite_id and envelope.suite:
        updates["suite_id"] = envelope.suite
    if updates:
        return envelope.model_copy(update=updates)
    return envelope


def resolve_candidate_version(envelope: RunIngestEnvelope) -> str:
    if envelope.candidate_version:
        return envelope.candidate_version
    raise BadRequestError("candidate_version or agent_version is required.")


def resolve_subject_id(envelope: RunIngestEnvelope) -> str | None:
    return envelope.subject_id or envelope.agent


def resolve_suite_id(envelope: RunIngestEnvelope) -> str | None:
    return envelope.suite_id or envelope.suite


def _validate_envelope(
    envelope: RunIngestEnvelope,
    *,
    allowed_sources: list[str],
) -> None:
    if envelope.schema_version not in {"1", "2"}:
        raise BadRequestError(
            f"Unsupported schema_version: {envelope.schema_version!r}. Expected '1' or '2'.",
        )
    if not SOURCE_PATTERN.fullmatch(envelope.source):
        raise BadRequestError(
            "source must match [a-z][a-z0-9_-]{0,63} (e.g. edd-agent-lab, ci, partner-x).",
        )
    if allowed_sources and envelope.source not in allowed_sources:
        raise BadRequestError(
            f"source {envelope.source!r} is not in APP_INGEST_ALLOWED_SOURCES.",
        )
    resolve_candidate_version(envelope)


def extract_overall_score(eval_summary: dict[str, Any] | None) -> float | None:
    if not eval_summary:
        return None
    raw = eval_summary.get("overall_score")
    if raw is None:
        return None
    try:
        score = float(raw)
    except (TypeError, ValueError):
        return None
    if score <= 1.0:
        return score * 100.0
    return score


# Backward-compatible alias; implementation lives in readiness_evaluation.
def compute_gate(
    *,
    pass_threshold: float,
    overall_score: float | None,
    failure_packet: dict[str, Any] | None,
    tool_mode_summary: str | None = None,
    production_ready: bool | None = None,
    tool_bindings: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    return _compute_gate(
        pass_threshold=pass_threshold,
        overall_score=overall_score,
        failure_packet=failure_packet,
        tool_mode_summary=tool_mode_summary,
        production_ready=production_ready,
        tool_bindings=tool_bindings,
    )


def _result_count(envelope: RunIngestEnvelope) -> int:
    if envelope.scenario_ids:
        return len(envelope.scenario_ids)
    eval_summary = envelope.eval_summary or {}
    variant_count = len(eval_summary.get("variants") or [])
    if variant_count or eval_summary.get("base_case") is not None:
        return variant_count + (1 if eval_summary.get("base_case") is not None else 0)
    if eval_summary.get("cases"):
        return len(eval_summary["cases"])
    if eval_summary:
        return 1
    return 0


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


async def _find_idempotent_run(
    repository: EddRepository,
    *,
    tenant_id: str,
    source: str,
    idempotency_key: str,
) -> ExperimentRun | None:
    runs = await repository.list_experiment_runs(
        tenant_id=tenant_id,
        ingest_source=source,
        limit=500,
    )
    for run in runs:
        ingest = run.ingest
        if ingest is not None and ingest.idempotency_key == idempotency_key:
            return run
    return None


def _response_from_existing_run(run: ExperimentRun) -> RunIngestResponse:
    ingest = run.ingest
    assert ingest is not None
    return RunIngestResponse(
        platform_run_id=run.experiment_run_id,
        experiment_run_id=run.experiment_run_id,
        external_run_id=ingest.external_run_id,
        lab_run_id=ingest.external_run_id,
        gate_status=ingest.gate_status or "insufficient_evidence",
        gate_explanation=ingest.gate_explanation or "No gate explanation recorded.",
        behavior_status=ingest.behavior_status,
        tool_status=ingest.tool_status,
        production_status=ingest.production_status,
        overall_status=ingest.overall_status,
        readiness_explanation=ingest.readiness_explanation,
        experiment_run=run,
    )


# Backward-compatible aliases for tests and legacy imports.
LabPublishService = RunIngestService
LAB_PUBLISH_SCHEMA_VERSION = INGEST_SCHEMA_VERSION
LAB_PUBLISH_SOURCE = "edd-agent-lab"
