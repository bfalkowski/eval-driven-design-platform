from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EvalMetric(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    scale_min: float
    scale_max: float
    behavior_rule_ids: list[str] = Field(default_factory=list)
    rubric: str = Field(min_length=1, max_length=10_000)


class EvalContractGate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=256)
    gate_type: str = Field(min_length=1, max_length=32, alias="type")
    category: str = Field(min_length=1, max_length=64)
    condition: str = Field(min_length=1, max_length=500)


class EvalContract(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    agent_target_id: str = Field(min_length=1, max_length=128)
    version: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=256)
    metrics: list[EvalMetric] = Field(default_factory=list)
    gates: list[EvalContractGate] = Field(default_factory=list)
