from __future__ import annotations

from typing import Any

from app.domain.edd.readiness import ReadinessEvaluation

_BEHAVIOR_FAIL = "fail"
_BEHAVIOR_PASS = "pass"
_BEHAVIOR_INSUFFICIENT = "insufficient_evidence"
_BEHAVIOR_NOT_RUN = "not_run"

_TOOL_NOT_DECLARED = "not_declared"
_TOOL_MOCK_ONLY = "mock_only"
_TOOL_LOCAL_ONLY = "local_only"
_TOOL_MOCK_LOCAL = "mock_local"
_TOOL_PRODUCTION_READY = "production_ready"
_TOOL_MISSING = "missing"

_PRODUCTION_NOT_EVALUATED = "not_evaluated"
_PRODUCTION_BLOCKED = "blocked"
_PRODUCTION_READY = "ready"

_OVERALL_FAIL = "fail"
_OVERALL_INSUFFICIENT = "insufficient_evidence"
_OVERALL_PASS = "pass"
_OVERALL_PASS_DEMO = "pass_for_demo_not_production"


def evaluate_readiness(
    *,
    pass_threshold: float,
    overall_score: float | None,
    failure_packet: dict[str, Any] | None,
    tool_mode_summary: str | None = None,
    production_ready: bool | None = None,
    tool_bindings: list[dict[str, Any]] | None = None,
) -> ReadinessEvaluation:
    behavior_status, behavior_explanation = _evaluate_behavior(
        pass_threshold=pass_threshold,
        overall_score=overall_score,
        failure_packet=failure_packet,
    )
    tool_status = _evaluate_tool_status(
        tool_mode_summary=tool_mode_summary,
        tool_bindings=tool_bindings,
    )
    production_status, production_note = _evaluate_production_status(
        behavior_status=behavior_status,
        tool_status=tool_status,
        production_ready=production_ready,
        tool_bindings=tool_bindings,
    )
    overall_status = _derive_overall_status(
        behavior_status=behavior_status,
        production_status=production_status,
    )
    gate_status = _legacy_gate_status(overall_status)
    gate_explanation = _gate_explanation(
        behavior_status=behavior_status,
        behavior_explanation=behavior_explanation,
        overall_status=overall_status,
        production_status=production_status,
        production_note=production_note,
    )
    readiness_explanation = _readiness_explanation(
        behavior_status=behavior_status,
        tool_status=tool_status,
        production_status=production_status,
        overall_status=overall_status,
        production_note=production_note,
    )
    return ReadinessEvaluation(
        behavior_status=behavior_status,
        tool_status=tool_status,
        production_status=production_status,
        overall_status=overall_status,
        gate_status=gate_status,
        gate_explanation=gate_explanation,
        readiness_explanation=readiness_explanation,
    )


