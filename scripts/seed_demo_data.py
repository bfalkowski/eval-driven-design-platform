#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed demo EvalSpec, EvalCase, and ExperimentRun.")
    parser.add_argument("--base-url", default=os.getenv("EDD_API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--tenant-id", default="demo-tenant")
    parser.add_argument("--token", default=os.getenv("EDD_BEARER_TOKEN"))
    args = parser.parse_args()

    headers = {"content-type": "application/json"}
    if args.token:
        headers["authorization"] = f"Bearer {args.token}"

    base_url = args.base_url.rstrip("/")
    tenant_id = args.tenant_id

    with httpx.Client(base_url=base_url, headers=headers, timeout=15.0) as client:
        spec_payload = {
            "name": "Support workflow quality",
            "description": "Demo eval spec for local EDD walkthrough",
            "rubric": "Mention empathy, resolution steps, failures, latency, or quality.",
            "pass_threshold": 70,
        }
        if not args.token:
            spec_payload["tenant_id"] = tenant_id

        spec_response = client.post("/v1/eval-specs", json=spec_payload)
        spec_response.raise_for_status()
        spec = spec_response.json()

        case_payload = {
            "eval_spec_id": spec["eval_spec_id"],
            "name": "Refund escalation",
            "input_payload": {
                "task": "Handle refund request with empathy and clear next steps.",
            },
            "notes": "Seeded by scripts/seed_demo_data.py",
        }
        if not args.token:
            case_payload["tenant_id"] = tenant_id

        case_response = client.post("/v1/eval-cases", json=case_payload)
        case_response.raise_for_status()
        case = case_response.json()

        run_payload = {
            "eval_spec_id": spec["eval_spec_id"],
            "candidate_version": "prompt_v4",
            "eval_case_ids": [case["eval_case_id"]],
        }
        if not args.token:
            run_payload["tenant_id"] = tenant_id

        run_response = client.post("/v1/experiment-runs", json=run_payload)
        run_response.raise_for_status()
        run = run_response.json()

        params = {} if args.token else {"tenant_id": tenant_id}
        summary_response = client.get(
            f"/v1/experiment-runs/{run['experiment_run_id']}/summary",
            params=params,
        )
        summary_response.raise_for_status()
        summary = summary_response.json()

    print(json.dumps({"spec": spec, "case": case, "run": run, "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except httpx.HTTPError as exc:
        print(f"Seed failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
