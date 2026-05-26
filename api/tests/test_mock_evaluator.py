from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.domain.models import EvalCase, EvalSpec, JudgeConfig
from app.services.mock_evaluator import evaluate_mock
from app.services.scaffold_runner import run_scaffold


def _sample_spec() -> EvalSpec:
    now = datetime.now(UTC)
    return EvalSpec(
        eval_spec_id=UUID("00000000-0000-0000-0000-000000000001"),
        tenant_id="tenant-a",
        name="Support quality",
        description=None,
        version="1",
        rubric="Mention empathy, resolution steps, failures, or quality.",
        pass_threshold=70.0,
        judge_config=JudgeConfig(),
        created_at=now,
        updated_at=now,
    )


def _sample_case() -> EvalCase:
    now = datetime.now(UTC)
    return EvalCase(
        eval_case_id=UUID("00000000-0000-0000-0000-000000000002"),
        tenant_id="tenant-a",
        eval_spec_id=UUID("00000000-0000-0000-0000-000000000001"),
        name="Refund escalation",
        input_payload={"task": "Handle refund request with empathy and clear next steps."},
        notes=None,
        source="manual",
        langfuse_trace_id=None,
        created_at=now,
        updated_at=now,
    )


def test_scaffold_and_evaluator_are_deterministic() -> None:
    spec = _sample_spec()
    case = _sample_case()
    first_output = run_scaffold(case=case, candidate_version="prompt_v4")
    second_output = run_scaffold(case=case, candidate_version="prompt_v4")
    assert first_output == second_output

    first_score, first_passed, first_breakdown = evaluate_mock(
        spec=spec,
        case=case,
        scaffold_output=first_output,
    )
    second_score, second_passed, second_breakdown = evaluate_mock(
        spec=spec,
        case=case,
        scaffold_output=second_output,
    )
    assert first_score == second_score
    assert first_passed == second_passed
    assert first_breakdown == second_breakdown
