from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.domain.edd.graph_design import GraphDesign, GraphNode


def load_yaml_document(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = f"Expected mapping at root of {path.name}"
        raise ValueError(msg)
    return payload


def load_graph_design_bundle(path: Path) -> tuple[GraphDesign, list[GraphNode]]:
    document = load_yaml_document(path)
    graph_design = GraphDesign.model_validate(document["graph_design"])
    graph_nodes = [GraphNode.model_validate(item) for item in document.get("graph_nodes", [])]
    return graph_design, graph_nodes
