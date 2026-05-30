from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TraceLink(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    provider: str = Field(default="langfuse", max_length=64)
    external_trace_id: str = Field(min_length=1, max_length=256)
    external_url: str | None = Field(default=None, max_length=2000)
    experiment_run_id: str | None = Field(default=None, max_length=128)
    operational_run_id: str | None = Field(default=None, max_length=128)
    scenario_id: str | None = Field(default=None, max_length=128)
    agent_version_id: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
