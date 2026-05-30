from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import BadRequestError
from app.domain.models import RunIngestEnvelope

SUPPORTED_PUBLISH_SCHEMA_VERSIONS = frozenset({"1", "2"})


class ParsePublishEnvelope(BaseModel):
    """Loose publish payload accepting v1 flat fields and v2 structured sections."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(min_length=1, max_length=16)
    source: str | None = Field(default=None, min_length=1, max_length=64)
    run_id: str | None = Field(default=None, min_length=1, max_length=128)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=256)
    candidate_version: str | None = Field(default=None, min_length=1, max_length=128)
    subject_id: str | None = Field(default=None, min_length=1, max_length=128)
    agent: str | dict[str, Any] | None = None
    suite_id: str | None = Field(default=None, min_length=1, max_length=128)
    suite: str | None = Field(default=None, min_length=1, max_length=128)
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    eval_spec_id: Any | None = None
    scenario_ids: list[str] = Field(default_factory=list)
    started_at: str | None = Field(default=None, max_length=64)
    completed_at: str | None = Field(default=None, max_length=64)
    outputs: dict[str, Any] = Field(default_factory=dict)
    eval_summary: dict[str, Any] | None = None
    failure_packet: dict[str, Any] | None = None
    artifact_paths: dict[str, Any] = Field(default_factory=dict)
    tool_mode_summary: str | None = Field(default=None, max_length=64)
    production_ready: bool | None = None
    tool_bindings: list[dict[str, Any]] | None = None
    producer: dict[str, Any] | None = None
    target: dict[str, Any] | str | None = None
    eval_contract: dict[str, Any] | str | None = None
    agent_version: str | dict[str, Any] | None = None
    tool_context: dict[str, Any] | None = None
    scenario_set: dict[str, Any] | None = None
    run: dict[str, Any] | None = None


def normalize_publish_envelope(payload: ParsePublishEnvelope) -> RunIngestEnvelope:
    if payload.schema_version not in SUPPORTED_PUBLISH_SCHEMA_VERSIONS:
        msg = (
            f"Unsupported schema_version: {payload.schema_version!r}. "
            f"Expected one of {sorted(SUPPORTED_PUBLISH_SCHEMA_VERSIONS)}."
        )
        raise BadRequestError(msg)

    if payload.schema_version == "1":
        return _normalize_v1(payload)

    return _normalize_v2(payload)


def _normalize_v1(payload: ParsePublishEnvelope) -> RunIngestEnvelope:
    if not payload.run_id:
        raise BadRequestError("run_id is required for schema_version '1'.")
    if not payload.source:
        raise BadRequestError("source is required for schema_version '1'.")
    agent_value = _agent_id(payload.agent)
    return RunIngestEnvelope(
        schema_version="1",
        source=payload.source,
        run_id=payload.run_id,
        idempotency_key=payload.idempotency_key,
        candidate_version=payload.candidate_version,
        agent_version=_agent_version_label(payload),
        subject_id=payload.subject_id or agent_value,
        agent=agent_value,
        suite_id=payload.suite_id,
        suite=payload.suite,
        tenant_id=payload.tenant_id,
        eval_spec_id=payload.eval_spec_id,
        scenario_ids=list(payload.scenario_ids),
        started_at=payload.started_at,
        completed_at=payload.completed_at,
        outputs=dict(payload.outputs),
        eval_summary=payload.eval_summary,
        failure_packet=payload.failure_packet,
        artifact_paths=dict(payload.artifact_paths),
        tool_mode_summary=payload.tool_mode_summary,
        production_ready=payload.production_ready,
        tool_bindings=payload.tool_bindings,
    )


def _normalize_v2(payload: ParsePublishEnvelope) -> RunIngestEnvelope:
    producer = payload.producer or {}
    for field in ("name", "environment", "run_mode"):
        if not str(producer.get(field, "")).strip():
            raise BadRequestError(f"producer.{field} is required for schema_version '2'.")

    run_block = payload.run or {}
    run_id = payload.run_id or str(run_block.get("id") or "").strip()
    if not run_id:
        raise BadRequestError("run_id or run.id is required for schema_version '2'.")

    source = (payload.source or str(producer.get("name") or "")).strip()
    if not source:
        raise BadRequestError("source or producer.name is required for schema_version '2'.")

    tool_context = payload.tool_context or {}
    tool_bindings = payload.tool_bindings or tool_context.get("tool_bindings")
    if tool_bindings is not None and not isinstance(tool_bindings, list):
        raise BadRequestError("tool_context.tool_bindings must be a list when provided.")

    scenario_set = payload.scenario_set or {}
    scenario_ids = list(payload.scenario_ids or scenario_set.get("scenario_ids") or [])

    agent_version_ref = payload.agent_version
    if isinstance(agent_version_ref, dict):
        agent_version = str(
            agent_version_ref.get("version_label")
            or agent_version_ref.get("id")
            or ""
        ).strip()
    else:
        agent_version = str(agent_version_ref or "").strip()

    agent_value = _agent_id(payload.agent)
    if not agent_value and isinstance(agent_version_ref, dict):
        agent_value = str(agent_version_ref.get("agent_id") or "").strip() or None

    candidate_version = payload.candidate_version or agent_version
    if not candidate_version:
        raise BadRequestError("agent_version or candidate_version is required for schema_version '2'.")

    target_id = _reference_id(payload.target)
    eval_contract_id = _reference_id(payload.eval_contract)

    tool_mode_summary = payload.tool_mode_summary or tool_context.get("tool_mode_summary")
    production_ready = payload.production_ready
    if production_ready is None and "production_ready" in tool_context:
        production_ready = tool_context.get("production_ready")

    return RunIngestEnvelope(
        schema_version="2",
        source=source,
        run_id=run_id,
        idempotency_key=payload.idempotency_key,
        candidate_version=candidate_version,
        agent_version=agent_version or candidate_version,
        subject_id=payload.subject_id or agent_value,
        agent=agent_value,
        suite_id=payload.suite_id,
        suite=payload.suite,
        tenant_id=payload.tenant_id,
        eval_spec_id=payload.eval_spec_id,
        scenario_ids=scenario_ids,
        started_at=payload.started_at or run_block.get("started_at"),
        completed_at=payload.completed_at or run_block.get("completed_at"),
        outputs=dict(payload.outputs or run_block.get("raw_output") or {}),
        eval_summary=payload.eval_summary,
        failure_packet=payload.failure_packet,
        artifact_paths=dict(payload.artifact_paths),
        tool_mode_summary=str(tool_mode_summary).strip() if tool_mode_summary else None,
        production_ready=production_ready,
        tool_bindings=tool_bindings,
        producer=dict(producer),
        target_id=target_id,
        eval_contract_ref_id=eval_contract_id,
    )


def _agent_id(agent: str | dict[str, Any] | None) -> str | None:
    if agent is None:
        return None
    if isinstance(agent, str):
        return agent
    return str(agent.get("id") or agent.get("name") or "").strip() or None


def _agent_version_label(payload: ParsePublishEnvelope) -> str | None:
    value = payload.agent_version
    if isinstance(value, dict):
        return str(value.get("version_label") or value.get("id") or "").strip() or None
    if isinstance(value, str):
        return value
    return None


def _reference_id(value: dict[str, Any] | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    return str(value.get("id") or "").strip() or None
