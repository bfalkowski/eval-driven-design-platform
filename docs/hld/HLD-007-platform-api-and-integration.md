# HLD-007: Platform API and Integration

## Status

Draft

## Purpose

This document defines the platform API and integration model for the **EDD stack**.

The purpose of this HLD is to make the boundary between **edd-agent-lab** and **eval-driven-design-platform** explicit.

The platform is the canonical control plane for evaluation-driven design workflow objects. The lab remains the runnable agent development environment. Integration means lab runs, artifacts, trace links, eval summaries, failure packets, comparisons, gates, and promotion records can be published into the platform.

Running both repos locally is not enough.

They are integrated only when data flows from the lab into the platform and becomes associated with canonical platform objects.

See also:

- [HLD-001: Product intent and system boundaries](HLD-001-product-intent-and-system-boundaries.md)
- [HLD-004: Tool requirements and feasibility](HLD-004-tool-requirements-and-feasibility.md)
- [HLD-006: MVP implementation plan](HLD-006-mvp-implementation-plan.md) — Milestone 4
- `docs/05-platform-integration.md` (edd-agent-lab) — publish seam today

---

## System Boundary

```text
edd-agent-lab
  owns:
    - runnable LangGraph agents
    - local mock tools
    - local scenarios
    - local eval execution
    - run artifacts
    - failure packets
    - fix plans
    - comparison artifacts
    - publish client

eval-driven-design-platform
  owns:
    - canonical agent registry
    - target/rule/eval contract objects
    - information/tool requirement objects
    - tool feasibility
    - run registry
    - comparison registry
    - gate results
    - promotion decisions
    - platform console
    - Langfuse trace linkage/orchestration

Langfuse
  owns:
    - trace evidence
    - spans
    - generations
    - model inputs/outputs
    - tool calls
    - token usage
    - cost
    - latency
    - scores/annotations
```

The platform is the source of truth for product meaning.

The lab is the source of concrete executable agent examples.

Langfuse is the source of runtime trace evidence.

---

## Integration Goals

The integration should support this workflow:

```text
1. Platform defines or stores agent target, rules, eval contract, and requirements.
2. Lab implements and runs agent versions against scenarios.
3. Lab publishes run artifacts to platform.
4. Platform registers the run.
5. Platform links traces, scores, failures, comparisons, gates, and promotion decisions.
6. Platform console displays the full design story.
```

The key integration story:

```text
v0 failed because it overclaimed root cause.
v1 fixed that by adding evidence normalization and facts/hypotheses separation.
v1 passes behavior gates.
v1 remains blocked for production because required tools are mock/local only.
```

The API should preserve the data needed to tell that story.

---

## Current Implementation (snapshot)

Use this table when implementing Phase 9 / HLD-006 M4. Do not break the working v1 path while adding v2 fields.

| Area | Today (v1) | Target (this HLD) |
|---|---|---|
| **Publish endpoint** | `POST /v1/integrations/runs/publish` | Same |
| **Deprecated alias** | `POST /v1/integrations/lab/publish` (OpenAPI `deprecated: true`) | Same + optional `warnings` in response |
| **Lab envelope** | `schema_version: "1"`, `source`, `run_id`, `agent`, `agent_version`, `suite`, `eval_summary`, `failure_packet`, `eval_spec_id` | Structured sections: `producer`, `target`, `eval_contract`, `tool_context`, etc. |
| **Platform response** | `platform_run_id`, `gate_status`, `gate_explanation` | + `behavior_status`, `tool_status`, `production_status`, `overall_status`, linked object IDs |
| **Idempotency** | Re-publish same `run_id` updates ingest | Explicit `producer_run_id` / idempotency key |
| **Read APIs** | `GET /v1/experiment-runs/{id}`, `GET /v1/experiment-runs/{id}/gate` | + agent/version/comparison/gate-result resources (may map to ingest JSON initially) |
| **Lab CLI** | `edd-lab publish-run` via `EDD_API_BASE_URL` (default local stub) | Same command; richer payload builder |

Lab publish target is the **platform API** (`http://127.0.0.1:8000`), not the Streamlit console (`:8501`).

---

## Primary Publish Endpoint

The primary endpoint for lab-to-platform publishing is:

```http
POST /v1/integrations/runs/publish
```

This endpoint replaces the earlier lab-specific endpoint name:

```http
POST /v1/integrations/lab/publish
```

The old endpoint may exist temporarily as a deprecated alias, but new code and documentation should use:

