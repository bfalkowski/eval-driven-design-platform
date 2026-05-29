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

        eval_spec_id = normalized.eval_spec_id or self._default_eval_spec_id
        if eval_spec_id is None:
            raise BadRequestError(
                "eval_spec_id is required (set on the envelope or APP_INGEST_DEFAULT_EVAL_SPEC_ID).",
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
        gate_status, gate_explanation = compute_gate(
            pass_threshold=spec.pass_threshold,
            overall_score=overall_score,
            failure_packet=normalized.failure_packet,
        )

        ingest = ExperimentRunIngest(
            source=normalized.source,
            external_run_id=normalized.run_id,
            subject_id=resolve_subject_id(normalized),
            suite_id=resolve_suite_id(normalized),
            gate_status=gate_status,
            gate_explanation=gate_explanation,
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
            gate_status=gate_status,
            gate_explanation=gate_explanation,
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
    if envelope.schema_version != INGEST_SCHEMA_VERSION:
        raise BadRequestError(
            f"Unsupported schema_version: {envelope.schema_version!r}. "
            f"Expected {INGEST_SCHEMA_VERSION!r}.",
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


def compute_gate(
    *,
    pass_threshold: float,
    overall_score: float | None,
    failure_packet: dict[str, Any] | None,
) -> tuple[str, str]:
    if failure_packet:
        failure_type = failure_packet.get("failure_type") or failure_packet.get("summary")
        detail = f" ({failure_type})" if failure_type else ""
        return "fail", f"Ingest reported a failure packet{detail}."

    if overall_score is None:
        return "insufficient_evidence", "No overall_score in eval_summary."

    if overall_score >= pass_threshold:
        return (
            "pass",
            f"Ingest overall score {overall_score:.1f} meets pass threshold {pass_threshold:.1f}.",
        )
    return (
        "fail",
        f"Ingest overall score {overall_score:.1f} is below pass threshold {pass_threshold:.1f}.",
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


# Backward-compatible aliases for tests and legacy imports.
LabPublishService = RunIngestService
LAB_PUBLISH_SCHEMA_VERSION = INGEST_SCHEMA_VERSION
LAB_PUBLISH_SOURCE = "edd-agent-lab"
