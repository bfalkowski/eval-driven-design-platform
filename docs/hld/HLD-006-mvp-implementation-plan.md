# HLD-006: MVP Implementation Plan

## Status

Draft

## Purpose

This document defines the MVP implementation plan for the **EDD stack**.

The purpose of this HLD is to give coding agents a scoped, buildable sequence that preserves the product intent without trying to implement the entire ideal state at once.

The MVP should prove the core evaluation-driven design loop:

```text
agent idea
  → target
  → rules
  → eval contract
  → information requirements
  → tool requirements
  → tool feasibility
  → graph design
  → v0
  → trace evidence
  → failure packet
  → bounded fix
  → v1
  → comparison
  → gates
  → promotion
```

The MVP does not need to solve production deployment, live tool connectors, or controlled automation.

It does need to prove that agent improvement is driven by explicit targets, rules, evidence, failures, and bounded fixes.

See also:

- [HLD-003: Evaluation-Driven Design Workflow](HLD-003-evaluation-driven-design-workflow.md)
- [HLD-005: Reference Scenario](HLD-005-reference-scenario-customer-escalation-triage.md)
- [`EVAL_DRIVEN_DESIGN_PLAN.md`](../../EVAL_DRIVEN_DESIGN_PLAN.md) — platform Phases 0–8 (MVP spine done) and post-MVP Phases 9–14

---

## MVP Product Goal

The MVP should demonstrate this story:

```text
A user defines a new agent target.

The platform generates rules, evals, information requirements, tool requirements,
and tool feasibility.

The lab runs a weak v0 baseline.

v0 fails a specific rule.

The platform generates a failure packet and bounded fix plan.

The lab runs v1.

v1 improves against the same eval contract.

The platform applies gates.

v1 is promoted for demo, while production readiness remains blocked because
some required tools are mock/local only.
```

The canonical reference scenario is the **Customer Escalation Triage Agent** from [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md).

---

## Non-Goals

The MVP should not attempt to build everything.

Out of scope:

- Full production connector marketplace
- Full Langfuse replacement
- Automatic production deployment
- Autonomous write actions
- Controlled automation
- Complex auth/tenant model beyond what the platform spine already provides
- Full DB migration strategy for every future object
- Sophisticated prompt/version diffing
- Advanced overfitting detection
- Multi-agent orchestration
- Enterprise-grade permissioning

The MVP should favor a small, coherent vertical slice over a broad, incomplete platform.

---

## Repositories

The MVP spans two repos and one external system.

| System | Role |
|---|---|
| **eval-driven-design-platform** | Canonical workflow objects, platform API, platform console, gates, promotion, Langfuse integration orchestration |
| **edd-agent-lab** | Runnable agents, LangGraph code, mock tools, local runs, artifacts, publish-to-platform |
| **Langfuse** | Trace evidence, spans, generations, scores, cost, latency, annotations |

The platform is the control plane.

The lab is the implementation workshop.

Langfuse is the trace evidence layer.

---

## MVP Architecture

```text
┌───────────────────────────────┐
│ edd-agent-lab                 │
│                               │
│ - LangGraph agents            │
│ - mock tools                  │
│ - local scenarios             │
│ - local eval runner           │
│ - artifact generation         │
│ - publish run client          │
└───────────────┬───────────────┘
                │
                │ POST /v1/integrations/runs/publish
                ▼
┌───────────────────────────────┐
│ eval-driven-design-platform   │
│                               │
│ - target/rule/eval objects    │
│ - information/tool objects    │
│ - run registry                │
│ - failure packets             │
│ - fix plans                   │
│ - comparisons                 │
│ - gates                       │
│ - promotion records           │
│ - platform console            │
└───────────────┬───────────────┘
                │
                │ trace metadata / links
                ▼
┌───────────────────────────────┐
│ Langfuse                      │
│                               │
│ - traces, spans, generations  │
│ - scores, cost/latency/tokens │
└───────────────────────────────┘
```

For the MVP, Langfuse may be partially mocked or linked by placeholder trace IDs if full integration is not yet available. The data model should still preserve `TraceLink`.

