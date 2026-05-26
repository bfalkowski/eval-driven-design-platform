from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JudgeConfig(BaseModel):
    judge_id: str = Field(default="mock", min_length=1, max_length=128)
    version: str = Field(default="1", min_length=1, max_length=64)
    rubric_id: str | None = Field(default=None, max_length=128)


class EvalSpec(BaseModel):
    eval_spec_id: UUID
    tenant_id: str
    name: str
    description: str | None = None
    version: str
    rubric: str
    pass_threshold: float = Field(ge=0, le=100)
    judge_config: JudgeConfig
    created_at: datetime
    updated_at: datetime


class CreateEvalSpecRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2000)
    version: str = Field(default="1", min_length=1, max_length=64)
    rubric: str = Field(min_length=1, max_length=10_000)
    pass_threshold: float = Field(default=70.0, ge=0, le=100)
    judge_config: JudgeConfig = Field(default_factory=JudgeConfig)


class UpdateEvalSpecRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=2000)
    version: str | None = Field(default=None, min_length=1, max_length=64)
    rubric: str | None = Field(default=None, min_length=1, max_length=10_000)
    pass_threshold: float | None = Field(default=None, ge=0, le=100)
    judge_config: JudgeConfig | None = None


class EvalSpecResponse(EvalSpec):
    request_id: str


class EvalSpecListResponse(BaseModel):
    eval_specs: list[EvalSpec]
    request_id: str


class EvalCase(BaseModel):
    eval_case_id: UUID
    tenant_id: str
    eval_spec_id: UUID
    name: str
    input_payload: dict[str, Any]
    notes: str | None = None
    source: str
    langfuse_trace_id: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateEvalCaseRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=128)
    eval_spec_id: UUID
    name: str = Field(min_length=1, max_length=256)
    input_payload: dict[str, Any]
    notes: str | None = Field(default=None, max_length=5000)
    source: str = Field(default="manual", min_length=1, max_length=64)
    langfuse_trace_id: str | None = Field(default=None, max_length=256)


class UpdateEvalCaseRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=256)
    input_payload: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=5000)
    source: str | None = Field(default=None, min_length=1, max_length=64)
    langfuse_trace_id: str | None = Field(default=None, max_length=256)


class EvalCaseResponse(EvalCase):
    request_id: str


class EvalCaseListResponse(BaseModel):
    eval_cases: list[EvalCase]
    request_id: str
