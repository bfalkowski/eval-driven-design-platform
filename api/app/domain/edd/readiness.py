from __future__ import annotations

from pydantic import BaseModel, Field


class ReadinessEvaluation(BaseModel):
    """Behavior, tool, and production readiness split per HLD-004 / HLD-012."""

    behavior_status: str = Field(min_length=1, max_length=32)
    tool_status: str = Field(min_length=1, max_length=32)
    production_status: str = Field(min_length=1, max_length=32)
    overall_status: str = Field(min_length=1, max_length=64)
    gate_status: str = Field(min_length=1, max_length=64)
    gate_explanation: str = Field(min_length=1, max_length=5000)
    readiness_explanation: str = Field(min_length=1, max_length=5000)
