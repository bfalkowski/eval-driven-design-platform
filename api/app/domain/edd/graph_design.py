from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GraphNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1, max_length=128)
    graph_design_id: str | None = Field(default=None, max_length=128)
    name: str | None = Field(default=None, max_length=256)
    purpose: str = Field(min_length=1, max_length=5000)
    behavior_rule_ids: list[str] = Field(default_factory=list, alias="supports_rules")
    information_requirement_ids: list[str] = Field(
        default_factory=list,
        alias="information_requirements",
    )
    tool_requirement_ids: list[str] = Field(default_factory=list, alias="tool_requirements")
    tool_binding_ids: list[str] = Field(default_factory=list, alias="tool_bindings")
    active_tool_binding: str | None = Field(default=None, max_length=128)
    tool_mode: str | None = Field(default=None, max_length=32)
    production_blocker: bool | None = None
    failure_packets_addressed: list[str] = Field(default_factory=list)
    reads_state: list[str] = Field(default_factory=list)
    writes_state: list[str] = Field(default_factory=list)
    operational_safety_notes: list[str] = Field(default_factory=list)


class GraphDesign(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    agent_target_id: str = Field(min_length=1, max_length=128)
    eval_contract_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    description: str = Field(min_length=1, max_length=5000)
    source_version: str | None = Field(default=None, max_length=64)
    fix_plan_id: str | None = Field(default=None, max_length=128)
    graph_node_ids: list[str] = Field(default_factory=list)
    flow_order: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", min_length=1, max_length=32)