def compute_gate(
    *,
    pass_threshold: float,
    overall_score: float | None,
    failure_packet: dict[str, Any] | None,
    tool_mode_summary: str | None = None,
    production_ready: bool | None = None,
    tool_bindings: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    evaluation = evaluate_readiness(
        pass_threshold=pass_threshold,
        overall_score=overall_score,
        failure_packet=failure_packet,
        tool_mode_summary=tool_mode_summary,
        production_ready=production_ready,
        tool_bindings=tool_bindings,
    )
    return evaluation.gate_status, evaluation.gate_explanation


def _evaluate_behavior(
    *,
    pass_threshold: float,
    overall_score: float | None,
    failure_packet: dict[str, Any] | None,
) -> tuple[str, str]:
    if failure_packet:
        failure_type = failure_packet.get("failure_type") or failure_packet.get("summary")
        detail = f" ({failure_type})" if failure_type else ""
        return _BEHAVIOR_FAIL, f"Ingest reported a failure packet{detail}."

    if overall_score is None:
        return _BEHAVIOR_INSUFFICIENT, "No overall_score in eval_summary."

    if overall_score >= pass_threshold:
        return (
            _BEHAVIOR_PASS,
            f"Ingest overall score {overall_score:.1f} meets pass threshold {pass_threshold:.1f}.",
        )
    return (
        _BEHAVIOR_FAIL,
        f"Ingest overall score {overall_score:.1f} is below pass threshold {pass_threshold:.1f}.",
    )


def _evaluate_tool_status(
    *,
    tool_mode_summary: str | None,
    tool_bindings: list[dict[str, Any]] | None,
) -> str:
    if tool_mode_summary:
        normalized = tool_mode_summary.strip().lower().replace("-", "_")
        allowed = {
            _TOOL_NOT_DECLARED,
            _TOOL_MOCK_ONLY,
            _TOOL_LOCAL_ONLY,
            _TOOL_MOCK_LOCAL,
            _TOOL_PRODUCTION_READY,
            _TOOL_MISSING,
        }
        if normalized in allowed:
            return normalized
        return normalized[:32] or _TOOL_NOT_DECLARED

    if not tool_bindings:
        return _TOOL_NOT_DECLARED

    modes = {
        str(binding.get("mode", "")).strip().lower()
        for binding in tool_bindings
        if binding.get("mode")
    }
    if not modes:
        return _TOOL_NOT_DECLARED
    if modes == {_TOOL_MISSING}:
        return _TOOL_MISSING
    if modes <= {"mock"}:
        return _TOOL_MOCK_ONLY
    if modes <= {"local"}:
        return _TOOL_LOCAL_ONLY
    if modes <= {"mock", "local"}:
        return _TOOL_MOCK_LOCAL
    if "live" in modes:
        return _TOOL_PRODUCTION_READY
    return _TOOL_NOT_DECLARED


def _evaluate_production_status(
    *,
    behavior_status: str,
    tool_status: str,
    production_ready: bool | None,
    tool_bindings: list[dict[str, Any]] | None,
) -> tuple[str, str]:
    if behavior_status in {_BEHAVIOR_INSUFFICIENT, _BEHAVIOR_NOT_RUN}:
        return _PRODUCTION_NOT_EVALUATED, (
            "Production readiness not evaluated without behavior evidence."
        )

    if production_ready is True:
        if tool_status in {_TOOL_MOCK_ONLY, _TOOL_LOCAL_ONLY, _TOOL_MOCK_LOCAL, _TOOL_MISSING}:
            return (
                _PRODUCTION_BLOCKED,
                "production_ready was asserted but active tool bindings are "
                "not production-capable.",
            )
        return _PRODUCTION_READY, "Required production tools are marked ready."

    if production_ready is False:
        return _PRODUCTION_BLOCKED, "Publish marked production readiness as blocked."

    if tool_status in {_TOOL_NOT_DECLARED}:
        return _PRODUCTION_NOT_EVALUATED, "No tool mode metadata supplied on ingest."

    if tool_status in {_TOOL_MOCK_ONLY, _TOOL_LOCAL_ONLY, _TOOL_MOCK_LOCAL, _TOOL_MISSING}:
        return (
            _PRODUCTION_BLOCKED,
            "Required tools are mock-only, local-only, or missing for production use.",
        )

    if tool_status == _TOOL_PRODUCTION_READY:
        bindings = tool_bindings or []
        all_live = bool(bindings) and all(
            str(binding.get("mode", "")).strip().lower() == "live" for binding in bindings
        )
        if all_live:
            return _PRODUCTION_READY, "Active tool bindings use live implementations."
        return _PRODUCTION_BLOCKED, "Tool mode summary indicates live tools but bindings are mixed."

    return _PRODUCTION_NOT_EVALUATED, (
        "Production readiness could not be determined from ingest metadata."
    )


def _derive_overall_status(*, behavior_status: str, production_status: str) -> str:
    if behavior_status == _BEHAVIOR_FAIL:
        return _OVERALL_FAIL
    if behavior_status == _BEHAVIOR_INSUFFICIENT:
        return _OVERALL_INSUFFICIENT
    if behavior_status == _BEHAVIOR_NOT_RUN:
        return _OVERALL_INSUFFICIENT
    if production_status == _PRODUCTION_BLOCKED:
        return _OVERALL_PASS_DEMO
    if production_status == _PRODUCTION_READY:
        return _OVERALL_PASS
    return _OVERALL_PASS


def _legacy_gate_status(overall_status: str) -> str:
    if overall_status in {_OVERALL_PASS, _OVERALL_PASS_DEMO}:
        return _BEHAVIOR_PASS
    if overall_status == _OVERALL_INSUFFICIENT:
        return _BEHAVIOR_INSUFFICIENT
    return _OVERALL_FAIL


def _gate_explanation(
    *,
    behavior_status: str,
    behavior_explanation: str,
    overall_status: str,
    production_status: str,
    production_note: str,
) -> str:
    if overall_status == _OVERALL_PASS_DEMO:
        return (
            f"{behavior_explanation} Production readiness is blocked ({production_note}). "
            "Overall: pass_for_demo_not_production."
        )
    return behavior_explanation


def _readiness_explanation(
    *,
    behavior_status: str,
    tool_status: str,
    production_status: str,
    overall_status: str,
    production_note: str,
) -> str:
    return (
        f"behavior={behavior_status}; tool={tool_status}; production={production_status}; "
        f"overall={overall_status}. {production_note}"
    )