---

## Current Progress (snapshot)

Use this table to avoid re-building what already exists.

| Milestone | Status | Notes |
|---|---|---|
| **M1** Documentation | **Done** | HLD-001–006, README/plan links |
| **M2** Domain schemas | **Not started** | EvalSpec/Case/Run exist; HLD objects + example YAML TBD |
| **M3** Lab reference agent | **Not started** | `customer-solution` agent exists; escalation triage per HLD-005 TBD |
| **M4** Publish integration | **Partial** | `POST /v1/integrations/runs/publish`, ingest JSON, smoke script; envelope v2 + structured readiness TBD |
| **M5** Console MVP | **Partial** | Eval-centric console today; lifecycle screens TBD |
| **M6** Demo + validation | **Partial** | `DEMO_SCRIPT.md`, lab CLI smoke; reference-scenario demo script TBD |

---

## MVP Milestones

The MVP should be implemented in six milestones.

```text
M1: Documentation and reference scenario
M2: Platform domain schemas and artifact model
M3: Lab reference agent and local artifacts
M4: Run publish integration
M5: Platform console MVP
M6: End-to-end demo script and validation
```

These map to [`EVAL_DRIVEN_DESIGN_PLAN.md`](../../EVAL_DRIVEN_DESIGN_PLAN.md) post-MVP Phases 9–14.

---

## Milestone 1: Documentation and Reference Scenario

### Goal

Add the HLD docs and canonical reference scenario so all coding agents have a stable design target.

### Repo

**eval-driven-design-platform** (+ cross-links in **edd-agent-lab** README)

### Deliverables

```text
docs/hld/HLD-001-product-intent-and-system-boundaries.md
docs/hld/HLD-002-domain-object-model.md
docs/hld/HLD-003-evaluation-driven-design-workflow.md
docs/hld/HLD-004-tool-requirements-and-feasibility.md
docs/hld/HLD-005-reference-scenario-customer-escalation-triage.md
docs/hld/HLD-006-mvp-implementation-plan.md
```

### Acceptance criteria

1. HLD docs exist under `docs/hld/`.
2. README and plan link to the HLD pack.
3. HLD docs use **EDD stack**, **eval-driven-design-platform**, **edd-agent-lab** naming (no unresolved codenames).
4. HLD-005 includes the full Customer Escalation Triage reference scenario.

**Status: complete.**

---

## Milestone 2: Platform Domain Schemas and Artifact Model

### Goal

Create structured schemas for the MVP domain objects.

The first implementation can use JSON/YAML/Pydantic models before full database persistence.

### Repo

**eval-driven-design-platform**

### MVP objects

Implement schemas for the full HLD-002 set, or this **minimum first pass**:

```text
Agent
AgentTarget
BehaviorRule
EvalContract
InformationRequirement
ToolRequirement
ToolFeasibilityReview
GraphDesign
AgentVersion
ExperimentRun
TraceLink
Score
FailurePacket
FixPlan
Comparison
GateResult
PromotionRecord
ReadinessStatus
```

Map existing types where practical:

| Today | Target |
|---|---|
| `EvalSpec` | early `EvalContract` |
| `EvalCase` | `Scenario` |
| `ExperimentRun` + `ingest` JSON | normalized run + linked objects |

### Suggested package structure

Follow the repo’s existing layout (`api/app/domain/models.py` today). Extend rather than rewrite. Example target layout:

```text
api/app/domain/
  models.py              # extend incrementally
  edd/                   # optional package for HLD objects
    agent.py
    target.py
    ...
examples/customer_escalation_triage/
  agent-target.yaml
  behavior-rules.yaml
  eval-contract.yaml
  information-requirements.yaml
  tool-requirements.yaml
  tool-feasibility.yaml
  tool-bindings.yaml
  graph-design.yaml
```

### Acceptance criteria

1. Domain schemas represent the MVP objects.
2. `ToolRequirement`, `ToolImplementation`, `ToolBinding`, and `ToolFeasibilityReview` are distinct.
3. `InformationRequirement` exists separately from `ToolRequirement`.
4. Example artifacts validate against schemas.
5. Customer Escalation Triage artifacts match HLD-005.
6. No code treats a suggested tool as automatically implemented.

