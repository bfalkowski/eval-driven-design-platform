from __future__ import annotations

import hashlib
from typing import Any

from app.domain.models import EvalCase


def run_scaffold(*, case: EvalCase, candidate_version: str) -> dict[str, Any]:
    task = str(case.input_payload.get("task", case.name))
    seed = hashlib.sha256(f"{candidate_version}:{case.eval_case_id}:{task}".encode()).hexdigest()
    quality_suffix = (
        " We monitor failures, latency, cost, and quality trends."
        if int(seed[:2], 16) % 2 == 0
        else " Resolution steps and empathy are included."
    )
    output = f"Candidate {candidate_version} workflow output for: {task}.{quality_suffix}"
    return {
        "candidate_version": candidate_version,
        "workflow": "mock-support-agent",
        "steps_executed": 3,
        "output": output,
    }
