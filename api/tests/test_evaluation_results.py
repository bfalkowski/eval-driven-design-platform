from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.evaluation_results import _with_case_trace_ids
from app.domain.models import JudgeConfig
from app.storage.in_memory import InMemoryEddRepository


@pytest.mark.asyncio
async def test_with_case_trace_ids_backfills_from_eval_case() -> None:
    repository = InMemoryEddRepository()
    tenant_id = "tenant-a"
    spec = await repository.create_eval_spec(
        tenant_id=tenant_id,
        name="Spec",
        description=None,
        version="1",
        rubric="rubric",
        pass_threshold=70.0,
        judge_config=JudgeConfig(),
    )
    case = await repository.create_eval_case(
        tenant_id=tenant_id,
        eval_spec_id=spec.eval_spec_id,
        name="Case",
        input_payload={"task": "t"},
        notes=None,
        source="langfuse_import",
        langfuse_trace_id="trace-from-case",
    )
    run = await repository.create_experiment_run(
        tenant_id=tenant_id,
        eval_spec_id=spec.eval_spec_id,
        candidate_version="v1",
        status="completed",
        result_count=1,
        completed_at=datetime.now(UTC),
    )
    result = await repository.create_evaluation_result(
        tenant_id=tenant_id,
        experiment_run_id=run.experiment_run_id,
        eval_case_id=case.eval_case_id,
        candidate_version="v1",
        score=80.0,
        passed=True,
        langfuse_trace_id=None,
        langfuse_score_id=None,
        scaffold_output={},
        judge_breakdown={},
    )

    enriched = await _with_case_trace_ids(
        repository,
        tenant_id=tenant_id,
        results=[result],
    )
    assert enriched[0].langfuse_trace_id == "trace-from-case"
