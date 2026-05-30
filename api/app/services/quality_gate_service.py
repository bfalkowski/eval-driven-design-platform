from __future__ import annotations

from uuid import UUID

from app.domain.edd.readiness import ReadinessEvaluation
from app.domain.models import (
    ExperimentRun,
    ExperimentRunStatus,
    QualityGateEvaluation,
)
from app.services.experiment_service import summarize_run
from app.services.readiness_evaluation import evaluate_readiness
from app.storage.base import EddRepository


class QualityGateService:
    def __init__(self, repository: EddRepository) -> None:
        self._repository = repository

    async def evaluate(
        self,
        *,
        tenant_id: str,
        experiment_run_id: UUID,
    ) -> QualityGateEvaluation:
        run = await self._repository.get_experiment_run(
            tenant_id=tenant_id,
            experiment_run_id=experiment_run_id,
        )
        spec = await self._repository.get_eval_spec(
            tenant_id=tenant_id,
            eval_spec_id=run.eval_spec_id,
        )

        if run.ingest is not None:
            return _evaluation_from_ingest(run, spec.pass_threshold)

        results = await self._repository.list_evaluation_results(
            tenant_id=tenant_id,
            experiment_run_id=experiment_run_id,
            limit=1000,
        )
        summary = summarize_run(run, results)

        if run.status == ExperimentRunStatus.FAILED:
            readiness = evaluate_readiness(
                pass_threshold=spec.pass_threshold,
                overall_score=summary.average_score if results else None,
                failure_packet={"failure_type": "experiment_run_failed"},
            )
            return _quality_gate_from_readiness(
                run=run,
                pass_threshold=spec.pass_threshold,
                average_score=summary.average_score if results else None,
                evaluation_source="experiment_results",
                readiness=readiness,
            )

        if not results:
            readiness = evaluate_readiness(
                pass_threshold=spec.pass_threshold,
                overall_score=None,
                failure_packet=None,
            )
            return _quality_gate_from_readiness(
                run=run,
                pass_threshold=spec.pass_threshold,
                average_score=None,
                evaluation_source="experiment_results",
                readiness=readiness,
            )

        readiness = evaluate_readiness(
            pass_threshold=spec.pass_threshold,
            overall_score=summary.average_score,
            failure_packet=None,
        )
        return _quality_gate_from_readiness(
            run=run,
            pass_threshold=spec.pass_threshold,
            average_score=summary.average_score,
            evaluation_source="experiment_results",
            readiness=readiness,
        )


def _evaluation_from_ingest(run: ExperimentRun, pass_threshold: float) -> QualityGateEvaluation:
    ingest = run.ingest
    assert ingest is not None

    if ingest.overall_status and ingest.behavior_status:
        return QualityGateEvaluation(
            experiment_run_id=run.experiment_run_id,
            eval_spec_id=run.eval_spec_id,
            candidate_version=run.candidate_version,
            gate_status=ingest.gate_status or "insufficient_evidence",
            gate_explanation=ingest.gate_explanation or "No gate explanation recorded.",
            evaluation_source="ingest",
            pass_threshold=pass_threshold,
            average_score=_ingest_average_score(run),
            behavior_status=ingest.behavior_status,
            tool_status=ingest.tool_status,
            production_status=ingest.production_status,
            overall_status=ingest.overall_status,
            readiness_explanation=ingest.readiness_explanation,
            ingest_source=ingest.source,
            external_run_id=ingest.external_run_id,
        )

    readiness = evaluate_readiness(
        pass_threshold=pass_threshold,
        overall_score=_ingest_average_score(run),
        failure_packet=ingest.failure_packet,
        tool_mode_summary=ingest.tool_mode_summary,
        production_ready=None,
        tool_bindings=None,
    )
    return _quality_gate_from_readiness(
        run=run,
        pass_threshold=pass_threshold,
        average_score=_ingest_average_score(run),
        evaluation_source="ingest",
        readiness=readiness,
        ingest_source=ingest.source,
        external_run_id=ingest.external_run_id,
    )


def _quality_gate_from_readiness(
    *,
    run: ExperimentRun,
    pass_threshold: float,
    average_score: float | None,
    evaluation_source: str,
    readiness: ReadinessEvaluation,
    ingest_source: str | None = None,
    external_run_id: str | None = None,
) -> QualityGateEvaluation:
    return QualityGateEvaluation(
        experiment_run_id=run.experiment_run_id,
        eval_spec_id=run.eval_spec_id,
        candidate_version=run.candidate_version,
        gate_status=readiness.gate_status,
        gate_explanation=readiness.gate_explanation,
        evaluation_source=evaluation_source,
        pass_threshold=pass_threshold,
        average_score=average_score,
        behavior_status=readiness.behavior_status,
        tool_status=readiness.tool_status,
        production_status=readiness.production_status,
        overall_status=readiness.overall_status,
        readiness_explanation=readiness.readiness_explanation,
        ingest_source=ingest_source,
        external_run_id=external_run_id,
    )


def _ingest_average_score(run: ExperimentRun) -> float | None:
    if run.ingest is None or not run.ingest.eval_summary:
        return None
    raw = run.ingest.eval_summary.get("overall_score")
    if raw is None:
        return None
    try:
        score = float(raw)
    except (TypeError, ValueError):
        return None
    if score <= 1.0:
        return score * 100.0
    return score
