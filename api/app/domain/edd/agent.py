from __future__ import annotations

from pydantic import BaseModel, Field


class Agent(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=5000)


class AgentTarget(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    agent_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    purpose: str = Field(min_length=1, max_length=5000)
    intended_users: list[str] = Field(default_factory=list)
    primary_goals: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)