---

## Milestone 3: Lab Reference Agent and Local Artifacts

### Goal

Add the Customer Escalation Triage Agent to **edd-agent-lab**.

The lab should run v0 and v1 locally using mock/local tools.

### Repo

**edd-agent-lab**

### Deliverables

Add a new reference agent **without** deleting the existing Customer Solution Discovery agent.

```text
data/mock/customer_escalation_triage/apex_health/
  customer_report.json
  langfuse_trace_summary.json
  eval_results.json
  recent_changes.json
  tool_health.json
  customer_context.json

lab-runs/customer_escalation_triage/
  target/          # design artifacts
  v0-baseline/
  v1-evidence-triage-graph/
```

See [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) for full artifact shapes.

### v0 behavior

Intentionally weak: single-pass prompt, no tool bindings, no facts/hypotheses separation.

Expected failure: overclaims prompt change as root cause; tells customer the issue was found.

### v1 behavior

Evidence-first graph: collect → normalize → correlate → separate facts/hypotheses/unknowns → impact → mitigation → customer update review.

### Mock tools

```text
fetch_customer_report_from_scenario
fetch_trace_summary_mock
fetch_eval_results_local
fetch_recent_changes_mock
fetch_tool_health_mock
fetch_customer_context_from_scenario
```

### Acceptance criteria

1. Lab runs `v0-baseline` for the reference scenario.
2. v0 produces expected failure behavior and eval summary with failed gates.
3. v0 failure packet references `separate_facts_from_hypotheses`.
4. Lab runs `v1-evidence-triage-graph` with facts/hypotheses/unknowns output.
5. v1 gate result is `pass_for_demo_not_production`; tool readiness mock/local.
6. Existing `customer-solution` agent and CI smoke remain working.

---

## Milestone 4: Run Publish Integration

### Goal

Lab publishes run artifacts to the platform with enough structure to tell the reference story.

**Canonical contract:** [HLD-007: Platform API and integration](HLD-007-platform-api-and-integration.md) (envelope v2, readiness response, idempotency, validation).

### Repos

**eval-driven-design-platform** + **edd-agent-lab**

### Primary endpoint

```http
POST /v1/integrations/runs/publish
```

### Deprecated alias

```http
POST /v1/integrations/lab/publish
```

Document as deprecated; new code uses `/v1/integrations/runs/publish`.

### Target request payload (envelope v2)

Extend today’s publish envelope. Target shape:

```json
{
  "schema_version": "2",
  "source": "edd-agent-lab",
  "run_id": "run_v1_001",
  "agent_id": "customer-escalation-triage-agent",
  "agent_version_id": "v1-evidence-triage-graph",
  "target_id": "customer-escalation-triage-target-v1",
  "eval_contract_id": "customer-escalation-triage-eval-contract-v1",
  "scenario_set_id": "escalation-core-scenarios",
  "environment": "local_demo",
  "tool_mode_summary": "mock_local",
  "tool_bindings": [
    {
      "graph_node": "collect_trace_evidence",
      "requirement_id": "trace_evidence_source",
      "implementation_id": "fetch_trace_summary_mock",
      "mode": "mock"
    }
  ],
  "eval_summary": {},
  "failure_packets": [],
  "fix_plan": {},
  "comparison": {},
  "gate_result": {},
  "promotion_record": {},
  "trace_links": [],
  "artifacts": []
}
```

**Today:** v1 envelope with `eval_summary`, `failure_packet`, ingest metadata — see [HLD-007](HLD-007-platform-api-and-integration.md) and edd-agent-lab `docs/05-platform-integration.md`.

### Target response payload

```json
{
  "platform_run_id": "run_v1_001",
  "behavior_status": "pass",
  "tool_status": "mock_local",
  "production_status": "blocked",
  "promotion_status": "promoted_for_demo",
  "gate_result_id": "gate_v1_001",
  "comparison_id": "compare_v0_v1_escalation_triage"
}
```

### Lab CLI

