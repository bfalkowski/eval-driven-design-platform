from __future__ import annotations

from typing import Any

from app.domain.models import EvalCase, EvalSpec


def evaluate_mock(
    *,
    spec: EvalSpec,
    case: EvalCase,
    scaffold_output: dict[str, Any],
) -> tuple[float, bool, dict[str, float]]:
    output = str(scaffold_output.get("output", ""))
    rubric_overlap = _overlap_score(spec.rubric, output)
    task_text = str(case.input_payload.get("task", case.name))
    task_overlap = _overlap_score(task_text, output)
    length_score = min(len(output) // 12, 25)
    score = min(100.0, float(rubric_overlap + task_overlap + length_score))
    passed = score >= spec.pass_threshold
    breakdown = {
        "rubric_overlap": float(rubric_overlap),
        "task_overlap": float(task_overlap),
        "length_score": float(length_score),
    }
    return score, passed, breakdown


def _overlap_score(left: str, right: str) -> int:
    overlap = _significant_terms(left) & _significant_terms(right)
    return min(len(overlap) * 12, 40)


def _significant_terms(text: str) -> set[str]:
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "is",
        "it",
        "for",
        "on",
        "with",
        "are",
        "this",
        "that",
    }
    terms = {token.lower().strip(".,!?;:()[]{}\"'") for token in text.split() if len(token) > 3}
    return terms - stop_words
