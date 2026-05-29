from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.errors import BadRequestError, NotFoundError
from app.domain.models import (
    ExperimentRun,
    ExperimentRunStatus,
    LabPublishEnvelope,
    LabPublishResponse,
)
from app.storage.base import EddRepository

LAB_PUBLISH_SCHEMA_VERSION = "1"
LAB_PUBLISH_SOURCE = "edd-agent-lab"


class LabPublishService:
    def __init__(
        self,
        repository: EddRepository,
        *,
        default_eval_spec_id: UUID | None = None,
    ) -> None:
        self._repository = repository
        self._default_eval_spec_id = default_eval_spec_id

    async def publish(
        self,
        *,
        tenant_id: str,
        envelope: LabPublishEnvelope,
    ) -> LabPublishResponse:
        _validate_envelope(envelope)
        eval_spec_id = envelope.eval_spec_id or self._default_eval_spec_id
        if eval_spec_id is None:
            raise BadRequestError(
                "eval_spec_id is required (set on the envelope or APP_LAB_DEFAULT_EVAL_SPEC_ID).",
            )

        try:
            spec = await self._repository.get_eval_spec(
                tenant_id=tenant_id,
                eval_spec_id=eval_spec_id,
            )
        except NotFoundError as exc:
            raise BadRequestError("eval_spec_id does not exist for this tenant.") from exc

        status = (
            ExperimentRunStatus.FAILED
            if envelope.failure_packet
            else ExperimentRunStatus.COMPLETED
        )
        completed_at = _parse_timestamp(envelope.completed_at) or datetime.now(UTC)
        result_count = _result_count(envelope)
        overall_score = extract_overall_score(envelope.eval_summary)
        gate_status, gate_explanation = compute_gate(
            pass_threshold=spec.pass_threshold,
            overall_score=overall_score,
            failure_packet=envelope.failure_packet,
        )

        run = await self._repository.create_experiment_run(
            tenant_id=tenant_id,
            eval_spec_id=eval_spec_id,
            candidate_version=envelope.agent_version,
            status=status,
            result_count=result_count,
            completed_at=completed_at,
        )
        return LabPublishResponse(
            platform_run_id=run.experiment_run_id,
            experiment_run_id=run.experiment_run_id,
            lab_run_id=envelope.run_id,
            gate_status=gate_status,
            gate_explanation=gate_explanation,
            experiment_run=run,
        )


def _validate_envelope(envelope: LabPublishEnvelope) -> None:
    if envelope.schema_version != LAB_PUBLISH_SCHEMA_VERSION:
        raise BadRequestError(
            f"Unsupported schema_version: {envelope.schema_version!r}. Expected {LAB_PUBLISH_SCHEMA_VERSION!r}.",
        )
    if envelope.source != LAB_PUBLISH_SOURCE:
        raise BadRequestError(
            f"Unsupported source: {envelope.source!r}. Expected {LAB_PUBLISH_SOURCE!r}.",
        )


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
        return "fail", f"Lab reported a failure packet{detail}."

    if overall_score is None:
        return "insufficient_evidence", "No overall_score in eval_summary."

    if overall_score >= pass_threshold:
        return (
            "pass",
            f"Lab overall score {overall_score:.1f} meets pass threshold {pass_threshold:.1f}.",
        )
    return (
        "fail",
        f"Lab overall score {overall_score:.1f} is below pass threshold {pass_threshold:.1f}.",
    )


def _result_count(envelope: LabPublishEnvelope) -> int:
    if envelope.scenario_ids:
        return len(envelope.scenario_ids)
    eval_summary = envelope.eval_summary or {}
    variant_count = len(eval_summary.get("variants") or [])
    if variant_count or eval_summary.get("base_case") is not None:
        return variant_count + (1 if eval_summary.get("base_case") is not None else 0)
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