```bash
EDD_CLIENT_MODE=http \
EDD_API_BASE_URL=http://127.0.0.1:8000 \
EDD_TENANT_ID=tenant-a \
EDD_EVAL_SPEC_ID=<uuid> \
EDD_API_KEY=<jwt-if-auth-enabled> \
edd-lab publish-run --agent customer-escalation-triage --version v1-evidence-triage-graph
```

Adjust flags to match existing lab CLI conventions.

### Acceptance criteria

1. Platform exposes `POST /v1/integrations/runs/publish`.
2. Lab publishes v0 and v1 reference runs.
3. Published runs preserve target, eval contract, version, scenario, and tool mode.
4. Platform stores or displays failure packets, comparison, gate result, and promotion record.
5. Response includes readiness status (behavior vs production).
6. Deprecated alias documented if still implemented.
7. Data flows lab → platform (not just two repos running side by side).

**Partial today:** basic ingest + gate API; structured v2 fields and readiness in response TBD.

---

## Milestone 5: Platform Console MVP

### Goal

Platform console tells the Customer Escalation Triage reference story.

### Repo

**eval-driven-design-platform**

### Required screens

```text
Overview
Target
Rules
Eval Contract
Information Requirements
Tool Requirements
Tool Feasibility
Graph Design
Runs
Failure Packets
Fix Plans
Compare Versions
Gates
Promotion
Artifacts
```

A single-page Streamlit app with sections is acceptable for MVP if full nav is too much.

### Required console story

```text
v0 guessed the root cause.
v0 failed separate_facts_from_hypotheses.
The failure packet identified the missing facts/hypotheses/unknowns step.
The fix plan added evidence collection and evidence normalization.
v1 separated facts, hypotheses, and unknowns.
v1 passed behavior gates.
v1 is promoted for demo.
v1 is blocked for production because required tools are mock/local only.
```

### Required status cards

- Behavior Gate: PASS / FAIL
- Tool Readiness: MISSING / MOCK_ONLY / LOCAL / LIVE
- Production Readiness: READY / BLOCKED
- Promotion Status: DRAFT / PROMOTED_FOR_DEMO / REJECTED / etc.

### MVP actions (read-only OK)

- Load reference scenario
- View v0 / v1
- Compare v0/v1
- View failure packet, fix plan, gate result, promotion record

### Acceptance criteria

1. Console loads Customer Escalation Triage reference scenario.
2. Shows target, rules, eval contract, information/tool requirements, feasibility.
3. Mock/local tool readiness visible.
4. Shows v0 failure and v1 improvement.
5. Shows `pass_for_demo_not_production`.
6. Does not imply production readiness.
7. Tells the full story without raw file inspection.

**Partial today:** EvalSpec/Case/Runs/Quality Gates pages; lifecycle screens TBD.

---

## Milestone 6: End-to-End Demo Script and Validation

### Goal

Repeatable demo and validation scripts prove the MVP.

### Repos

**eval-driven-design-platform** + **edd-agent-lab**

### Demo sequence

1. Start platform (`./scripts/local_e2e.sh`)
2. Start lab console or CLI as needed
3. Open platform console (`:8501`)
4. Load Customer Escalation Triage Agent
5. Review target, rules, eval contract, information requirements, tool feasibility
6. Run or load v0-baseline
7. Show v0 failure packet
8. Show v1 fix plan
9. Run or load v1-evidence-triage-graph
10. Publish v1 run to platform (`:8000`)
11. Compare v0 and v1
12. Show gate result
13. Show `promoted_for_demo`
14. Show production blocked (mock/local tools)

### Suggested scripts

**Platform / combined:**

```bash
scripts/demo_customer_escalation_triage.sh
scripts/validate_reference_scenario.sh
```

**Lab (extend existing):**

```bash
scripts/test_platform_publish.sh   # auth-aware smoke today
```

Validation should verify reference artifacts exist and `production_readiness` is blocked.

### Acceptance criteria

1. Demo runs from clean checkout with documented commands.
2. Demo shows complete target-to-promotion flow.
3. Validation script passes.
4. README includes demo instructions.
5. No live external tools required.
6. Mock/local tool usage explicit.
7. Platform run IDs visible.

