from __future__ import annotations

from pydantic import BaseModel, Field


class InformationRequirement(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    agent_target_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    required: bool = True
    sensitivity: str = Field(min_length=1, max_length=64)
    behavior_rule_ids: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1, max_length=5000)


class ToolRequirement(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    information_requirement_id: str = Field(min_length=1, max_length=128)
    suggested_tool_name: str = Field(min_length=1, max_length=128)
    access_mode: str = Field(min_length=1, max_length=64)
    required_for_demo: bool = True
    required_for_production: bool = True
    purpose: str = Field(min_length=1, max_length=5000)


class ToolFeasibilityReview(BaseModel):
    requirement_id: str = Field(min_length=1, max_length=128)
    suggested_tool_name: str = Field(min_length=1, max_length=128)
    implementation_status: str = Field(min_length=1, max_length=64)
    mvp_strategy: str = Field(min_length=1, max_length=256)
    production_strategy: str = Field(min_length=1, max_length=256)
    feasibility_status: str = Field(min_length=1, max_length=64)
    demo_ready: bool
    production_ready: bool
    risks: list[str] = Field(default_factory=list)


class ToolBinding(BaseModel):
    graph_node: str = Field(min_length=1, max_length=128)
    requirement_id: str = Field(min_length=1, max_length=128)
    active_implementation: str = Field(min_length=1, max_length=128)
    mode: str = Field(min_length=1, max_length=64)
    environment: str = Field(min_length=1, max_length=64)