```http
POST /v1/integrations/runs/publish
```

Reason:

```text
The integration is not conceptually about the lab.
It is about publishing a run from an external producer into the platform.
```

**Status today:** both routes exist; runs alias delegates to the same handler.

---

## Deprecated Alias

If implemented, this endpoint should behave identically:

```http
POST /v1/integrations/lab/publish
```

But it should be documented as deprecated.

Recommended response field (additive, non-breaking):

```json
{
  "warnings": [
    "POST /v1/integrations/lab/publish is deprecated. Use POST /v1/integrations/runs/publish."
  ]
}
```

---

## Publish Run Request

The publish request should be self-contained enough for the platform to register the run and attach related artifacts.

### Top-level shape (target)

```json
{
  "schema_version": "2",
  "producer": {
    "name": "edd-agent-lab",
    "version": "local-dev",
    "environment": "local_demo"
  },
  "agent": {},
  "target": {},
  "eval_contract": {},
  "agent_version": {},
  "scenario_set": {},
  "tool_context": {},
  "run": {},
  "scores": [],
  "trace_links": [],
  "failure_packets": [],
  "fix_plan": null,
  "comparison": null,
  "gate_result": null,
  "promotion_record": null,
  "artifacts": []
}
```

The exact schema may evolve, but the conceptual sections should remain.

**Migration:** v1 envelopes (`schema_version: "1"`) remain valid. The platform maps v1 fields into `ExperimentRun` + `ingest` JSON until HLD domain objects are first-class.

---

## Producer Metadata

```json
{
  "producer": {
    "name": "edd-agent-lab",
    "version": "0.1.0",
    "environment": "local_demo",
    "commit_sha": "optional",
    "run_mode": "mock_local"
  }
}
```

### Required fields

```text
name
environment
run_mode
```

### Notes

The platform should know whether a run came from local demo mode, test mode, internal mode, or production mode.

---

## Agent Identity

```json
{
  "agent": {
    "id": "customer-escalation-triage-agent",
    "name": "Customer Escalation Triage Agent",
    "description": "Helps FDEs triage customer AI deployment escalations."
  }
}
```

### Behavior

If the agent already exists, the platform should update or reuse it.

If it does not exist, the platform may create it.

For MVP, upsert behavior is acceptable.

---

## Target Reference

```json
{
  "target": {
    "id": "customer-escalation-triage-target-v1",
    "agent_id": "customer-escalation-triage-agent",
    "version": "v1",
    "name": "Customer Escalation Triage Target"
  }
}
```

The request may include either:

```text
target reference only
```

or:

```text
full target artifact
```

For MVP, including the full target artifact is acceptable because file-based lab artifacts may be the easiest integration path.

---

## Eval Contract Reference

```json
{
  "eval_contract": {
    "id": "customer-escalation-triage-eval-contract-v1",
    "target_id": "customer-escalation-triage-target-v1",
    "version": "v1",
    "name": "Customer Escalation Triage Eval Contract"
  }
}
```

The platform must associate all scores and gates with the eval contract used at runtime.

Comparisons should not silently compare versions evaluated under different contracts.

**Today:** `eval_spec_id` (UUID) on the v1 envelope links to platform `EvalSpec`.

---

## Agent Version

```json
{
  "agent_version": {
    "id": "v1-evidence-triage-graph",
    "agent_id": "customer-escalation-triage-agent",
    "source_version_id": "v0-baseline",
    "target_id": "customer-escalation-triage-target-v1",
    "eval_contract_id": "customer-escalation-triage-eval-contract-v1",
    "graph_design_id": "customer-escalation-triage-graph-v1",
    "version_label": "v1-evidence-triage-graph",
    "implementation_summary": "Adds evidence collection, evidence normalization, facts/hypotheses/unknowns separation, mitigation planning, and customer-safe update review.",
    "tool_mode_summary": "mock_local"
  }
}
```

The platform should not assume the latest version is active.

Promotion is handled separately by `PromotionRecord`.

---

## Scenario Set

```json
{
  "scenario_set": {
    "id": "escalation-core-scenarios",
    "name": "Escalation Core Scenarios",
    "scenario_ids": [
      "escalation-latency-quality-regression-001"
    ]
  }
}
```

The run should always identify the scenario or scenario set used.

---

## Tool Context

Tool context is required because behavior quality and production readiness are separate.

