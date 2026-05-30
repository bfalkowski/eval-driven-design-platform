#!/usr/bin/env python3
"""Automate DEMO_SCRIPT.md steps 2-6 against a running EDD API (live HTTP).

Usage:
  ./scripts/run_demo_loop.sh
  EDD_API_KEY=<jwt> ./scripts/run_demo_loop.sh
  RUN_DEMO_LAB_SMOKE=1 ./scripts/run_demo_loop.sh   # also run lab publish smoke if present
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "api"
API_BASE = os.environ.get("EDD_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TENANT_ID = os.environ.get("EDD_TENANT_ID", "tenant-a")
RUN_LAB_SMOKE = os.environ.get("RUN_DEMO_LAB_SMOKE", "").strip().lower() in {
    "1",
    "true",
    "yes",
}


def fail(message: str) -> None:
    print(f"✗ {message}", file=sys.stderr)
    sys.exit(1)


def step(message: str) -> None:
    print(f"\n→ {message}")


def pass_msg(message: str) -> None:
    print(f"✓ {message}")


def resolve_bearer_token() -> str:
    api_key = os.environ.get("EDD_API_KEY", "").strip()
    if api_key:
        return api_key

    token_file = os.environ.get("EDD_TOKEN_FILE", f"{os.environ.get('TMPDIR', '/tmp')}/edd-api.token")
    token_path = Path(token_file)
    if token_path.is_file():
        return token_path.read_text(encoding="utf-8").strip()

    mint_script = REPO_ROOT / "scripts" / "create_demo_jwt.py"
    if not (API_ROOT / "pyproject.toml").is_file():
        return ""

    result = subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(mint_script),
            "--tenant-id",
            TENANT_ID,
            "--subject",
            "demo-loop",
        ],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return ""


def request_json(
    method: str,
    path: str,
    *,
    bearer_token: str,
    body: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    url = f"{API_BASE}{path}"
    if params:
        query = "&".join(f"{key}={value}" for key, value in params.items())
        url = f"{url}?{query}"

    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15.0) as response:
            payload = response.read().decode("utf-8")
            parsed: dict[str, Any] = json.loads(payload) if payload else {}
            return response.status, parsed
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"{method} {path} failed: HTTP {exc.code} {detail}")
    except URLError as exc:
        fail(f"{method} {path} failed: {exc.reason}")
    raise AssertionError("unreachable")


def wait_for_api() -> None:
    for _ in range(40):
        try:
            with urlopen(f"{API_BASE}/v1/health", timeout=2.0) as response:
                if response.status == 200:
                    return
        except URLError:
            pass
        time.sleep(0.25)
    fail(f"API not reachable at {API_BASE}/v1/health")


def tenant_params(bearer_token: str) -> dict[str, str]:
    if bearer_token:
        return {}
    return {"tenant_id": TENANT_ID}


def main() -> None:
    bearer_token = resolve_bearer_token()
    auth_mode = "bearer" if bearer_token else "tenant_query"

    step(f"Wait for API at {API_BASE}")
    wait_for_api()
    pass_msg("API health OK")

    step("GET /v1/health and /v1/ready")
    for path in ("/v1/health", "/v1/ready"):
        status, _ = request_json("GET", path, bearer_token=bearer_token)
        if status != 200:
            fail(f"{path} returned HTTP {status}")
    pass_msg("health + ready OK")

    step("Create EvalSpec (DEMO step 2)")
    spec_body: dict[str, Any] = {
        "name": "Demo loop spec",
        "description": "Automated demo loop eval spec",
        "rubric": "Mention resolution steps and empathy.",
        "pass_threshold": 75,
    }
    if not bearer_token:
        spec_body["tenant_id"] = TENANT_ID
    status, spec = request_json("POST", "/v1/eval-specs", bearer_token=bearer_token, body=spec_body)
    if status != 201:
        fail(f"create eval spec failed: HTTP {status}")
    spec_id = str(spec["eval_spec_id"])
    pass_msg(f"EvalSpec created: {spec_id}")

    step("Create EvalCase (DEMO step 3)")
    case_body: dict[str, Any] = {
        "eval_spec_id": spec_id,
        "name": "Demo loop case",
        "input_payload": {
            "task": "Handle refund request with empathy and clear next steps.",
        },
        "notes": "Created by scripts/run_demo_loop.py",
    }
    if not bearer_token:
        case_body["tenant_id"] = TENANT_ID
    status, case = request_json("POST", "/v1/eval-cases", bearer_token=bearer_token, body=case_body)
    if status != 201:
        fail(f"create eval case failed: HTTP {status}")
    case_id = str(case["eval_case_id"])
    pass_msg(f"EvalCase created: {case_id}")

    step("Run experiment (DEMO step 4, candidate prompt_v4)")
    run_body: dict[str, Any] = {
        "eval_spec_id": spec_id,
        "candidate_version": "prompt_v4",
        "eval_case_ids": [case_id],
    }
    if not bearer_token:
        run_body["tenant_id"] = TENANT_ID
    status, run = request_json("POST", "/v1/experiment-runs", bearer_token=bearer_token, body=run_body)
    if status != 201:
        fail(f"create experiment run failed: HTTP {status}")
    run_id = str(run["experiment_run_id"])
    pass_msg(f"ExperimentRun created: {run_id}")

    step("Fetch run summary and evaluation results (DEMO step 5)")
    params = tenant_params(bearer_token)
    status, summary = request_json(
        "GET",
        f"/v1/experiment-runs/{run_id}/summary",
        bearer_token=bearer_token,
        params=params,
    )
    if status != 200:
        fail(f"run summary failed: HTTP {status}")
    if summary.get("result_count", 0) < 1:
        fail("expected at least one evaluation result in summary")

    list_params = {**params, "experiment_run_id": run_id}
    status, results_payload = request_json(
        "GET",
        "/v1/evaluation-results",
        bearer_token=bearer_token,
        params=list_params,
    )
    if status != 200:
        fail(f"list evaluation results failed: HTTP {status}")
    results = results_payload.get("evaluation_results", [])
    if not results:
        fail("expected evaluation results for experiment run")
    pass_msg(
        f"summary avg={summary.get('average_score')} pass_rate={summary.get('pass_rate')} "
        f"results={len(results)}"
    )

    step("Quality gate (DEMO step 6)")
    status, gate = request_json(
        "GET",
        f"/v1/experiment-runs/{run_id}/gate",
        bearer_token=bearer_token,
        params=params,
    )
    if status != 200:
        fail(f"gate GET failed: HTTP {status}")
    gate_status = gate.get("gate_status")
    if gate.get("evaluation_source") != "experiment_results":
        fail(f"expected evaluation_source=experiment_results, got {gate.get('evaluation_source')!r}")
    if gate_status != "pass":
        fail(
            f"expected gate_status=pass for platform demo run, got {gate_status!r} "
            f"({gate.get('gate_explanation')})"
        )
    pass_msg(f"gate_status={gate_status} auth={auth_mode}")

    step("run_quality_gate.sh exit check")
    env = os.environ.copy()
    env["EDD_API_BASE_URL"] = API_BASE
    env["EDD_TENANT_ID"] = TENANT_ID
    if bearer_token:
        env["EDD_API_KEY"] = bearer_token
    gate_script = REPO_ROOT / "scripts" / "run_quality_gate.sh"
    result = subprocess.run(
        [str(gate_script), run_id],
        cwd=REPO_ROOT,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        fail(f"run_quality_gate.sh exited {result.returncode} for run {run_id}")
    pass_msg("run_quality_gate.sh exit 0")

    if RUN_LAB_SMOKE:
        lab_root = Path(os.environ.get("EDD_LAB_ROOT", REPO_ROOT.parent / "edd-agent-lab"))
        lab_smoke = lab_root / "scripts" / "test_platform_publish.sh"
        if lab_smoke.is_file():
            step("Optional lab publish smoke (DEMO step 7)")
            lab_env = env.copy()
            lab_env["EDD_PLATFORM_ROOT"] = str(REPO_ROOT)
            lab_env["EDD_EVAL_SPEC_ID"] = spec_id
            lab_result = subprocess.run([str(lab_smoke)], cwd=lab_root, env=lab_env, check=False)
            if lab_result.returncode != 0:
                fail("test_platform_publish.sh failed")
            pass_msg("lab publish smoke OK")
        else:
            print(f"skip lab smoke: {lab_smoke} not found")

    print(f"\nDemo loop passed (run_id={run_id}, auth={auth_mode})")


if __name__ == "__main__":
    main()