---

## Suggested Implementation Order

```text
1. HLD docs                          (done)
2. Reference scenario example YAML   (M2)
3. Schema validation for artifacts   (M2)
4. Lab mock data and mock tools      (M3)
5. v0/v1 local run artifacts         (M3)
6. Publish envelope v2 + readiness   (M4)
7. Lab publish client updates        (M4)
8. Platform console sections         (M5)
9. Demo script                       (M6)
10. Validation script + cross-repo CI (M6 / Phase 9)
```

Do not start the console before artifacts and domain model exist.

---

## Cursor / Codex Guardrails

Coding agents should:

- Not rewrite the whole repo from scratch.
- Not remove existing working demos unless necessary.
- Not collapse domain objects (`ToolRequirement` ≠ `ToolImplementation`).
- Not treat suggested tools as implemented tools.
- Not use unresolved product codenames.
- Not mark mock-tool runs as production-ready.
- Not make Langfuse the source of truth for targets, gates, or promotion.
- Not silently change the eval contract between v0 and v1.

Prefer:

- Customer Escalation Triage as the canonical vertical slice.
- Readable artifacts over complex infrastructure.
- Visible mock/local/live tool mode.
- Honest demo narrative.
- End-to-end EDD loop preservation.

---

## MVP Acceptance Criteria

The MVP is complete when:

1. User can inspect an `AgentTarget` for Customer Escalation Triage.
2. Platform shows `BehaviorRule`s from that target.
3. Platform shows `EvalContract` with metrics and gates.
4. Platform shows `InformationRequirement`s and `ToolRequirement`s.
5. Platform shows `ToolFeasibilityReview` with mock/local production blockers.
6. Lab runs or loads v0-baseline; v0 overclaims root cause.
7. Platform shows `FailurePacket` for `separate_facts_from_hypotheses`.
8. Platform shows `FixPlan` for evidence normalization + facts/hypotheses separation.
9. Lab runs or loads v1-evidence-triage-graph; v1 improves on same contract.
10. Platform shows v0/v1 `Comparison`.
11. Platform shows `GateResult`: behavior pass, production blocked.
12. Platform records `PromotionRecord` as `promoted_for_demo`.
13. Console tells the full story clearly.

---

## Final Demo Narrative

```text
We defined a Customer Escalation Triage Agent.

The platform generated behavior rules, an eval contract, information requirements,
and tool requirements.

It also showed that several required tools are mock/local only.

v0 was a simple prompt agent. It failed because it guessed the root cause.

The failure packet identified the violated rule: separate_facts_from_hypotheses.

The fix plan added an evidence-first graph with facts, hypotheses, and unknowns.

v1 passed the behavior gates.

But the platform did not mark it production-ready because trace, recent-change,
and tool-health tools are mock/local.

So v1 is promoted for demo, not production.
```

---

## Summary

The MVP should prove one thing clearly:

> The EDD stack can turn agent intent into rules, evals, information needs, tool requirements, graph design, trace-backed failures, bounded fixes, version comparison, gates, and honest promotion decisions.

It should not try to be a complete enterprise platform yet.

The first milestone is a credible vertical slice.

If the Customer Escalation Triage Agent works end to end, the foundation is sound.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Golden payloads |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Publish API contract |
| [HLD-008](HLD-008-langfuse-integration.md) | eval-driven-design-platform | Langfuse trace evidence |
| [HLD-009](HLD-009-architecture-and-flow-diagrams.md) | eval-driven-design-platform | Architecture diagrams |
| [HLD-010](HLD-010-graph-design-and-rule-mapping.md) | eval-driven-design-platform | Graph design and rule mapping |
| [`EVAL_DRIVEN_DESIGN_PLAN.md`](../../EVAL_DRIVEN_DESIGN_PLAN.md) | eval-driven-design-platform | Phases 9–14 mapping |
| `docs/DEMO_SCRIPT.md` | eval-driven-design-platform | Current platform demo |
| `docs/05-platform-integration.md` | edd-agent-lab | Publish seam today |