```json
{
  "tool_context": {
    "tool_mode_summary": "mock_local",
    "tool_bindings": [
      {
        "graph_node": "collect_trace_evidence",
        "requirement_id": "trace_evidence_source",
        "implementation_id": "fetch_trace_summary_mock",
        "mode": "mock",
        "environment": "local_demo"
      },
      {
        "graph_node": "collect_eval_history",
        "requirement_id": "eval_history_source",
        "implementation_id": "fetch_eval_results_local",
        "mode": "local",
        "environment": "local_demo"
      }
    ],
    "tool_feasibility": [
      {
        "requirement_id": "trace_evidence_source",
        "implementation_status": "mock_only",
        "demo_ready": true,
        "production_ready": false,
        "blockers": [
          "Live Langfuse API connector not implemented."
        ]
      }
    ]
  }
}
```

The platform should use this to compute readiness and display warnings.

See [HLD-004](HLD-004-tool-requirements-and-feasibility.md) for tool modeling rules.

---

## Run

```json
{
  "run": {
    "id": "run_v1_001",
    "type": "experiment",
    "status": "completed",
    "started_at": "2026-05-30T10:00:00Z",
    "completed_at": "2026-05-30T10:01:00Z",
    "environment": "local_demo",
    "input_summary": "Customer Apex Health reports inconsistent answers, higher latency, prompt change, eval drop, and tool timeouts.",
    "output_summary": "v1 separates facts, hypotheses, and unknowns and recommends safe next actions.",
    "raw_output": {}
  }
}
```

For MVP, timestamps can be generated by the lab or platform.

---

## Scores

Scores should reference metrics from the eval contract.

```json
{
  "scores": [
    {
      "metric_id": "diagnostic_grounding",
      "scenario_id": "escalation-latency-quality-regression-001",
      "value": 5,
      "scale_min": 0,
      "scale_max": 5,
      "explanation": "The agent separates confirmed facts, hypotheses, and unknowns and avoids claiming a confirmed root cause.",
      "evaluator": "local_evaluator"
    },
    {
      "metric_id": "customer_communication_quality",
      "scenario_id": "escalation-latency-quality-regression-001",
      "value": 5,
      "scale_min": 0,
      "scale_max": 5,
      "explanation": "The customer update is clear, non-speculative, and avoids sensitive internal details.",
      "evaluator": "local_evaluator"
    }
  ]
}
```

The platform should reject or warn on scores that reference unknown metrics.

---

## Trace Links

Trace links connect platform run records to Langfuse evidence.

```json
{
  "trace_links": [
    {
      "provider": "langfuse",
      "external_trace_id": "trace_v1_def456",
      "external_url": "http://localhost:3000/project/example/traces/trace_v1_def456",
      "scenario_id": "escalation-latency-quality-regression-001",
      "agent_version_id": "v1-evidence-triage-graph",
      "metadata": {
        "platform_run_id": "run_v1_001",
        "platform_agent_id": "customer-escalation-triage-agent",
        "platform_agent_version": "v1-evidence-triage-graph",
        "platform_target_id": "customer-escalation-triage-target-v1",
        "platform_eval_contract_id": "customer-escalation-triage-eval-contract-v1",
        "scenario_id": "escalation-latency-quality-regression-001",
        "tool_mode": "mock_local",
        "environment": "local_demo"
      }
    }
  ]
}
```

The platform should store trace references and metadata.

It should not duplicate full Langfuse traces.

---

## Failure Packets

```json
{
  "failure_packets": [
    {
      "id": "fp-v0-unsupported-root-cause",
      "experiment_run_id": "run_v0_001",
      "agent_version_id": "v0-baseline",
      "scenario_id": "escalation-latency-quality-regression-001",
      "failed_behavior_rule_id": "separate_facts_from_hypotheses",
      "severity": "critical",
      "observed_behavior": "The agent stated that the summarization prompt change was the likely cause and recommended telling the customer the issue had been found.",
      "expected_behavior": "The agent should have separated confirmed facts from hypotheses.",
      "suspected_cause": "v0 has no explicit evidence normalization or facts/hypotheses/unknowns step.",
      "recommended_fix": "Add normalize_evidence and separate_facts_hypotheses_unknowns nodes before mitigation planning or customer communication.",
      "trace_link_ids": [
        "trace_v0_abc123"
      ],
      "status": "open"
    }
  ]
}
```

For a v1 publish, failure packets may be empty or may include resolved failure references.

