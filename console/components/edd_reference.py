from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCENARIO_NAME = "customer_escalation_triage"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = _REPO_ROOT / "api"
_DOCKER_API_ROOT = Path("/opt/edd-api")


def _ensure_api_import_path() -> None:
    for candidate in (_API_ROOT, _DOCKER_API_ROOT):
        candidate_str = str(candidate)
        if candidate.is_dir() and candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


_ensure_api_import_path()

from app.domain.edd.agent import Agent, AgentTarget  # noqa: E402
from app.domain.edd.artifacts import load_graph_design_bundle, load_yaml_document  # noqa: E402
from app.domain.edd.eval_contract import EvalContract  # noqa: E402
from app.domain.edd.graph_design import GraphDesign, GraphNode  # noqa: E402
from app.domain.edd.requirements import (  # noqa: E402
    InformationRequirement,
    ToolFeasibilityReview,
    ToolRequirement,
)
from app.domain.edd.rules import BehaviorRule  # noqa: E402


def resolve_reference_scenario_dir() -> Path:
    configured = os.environ.get("EDD_REFERENCE_SCENARIO_DIR", "").strip()
    if configured:
        return Path(configured)

    candidates = (
        _REPO_ROOT / "examples" / DEFAULT_SCENARIO_NAME,
        Path("/app/examples") / DEFAULT_SCENARIO_NAME,
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    msg = (
        "Reference scenario directory not found. Set EDD_REFERENCE_SCENARIO_DIR "
        f"or mount examples/{DEFAULT_SCENARIO_NAME}."
    )
    raise FileNotFoundError(msg)


@dataclass(frozen=True)
class GraphDesignBundle:
    design: GraphDesign
    nodes: list[GraphNode]


@dataclass(frozen=True)
class ReferenceScenario:
    scenario_dir: Path
    agent: Agent
    agent_target: AgentTarget
    behavior_rules: list[BehaviorRule]
    eval_contract: EvalContract
    information_requirements: list[InformationRequirement]
    tool_requirements: list[ToolRequirement]
    tool_feasibility: list[ToolFeasibilityReview]
    graph_design_v0: GraphDesignBundle
    graph_design_v1: GraphDesignBundle


def load_graph_design(version: str, scenario_dir: Path | None = None) -> GraphDesignBundle:
    root = scenario_dir or resolve_reference_scenario_dir()
    filename = "graph-design-v0.yaml" if version == "v0" else "graph-design-v1.yaml"
    design, nodes = load_graph_design_bundle(root / filename)
    return GraphDesignBundle(design=design, nodes=nodes)


def load_reference_scenario(
    scenario_dir: Path | None = None,
) -> ReferenceScenario:
    root = scenario_dir or resolve_reference_scenario_dir()

    agent_target_doc = load_yaml_document(root / "agent-target.yaml")
    behavior_rules_doc = load_yaml_document(root / "behavior-rules.yaml")
    eval_contract_doc = load_yaml_document(root / "eval-contract.yaml")
    information_doc = load_yaml_document(root / "information-requirements.yaml")
    tool_requirements_doc = load_yaml_document(root / "tool-requirements.yaml")
    tool_feasibility_doc = load_yaml_document(root / "tool-feasibility.yaml")

    agent = Agent.model_validate(agent_target_doc["agent"])
    agent_target = AgentTarget.model_validate(agent_target_doc["agent_target"])
    behavior_rules = [
        BehaviorRule.model_validate(item) for item in behavior_rules_doc["behavior_rules"]
    ]
    eval_contract = EvalContract.model_validate(eval_contract_doc["eval_contract"])
    information_requirements = [
        InformationRequirement.model_validate(item)
        for item in information_doc["information_requirements"]
    ]
    tool_requirements = [
        ToolRequirement.model_validate(item) for item in tool_requirements_doc["tool_requirements"]
    ]
    tool_feasibility = [
        ToolFeasibilityReview.model_validate(item)
        for item in tool_feasibility_doc["tool_feasibility"]
    ]

    return ReferenceScenario(
        scenario_dir=root,
        agent=agent,
        agent_target=agent_target,
        behavior_rules=behavior_rules,
        eval_contract=eval_contract,
        information_requirements=information_requirements,
        tool_requirements=tool_requirements,
        tool_feasibility=tool_feasibility,
        graph_design_v0=load_graph_design("v0", root),
        graph_design_v1=load_graph_design("v1", root),
    )
