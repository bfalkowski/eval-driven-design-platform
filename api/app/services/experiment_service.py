from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.core.errors import BadRequestError
from app.domain.models import (
    EvaluationResult,
    ExperimentRun,
    ExperimentRunStatus,
    ExperimentRunSummary,
)
from app.services.mock_evaluator import evaluate_mock
from app.services.scaffold_runner import run_scaffold
from app.storage.base import EddRepository


class ExperimentService:
    def __init__(self, repository: EddRepository) -> None:
        self._repository = repository

    async def create_run(
        self,
        *,
        tenant_id: str,
        eval_spec_id: UUID,
        candidate_version: str,
        eval_case_ids: list[UUID] | None,
    ) -> tuple[ExperimentRun, list[EvaluationResult]]:
        spec = await self._repository.get_eval_spec(tenant_id=tenant_id, eval_spec_id=eval_spec_id)
        if eval_case_ids:
            cases = []
            for case_id in eval_case_ids:
                case = await self._repository.get_eval_case(
                    tenant_id=tenant_id,
                    eval_case_id=case_id,
                )
                if case.eval_spec_id != eval_spec_id:
                    raise BadRequestError("All eval cases must belong to the selected eval spec.")
                cases.append(case)
        else:
            cases = await self._repository.list_eval_cases(
                tenant_id=tenant_id,
                eval_spec_id=eval_spec_id,
            )

        if not cases:
            raise BadRequestError("No eval cases available for this experiment run.")

        completed_at = datetime.now(UTC)
        run = await self._repository.create_experiment_run(
            tenant_id=tenant_id,
            eval_spec_id=eval_spec_id,
            candidate_version=candidate_version,
            status=ExperimentRunStatus.COMPLETED,
            result_count=len(cases),
            completed_at=completed_at,
        )

        results: list[EvaluationResult] = []
        for case in cases:
            scaffold_output = run_scaffold(case=case, candidate_version=candidate_version)
            score, passed, breakdown = evaluate_mock(
                spec=spec,
                case=case,
                scaffold_output=scaffold_output,
            )
            result = await self._repository.create_evaluation_result(
                tenant_id=tenant_id,
                experiment_run_id=run.experiment_run_id,
                eval_case_id=case.eval_case_id,
                candidate_version=candidate_version,
                score=score,
                passed=passed,
                scaffold_output=scaffold_output,
                judge_breakdown=breakdown,
            )
            results.append(result)

        return run, results

    async def get_summary(
        self,
        *,
        tenant_id: str,
        experiment_run_id: UUID,
    ) -> ExperimentRunSummary:
        run = await self._repository.get_experiment_run(
            tenant_id=tenant_id,
            experiment_run_id=experiment_run_id,
        )
        results = await self._repository.list_evaluation_results(
            tenant_id=tenant_id,
            experiment_run_id=experiment_run_id,
            limit=1000,
        )
        return summarize_run(run, results)


def summarize_run(run: ExperimentRun, results: list[EvaluationResult]) -> ExperimentRunSummary:
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    average_score = sum(result.score for result in results) / len(results) if results else 0.0
    pass_rate = passed_count / len(results) if results else 0.0
    return ExperimentRunSummary(
        experiment_run_id=run.experiment_run_id,
        tenant_id=run.tenant_id,
        eval_spec_id=run.eval_spec_id,
        candidate_version=run.candidate_version,
        status=run.status,
        result_count=run.result_count,
        passed_count=passed_count,
        failed_count=failed_count,
        pass_rate=pass_rate,
        average_score=average_score,
    )