**Today:** v1 envelope uses singular `failure_packet` (JSON blob on ingest).

---

## Fix Plan

```json
{
  "fix_plan": {
    "id": "fix-v1-evidence-first-triage",
    "source_version_id": "v0-baseline",
    "target_version_label": "v1-evidence-triage-graph",
    "failure_packet_ids": [
      "fp-v0-unsupported-root-cause"
    ],
    "behavior_rule_ids_addressed": [
      "evidence_first_diagnosis",
      "separate_facts_from_hypotheses"
    ],
    "graph_changes": [
      "Add collect_evidence node.",
      "Add normalize_evidence node.",
      "Add separate_facts_hypotheses_unknowns node."
    ],
    "prompt_changes": [
      "Require output sections for Facts, Hypotheses, Unknowns, Immediate Actions, Investigation Plan, and Customer Update."
    ],
    "tool_changes": [
      "Add mock trace summary tool.",
      "Add mock recent changes tool.",
      "Add mock tool health tool."
    ],
    "non_goals": [
      "Do not automatically roll back production.",
      "Do not claim production readiness while tools are mock-only."
    ],
    "status": "implemented"
  }
}
```

---

## Comparison

```json
{
  "comparison": {
    "id": "compare-v0-v1-escalation-triage",
    "baseline_version_id": "v0-baseline",
    "candidate_version_id": "v1-evidence-triage-graph",
    "target_id": "customer-escalation-triage-target-v1",
    "eval_contract_id": "customer-escalation-triage-eval-contract-v1",
    "scenario_set_id": "escalation-core-scenarios",
    "score_deltas": {
      "diagnostic_grounding": {
        "v0": 2,
        "v1": 5,
        "delta": 3
      }
    },
    "resolved_failure_packet_ids": [
      "fp-v0-unsupported-root-cause"
    ],
    "new_failure_packet_ids": [],
    "regression_warnings": [
      "v1 has higher latency and token usage because it performs evidence normalization."
    ],
    "summary": "v1 improves because it separates facts, hypotheses, and unknowns instead of overclaiming root cause."
  }
}
```

---

## Gate Result

```json
{
  "gate_result": {
    "agent_version_id": "v1-evidence-triage-graph",
    "comparison_id": "compare-v0-v1-escalation-triage",
    "behavior_gate_status": "pass",
    "tool_readiness_status": "mock_local",
    "production_readiness_status": "blocked",
    "overall_status": "pass_for_demo_not_production",
    "behavior_gates": {
      "no_unsupported_root_cause": "pass",
      "must_separate_facts_and_hypotheses": "pass",
      "must_include_safe_next_actions": "pass",
      "customer_update_must_be_safe": "pass"
    },
    "tool_readiness_gates": {
      "required_tools_available_for_demo": "pass",
      "required_tools_available_for_production": "fail"
    },
    "blockers": [
      "trace_evidence_source uses mock implementation.",
      "recent_changes_source uses mock implementation.",
      "tool_health_source uses mock implementation."
    ]
  }
}
```

**Today:** quality gate service computes `gate_status` / `gate_explanation` from `eval_summary`; structured behavior vs production split is target state.

---

## Promotion Record

```json
{
  "promotion_record": {
    "agent_id": "customer-escalation-triage-agent",
    "agent_version_id": "v1-evidence-triage-graph",
    "previous_version_id": "v0-baseline",
    "decision": "promoted_for_demo",
    "production_status": "blocked",
    "rationale": "v1 resolves the critical v0 failure of unsupported root-cause claims by adding evidence collection, evidence normalization, and facts/hypotheses/unknowns separation.",
    "accepted_risks": [
      "v1 relies on mock/local tools.",
      "v1 should not be used for production escalation triage."
    ]
  }
}
```

---

## Artifacts

Artifacts are file-level evidence published from the lab.

```json
{
  "artifacts": [
    {
      "type": "agent_target",
      "path": "lab-runs/customer_escalation_triage/target/agent-target.yaml",
      "content_hash": "optional"
    },
    {
      "type": "eval_summary",
      "path": "lab-runs/customer_escalation_triage/v1-evidence-triage-graph/eval-summary.json",
      "content_hash": "optional"
    },
    {
      "type": "gate_result",
      "path": "lab-runs/customer_escalation_triage/v1-evidence-triage-graph/gate-result.yaml",
      "content_hash": "optional"
    }
  ]
}
```

For MVP, artifact paths are acceptable. Later, artifact contents or object storage links may be added.

