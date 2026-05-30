from __future__ import annotations

from pydantic import BaseModel, Field


class BehaviorRule(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    agent_target_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    severity: str = Field(min_length=1, max_length=32)
    category: str = Field(min_length=1, max_length=64)
    description: str = Field(min_length=1, max_length=5000)
