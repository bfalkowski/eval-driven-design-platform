from __future__ import annotations

from uuid import UUID

from app.domain.models import (
    ExperimentRun,
    ExperimentRunStatus,
    QualityGateEvaluation,
)
from app.services.experiment_service import summarize_run
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
            gate_status = run.ingest.gate_status or "insufficient_evidence"
            return QualityGateEvaluation(
                experiment_run_id=run.experiment_run_id,
                eval_spec_id=run.eval_spec_id,
                candidate_version=run.candidate_version,
                gate_status=gate_status,
                gate_explanation=run.ingest.gate_explanation or "No gate explanation recorded.",
                evaluation_source="ingest",
                pass_threshold=spec.pass_threshold,
                average_score=_ingest_average_score(run),
                ingest_source=run.ingest.source,
                external_run_id=run.ingest.external_run_id,
            )

        results = await self._repository.list_evaluation_results(
            tenant_id=tenant_id,
            experiment_run_id=experiment_run_id,
            limit=1000,
        )
        summary = summarize_run(run, results)

        if run.status == ExperimentRunStatus.FAILED:
            return QualityGateEvaluation(
                experiment_run_id=run.experiment_run_id,
                eval_spec_id=run.eval_spec_id,
                candidate_version=run.candidate_version,
                gate_status="fail",
                gate_explanation="Experiment run status is failed.",
                evaluation_source="experiment_results",
                pass_threshold=spec.pass_threshold,
                average_score=summary.average_score if results else None,
            )

        if not results:
            return QualityGateEvaluation(
                experiment_run_id=run.experiment_run_id,
                eval_spec_id=run.eval_spec_id,
                candidate_version=run.candidate_version,
                gate_status="insufficient_evidence",
                gate_explanation="No evaluation results for this experiment run.",
                evaluation_source="experiment_results",
                pass_threshold=spec.pass_threshold,
            )

        if summary.average_score >= spec.pass_threshold:
            return QualityGateEvaluation(
                experiment_run_id=run.experiment_run_id,
                eval_spec_id=run.eval_spec_id,
                candidate_version=run.candidate_version,
                gate_status="pass",
                gate_explanation=(
                    f"Average score {summary.average_score:.1f} meets pass threshold "
                    f"{spec.pass_threshold:.1f}."
                ),
                evaluation_source="experiment_results",
                pass_threshold=spec.pass_threshold,
                average_score=summary.average_score,
            )

        return QualityGateEvaluation(
            experiment_run_id=run.experiment_run_id,
            eval_spec_id=run.eval_spec_id,
            candidate_version=run.candidate_version,
            gate_status="fail",
            gate_explanation=(
                f"Average score {summary.average_score:.1f} is below pass threshold "
                f"{spec.pass_threshold:.1f}."
            ),
            evaluation_source="experiment_results",
            pass_threshold=spec.pass_threshold,
            average_score=summary.average_score,
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