---

## Publish Run Response

The platform should return canonical IDs and readiness status.

```json
{
  "platform_run_id": "platform-run-v1-001",
  "agent_id": "customer-escalation-triage-agent",
  "agent_version_id": "v1-evidence-triage-graph",
  "behavior_status": "pass",
  "tool_status": "mock_local",
  "production_status": "blocked",
  "overall_status": "pass_for_demo_not_production",
  "gate_result_id": "gate-v1-001",
  "comparison_id": "compare-v0-v1-escalation-triage",
  "promotion_record_id": "promotion-v1-demo",
  "artifact_ids": [
    "artifact-001",
    "artifact-002"
  ],
  "warnings": [
    "Production readiness is blocked because required tools are mock/local only."
  ]
}
```

**Today:** response includes `platform_run_id`, `gate_status`, `gate_explanation`, and full `experiment_run` (with ingest provenance).

---

## Idempotency

Publishing should be idempotent.

The lab may retry a publish request.

Recommended strategy:

```text
Use a producer_run_id or idempotency_key.
If the same producer_run_id is published again, update or return the existing platform run.
```

Example:

```json
{
  "run": {
    "id": "run_v1_001",
    "producer_run_id": "edd-agent-lab/customer_escalation_triage/v1-evidence-triage-graph/run_v1_001"
  }
}
```

The platform should avoid creating duplicate runs for the same lab artifact.

---

## Validation Rules

The platform should validate incoming publish payloads.

Minimum validation:

```text
1. agent.id is required.
2. agent_version.id is required.
3. target.id is required.
4. eval_contract.id is required.
5. run.id is required.
6. tool_context.tool_mode_summary is required.
7. scores must reference known or included metric IDs.
8. failure packets must reference known or included behavior rule IDs.
9. comparison must reference included or existing versions.
10. gate result must not mark production ready if required production tools are mock/local/missing.
```

For MVP, validation can be permissive but should warn loudly.

**v1 compatibility:** require `schema_version`, `source`, `run_id`, and either `agent` or `subject_id`; warn when `tool_context` is absent.

---

## Readiness Calculation

The platform should compute or confirm readiness.

### Behavior status

Derived from behavior gates.

```text
pass
fail
warning
not_run
```

### Tool status

Derived from tool feasibility and bindings.

```text
missing
mock_only
local_only
mock_local
read_only_live
approval_gated
production_ready
```

### Production status

Derived from behavior status, tool status, and operational safety gates.

```text
ready
blocked
not_applicable
```

### Overall status

Examples:

```text
fail
pass_for_demo_not_production
pass_for_internal_use
production_ready
```

Important rule:

```text
Behavior pass does not imply production ready.
```

---

## Error Responses

Use clear errors.

### Unknown eval metric

```json
{
  "error": "unknown_metric",
  "message": "Score references metric diagnostic_grounding, but the metric was not found in the eval contract.",
  "field": "scores[0].metric_id"
}
```

### Production readiness conflict

```json
{
  "error": "production_readiness_conflict",
  "message": "Payload marks production readiness as ready, but trace_evidence_source is mock-only.",
  "field": "gate_result.production_readiness_status"
}
```

### Missing tool mode

```json
{
  "error": "missing_tool_mode",
  "message": "tool_context.tool_mode_summary is required for published runs.",
  "field": "tool_context.tool_mode_summary"
}
```

---

## Platform Console Integration

After a run is published, the platform console should be able to show:

```text
Agent
Target
Rules
Eval contract
Information requirements
Tool requirements
Tool feasibility
Version
Run
Scores
Trace links
Failure packets
Fix plan
Comparison
Gate result
Promotion record
Artifacts
```

The key platform console story:

```text
v0 guessed the root cause.
v0 failed separate_facts_from_hypotheses.
v1 added evidence normalization and facts/hypotheses separation.
v1 passed behavior gates.
v1 is promoted for demo.
v1 is blocked for production because required tools are mock/local only.
```

---

## Lab CLI Integration

The lab should expose a publish command.

Example:

```bash
EDD_CLIENT_MODE=http \
EDD_API_BASE_URL=http://127.0.0.1:8000 \
EDD_TENANT_ID=tenant-a \
EDD_EVAL_SPEC_ID=<uuid> \
EDD_API_KEY=<jwt-if-auth-enabled> \
edd-lab publish-run \
  --agent customer-escalation-triage \
  --version v1-evidence-triage-graph
```

The exact command should follow the lab’s existing CLI conventions.

The command should:

```text
1. Load local artifacts for the selected agent/version.
2. Build the publish payload.
3. POST to /v1/integrations/runs/publish.
4. Print platform_run_id and readiness status.
5. Print warnings.
```

Example output:

```text
Published run: platform-run-v1-001
Behavior status: pass
Tool status: mock_local
Production status: blocked
Overall status: pass_for_demo_not_production

Warning:
Production readiness is blocked because trace_evidence_source,
recent_changes_source, and tool_health_source are mock/local only.
```

**Verify today:** `edd-agent-lab/scripts/test_platform_publish.sh`

---

## MVP Scope

For MVP, the platform API may be simple.

Required:

```text
POST /v1/integrations/runs/publish
GET  /v1/runs/{run_id}                    (or GET /v1/experiment-runs/{id} today)
GET  /v1/agents/{agent_id}
GET  /v1/agents/{agent_id}/versions
GET  /v1/comparisons/{comparison_id}
GET  /v1/gate-results/{gate_result_id}
```

Optional:

```text
POST /v1/agents
POST /v1/targets
POST /v1/eval-contracts
POST /v1/promotions
```

If the platform is file-backed for the MVP, the same API shape should still be preserved conceptually.

**Today:** publish + `GET /v1/experiment-runs/{id}/gate` are implemented; agent/comparison/gate-result resource routes are target state (data may live in ingest JSON initially).

---

## Anti-Patterns

### Anti-pattern: Running both repos means integration

Bad:

```text
The startup script runs the platform and the lab, so they are integrated.
```

Good:

```text
The lab publishes run artifacts into the platform through
POST /v1/integrations/runs/publish.
```

### Anti-pattern: Publish scores only

Bad:

```json
{
  "version": "v1",
  "score": 4.4
}
```

Good:

```text
Publish target, eval contract, tool mode, trace links, failure packets,
comparison, gate result, and promotion record.
```

### Anti-pattern: No tool context

Bad:

```text
v1 passed evals, so it is ready.
```

Good:

```text
v1 passed behavior gates but is blocked for production because required tools
are mock/local only.
```

### Anti-pattern: Langfuse as product database

Bad:

```text
Store target, gates, and promotion only as Langfuse metadata.
```

Good:

```text
Store platform objects in the platform and link to Langfuse traces as evidence.
```

---

## Acceptance Criteria for This HLD

Implementation is aligned with this HLD when:

```text
1. The primary publish endpoint is POST /v1/integrations/runs/publish.
2. The old /v1/integrations/lab/publish endpoint is treated as deprecated if present.
3. The publish payload includes agent, target, eval contract, version, scenario, tool context, run, scores, trace links, and artifacts.
4. The publish payload can include failure packets, fix plan, comparison, gate result, and promotion record.
5. Tool mode and active tool bindings are included or summarized.
6. The platform returns canonical run ID and readiness status.
7. The platform distinguishes behavior status from production status.
8. Publishing is idempotent or has an idempotency strategy.
9. Platform console can display the published run in the EDD workflow context.
10. The lab publish command can publish the Customer Escalation Triage v0/v1 artifacts.
```

---

## Summary

The platform API should make the integration real.

The lab does not become integrated with the platform simply because both are running.

Integration means:

```text
The lab publishes a run.
The platform registers it.
The platform links it to target, rules, eval contract, tool context, traces,
failure packets, comparison, gates, and promotion.
The console can tell the full EDD story.
```

The most important endpoint is:

```http
POST /v1/integrations/runs/publish
```

The most important rule is:

```text
Behavior success does not imply production readiness.
```

The API must preserve that distinction.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series |
| [HLD-004](HLD-004-tool-requirements-and-feasibility.md) | eval-driven-design-platform | Tool readiness modeling |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Golden publish payloads |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | Milestone 4 scope |
| [HLD-008](HLD-008-langfuse-integration.md) | eval-driven-design-platform | Trace links and metadata |
| [HLD-009](HLD-009-architecture-and-flow-diagrams.md) | eval-driven-design-platform | Architecture diagrams |
| [HLD-010](HLD-010-graph-design-and-rule-mapping.md) | eval-driven-design-platform | Graph design and rule mapping |
| `docs/05-platform-integration.md` | edd-agent-lab | Publish seam today |
| `scripts/test_platform_publish.sh` | edd-agent-lab | Auth-aware smoke test |
