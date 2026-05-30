# HLD-008: Langfuse Integration

## Status

Draft

## Purpose

This document defines how the **EDD stack** integrates with Langfuse.

The purpose of this HLD is to make Langfuse’s role clear:

- **Langfuse is the trace evidence layer.**
- **Langfuse is not the source of truth for the EDD workflow.**

The platform should use Langfuse to store and inspect runtime evidence such as traces, spans, generations, tool calls, scores, token usage, cost, and latency.

The platform should not rely on Langfuse to own agent targets, behavior rules, eval contracts, tool feasibility, gates, fix plans, promotion records, or readiness decisions.

See also:

- [HLD-001: Product intent and system boundaries](HLD-001-product-intent-and-system-boundaries.md)
- [HLD-002: Domain object model](HLD-002-domain-object-model.md) — `TraceLink`, `Score`
- [HLD-007: Platform API and integration](HLD-007-platform-api-and-integration.md) — publish `trace_links`
- [`integrations/langfuse_client.py`](../../api/app/integrations/langfuse_client.py) — sole Langfuse API seam today

---

## Core Principle

**The platform owns meaning.**

**Langfuse owns evidence.**

```text
eval-driven-design-platform
  owns:
    - AgentTarget
    - BehaviorRule
    - EvalContract
    - InformationRequirement
    - ToolRequirement
    - ToolFeasibilityReview
    - GraphDesign
    - AgentVersion
    - ExperimentRun
    - FailurePacket
    - FixPlan
    - Comparison
    - GateResult
    - PromotionRecord
    - ReadinessStatus

Langfuse
  owns:
    - traces
    - spans
    - generations
    - model inputs
    - model outputs
    - tool calls
    - cost
    - latency
    - tokens
    - trace-level scores
    - annotations
    - datasets
    - experiments
```

Langfuse evidence should support platform decisions.

It should not replace platform decisions.

---

## Integration Goals

The Langfuse integration should support the following goals:

1. Trace agent runs from **edd-agent-lab**.
2. Attach platform IDs to every trace.
3. Link platform runs to Langfuse traces.
4. Attach scores to traces where useful.
5. Support debugging of failed rules.
6. Support failure packet evidence.
7. Support version comparison evidence.
8. Support cost, latency, and token reporting.
9. Support future human annotation workflows.

The key product story is:

```text
The platform says v0 failed because it overclaimed root cause.
Langfuse shows the exact input, model output, graph path, and tool context
that support that failure packet.
```

---

## Current Implementation (snapshot)

| Area | Today | Target (this HLD) |
|---|---|---|
| **Langfuse API access** | `LangfuseClientAdapter` in `integrations/langfuse_client.py` only | Same constraint |
| **Health / import** | `GET /v1/integrations/langfuse/health`, trace import → EvalCase | Same + publish `trace_links` |
| **Trace IDs on cases/runs** | `langfuse_trace_id` on EvalCase / EvaluationResult | First-class `TraceLink` objects |
| **Scores** | Platform score push to Langfuse on result creation | Platform `Score` canonical; Langfuse trace score linked by metadata |
| **Publish payload** | v1 envelope; trace links TBD | `trace_links[]` on publish (HLD-007) |
| **Platform metadata** | Partial / ad hoc | Required `platform_*` fields on every trace link |
| **Integration level** | Level 0–1 (optional Langfuse in local_e2e; import + score push) | Level 2 preferred for reference agent graph spans |

Do not add Langfuse SDK/API calls outside `integrations/langfuse_client.py`.

---

## What Langfuse Should Store

Langfuse should store runtime evidence.

Examples:

- User input
- System prompt
- Node prompt
- Model input / output
- Tool calls and responses
- Graph path
- Span timing
- Token usage, cost, latency
- Evaluator score and explanation
- Annotations

For the Customer Escalation Triage Agent, Langfuse should help answer:

- What exact prompt caused v0 to overclaim root cause?
- Which model response made the unsupported claim?
- Which graph nodes ran in v1?
- Which mock tools were called?
- How much latency did evidence collection add?
- What score did the evaluator attach to the trace?

See [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) for reference trace shapes.

---

## What Langfuse Should Not Own

Langfuse should not be the canonical owner of:

```text
AgentTarget
BehaviorRule
EvalContract
InformationRequirement
ToolRequirement
ToolFeasibilityReview
GraphDesign
AgentVersion
FailurePacket
FixPlan
Comparison
GateResult
PromotionRecord
ReadinessStatus
```

Langfuse may store platform IDs as metadata.

It should not be the only place where those objects exist.

| Bad | Good |
|---|---|
| Store the eval contract only as trace metadata | Store canonical eval contract and gate result in the platform |
| Infer promotion from the latest successful Langfuse score | Record `PromotionRecord` on the platform |
| Treat Langfuse scores as the complete gate result | Use Langfuse scores as evidence; platform computes `GateResult` |

---

## Platform Metadata on Langfuse Traces

Every trace created by or linked to the EDD stack should include platform metadata.

### Required fields

```json
{
  "platform_run_id": "run_v1_001",
  "platform_agent_id": "customer-escalation-triage-agent",
  "platform_agent_version": "v1-evidence-triage-graph",
  "platform_target_id": "customer-escalation-triage-target-v1",
  "platform_eval_contract_id": "customer-escalation-triage-eval-contract-v1",
  "scenario_id": "escalation-latency-quality-regression-001",
  "tool_mode": "mock_local",
  "environment": "local_demo"
}
```

### Optional fields

```json
{
  "platform_comparison_id": "compare-v0-v1-escalation-triage",
  "platform_gate_result_id": "gate-v1-001",
  "platform_promotion_record_id": "promotion-v1-demo",
  "source_repo": "edd-agent-lab",
  "source_commit": "abc123",
  "producer_run_id": "edd-agent-lab/customer_escalation_triage/v1/run_v1_001"
}
```

The metadata prefix should be `platform_*`, not a product codename.

This keeps metadata stable even if the product name changes.

---

## Trace Link Object

The platform should represent Langfuse references using `TraceLink`.

Example:

```yaml
trace_link:
  id: trace-link-v1-001
  provider: langfuse
  external_trace_id: trace_v1_def456
  external_url: http://localhost:3000/project/example/traces/trace_v1_def456
  experiment_run_id: run_v1_001
  scenario_id: escalation-latency-quality-regression-001
  agent_version_id: v1-evidence-triage-graph
  metadata:
    platform_run_id: run_v1_001
    platform_agent_id: customer-escalation-triage-agent
    platform_agent_version: v1-evidence-triage-graph
    platform_target_id: customer-escalation-triage-target-v1
    platform_eval_contract_id: customer-escalation-triage-eval-contract-v1
    scenario_id: escalation-latency-quality-regression-001
    tool_mode: mock_local
    environment: local_demo
```

The platform should store references and metadata.

It should not duplicate the entire trace payload unless needed for caching or export.

---

## Trace Hierarchy

For graph-based agents, the trace should reflect the graph execution.

Recommended hierarchy:

```text
Trace: ExperimentRun / Scenario / AgentVersion
  Span: parse_escalation_report
  Span: collect_evidence
    Span/Observation: fetch_customer_report
    Span/Observation: fetch_trace_summary
    Span/Observation: fetch_eval_results
    Span/Observation: fetch_recent_changes
    Span/Observation: fetch_tool_health
    Span/Observation: fetch_customer_context
  Span: normalize_evidence
  Span: identify_correlations
  Span: separate_facts_hypotheses_unknowns
  Span: assess_customer_impact
  Span: recommend_mitigation_plan
  Span: draft_customer_update
  Span: customer_safe_update_review
  Span: final_response
```

This hierarchy lets the platform and developers inspect:

- Which graph path ran?
- Which tools were called?
- Which model calls produced the final answer?
- Which node likely caused a failed rule?

---

## v0 Trace Shape

v0 may be a simple prompt-only agent.

Trace shape:

```text
Trace: v0-baseline / escalation-latency-quality-regression-001
  Span: single_pass_response
    Generation: model call
```

Expected v0 evidence:

- The model output claims the summarization prompt change is the likely cause.
- The model recommends telling the customer the issue has been found.
- No evidence normalization node exists.
- No facts/hypotheses/unknowns separation exists.

This trace supports the v0 failure packet.

---

## v1 Trace Shape

v1 should show an evidence-first graph.

Trace shape:

```text
Trace: v1-evidence-triage-graph / escalation-latency-quality-regression-001
  Span: parse_escalation_report
  Span: collect_evidence
    Tool: fetch_customer_report_from_scenario
    Tool: fetch_trace_summary_mock
    Tool: fetch_eval_results_local
    Tool: fetch_recent_changes_mock
    Tool: fetch_tool_health_mock
    Tool: fetch_customer_context_from_scenario
  Span: normalize_evidence
  Span: identify_correlations
  Span: separate_facts_hypotheses_unknowns
  Span: assess_customer_impact
  Span: recommend_mitigation_plan
  Span: draft_customer_update
  Span: customer_safe_update_review
  Span: final_response
```

Expected v1 evidence:

- The graph explicitly collected evidence.
- The graph separated confirmed facts, hypotheses, and unknowns.
- The final response avoided claiming a confirmed root cause.
- The customer update avoided sensitive trace details and speculation.

This trace supports the v1 gate result and comparison.

---

## Scores in Langfuse

Scores may exist in both the platform and Langfuse.

The platform should own normalized scoring results tied to the active `EvalContract`.

Langfuse may store trace-level or span-level scores for observability.

Recommended approach:

| Layer | Role |
|---|---|
| **Platform Score** | Canonical score tied to `Metric`, `EvalContract`, `ExperimentRun`, `Scenario`, and `AgentVersion` |
| **Langfuse Score** | Trace-level or observation score for quick inspection and filtering |

The two should be linked by metadata.

Example platform score:

```yaml
score:
  metric_id: diagnostic_grounding
  experiment_run_id: run_v1_001
  scenario_id: escalation-latency-quality-regression-001
  trace_link_id: trace-link-v1-001
  value: 5
  scale_min: 0
  scale_max: 5
  explanation: >
    The agent separates confirmed facts, hypotheses, and unknowns and avoids
    claiming a confirmed root cause.
```

Example Langfuse score metadata:

```json
{
  "platform_metric_id": "diagnostic_grounding",
  "platform_eval_contract_id": "customer-escalation-triage-eval-contract-v1",
  "platform_score_id": "score-v1-diagnostic-grounding",
  "scenario_id": "escalation-latency-quality-regression-001"
}
```

**Today:** `EvaluationResult` stores `langfuse_trace_id` and `langfuse_score_id` after score push.

---

## Failure Packet Evidence

Failure packets should reference Langfuse evidence through `TraceLink`.

Example:

```yaml
failure_packet:
  id: fp-v0-unsupported-root-cause
  failed_behavior_rule_id: separate_facts_from_hypotheses
  observed_behavior: >
    The agent stated that the summarization prompt change was the likely cause
    and recommended telling the customer the issue had been found.
  trace_link_ids:
    - trace-link-v0-001
```

The platform console should allow the user to open the linked trace in Langfuse.

Expected console behavior:

```text
Failure Packet → Open Trace → Langfuse trace showing exact v0 output
```

The trace is evidence for the failure packet.

The failure packet remains a platform object.

---

## Comparison Evidence

Comparisons should also link to traces.

Example:

```yaml
comparison:
  id: compare-v0-v1-escalation-triage
  baseline_version_id: v0-baseline
  candidate_version_id: v1-evidence-triage-graph
  trace_links:
    baseline:
      - trace-link-v0-001
    candidate:
      - trace-link-v1-001
```

The platform console should show:

- **v0 trace:** single-pass model call that overclaimed root cause
- **v1 trace:** evidence-first graph path with facts/hypotheses separation

This lets a developer verify that the improvement was real.

---

## Gate Evidence

Gate results should reference traces and scores.

Example:

```yaml
gate_result:
  id: gate-v1-001
  agent_version_id: v1-evidence-triage-graph
  behavior_gate_status: pass
  tool_readiness_status: mock_local
  production_readiness_status: blocked
  trace_link_ids:
    - trace-link-v1-001
  evidence: >
    Diagnostic grounding improved to 5/5. The v1 trace shows explicit evidence
    collection and facts/hypotheses/unknowns separation. Production readiness
    remains blocked because trace and tool-health tools are mock/local only.
```

The platform should not rely on Langfuse alone to decide gate status.

Langfuse provides the evidence.

The platform computes or records the gate decision.

---

## Tool Mode Metadata

Tool mode must be visible in Langfuse traces.

Example:

```json
{
  "tool_mode": "mock_local",
  "tool_bindings": [
    {
      "graph_node": "collect_trace_evidence",
      "requirement_id": "trace_evidence_source",
      "implementation_id": "fetch_trace_summary_mock",
      "mode": "mock"
    },
    {
      "graph_node": "collect_eval_history",
      "requirement_id": "eval_history_source",
      "implementation_id": "fetch_eval_results_local",
      "mode": "local"
    }
  ]
}
```

This prevents trace evidence from appearing more production-ready than it is.

The platform console should show this same readiness status.

See [HLD-004](HLD-004-tool-requirements-and-feasibility.md).

---

## Environment Metadata

Every trace should identify its environment.

Recommended values:

```text
local_demo
test
internal
production
```

Examples:

```json
{
  "environment": "local_demo",
  "tool_mode": "mock_local"
}
```

```json
{
  "environment": "internal",
  "tool_mode": "read_only_live"
}
```

Environment and tool mode should be used in readiness decisions.

---

## Langfuse Project Strategy

For MVP, the simplest approach is acceptable.

Possible strategies:

| Strategy | Description |
|---|---|
| **Single Langfuse project** | All local demo traces in one project; filter by platform metadata |
| **Per-agent project** | Each agent has its own Langfuse project |
| **Per-environment project** | `local_demo`, `internal`, and `production` use separate projects |

**Recommended MVP:** one Langfuse project for local demo; rely on platform metadata for filtering.

Later, environment-specific projects may be introduced.

---

## Integration Modes

The MVP may support multiple levels of Langfuse integration.

| Level | Description |
|---|---|
| **0 — Placeholder trace links** | No live Langfuse write; `TraceLink` with placeholder `external_trace_id` |
| **1 — Basic trace creation** | Lab creates Langfuse traces for v0/v1; platform stores `TraceLink` |
| **2 — Graph node spans** | Each graph node emits spans; tool calls and generations visible |
| **3 — Scores and annotations** | Evaluator scores on traces; human annotations linked or imported |
| **4 — Dataset and experiment integration** | Scenario sets map to Langfuse datasets/experiments; platform still owns contract and gates |

**Recommended MVP target:** Level 0 or Level 1 acceptable; Level 2 preferred if straightforward.

The domain model should not depend on full Langfuse integration being available on day one.

---

## Lab Responsibilities

The lab should:

1. Create or receive platform run IDs where available.
2. Emit traces to Langfuse or create trace placeholders.
3. Attach platform metadata to traces.
4. Include trace links in publish payloads.
5. Preserve tool mode and environment metadata.

For local demo mode, the lab may emit mock trace links if Langfuse is not available.

**Rule:** The lab should not send traces directly to Langfuse for production workflows without going through the platform integration model. See edd-agent-lab `docs/05-platform-integration.md`.

---

## Platform Responsibilities

The platform should:

1. Store `TraceLink` objects.
2. Associate `TraceLink`s with `ExperimentRun`s, scenarios, versions, scores, failure packets, comparisons, and gate results.
3. Display trace links in the platform console.
4. Preserve platform metadata for trace filtering.
5. Avoid making Langfuse the canonical workflow database.

The platform may orchestrate Langfuse integration later, but the MVP can accept trace links published from the lab.

All Langfuse HTTP/API access goes through `integrations/langfuse_client.py`.

---

## API Implications

The publish endpoint must support trace links.

```http
POST /v1/integrations/runs/publish
```

Payload section:

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

The platform response may include stored trace link IDs:

```json
{
  "platform_run_id": "platform-run-v1-001",
  "trace_link_ids": [
    "trace-link-v1-001"
  ]
}
```

See [HLD-007](HLD-007-platform-api-and-integration.md) for the full publish contract.

---

## Console Requirements

The platform console should show Langfuse trace links in:

```text
Runs
Scores
Failure Packets
Comparisons
Gate Results
Operational Runs
```

For each trace link, the console should show:

- provider
- scenario
- agent version
- tool mode
- environment
- open in Langfuse

Example:

```text
Trace: trace_v1_def456
Scenario: escalation-latency-quality-regression-001
Version: v1-evidence-triage-graph
Tool mode: mock_local
Environment: local_demo
Open in Langfuse
```

The console should never imply a trace came from production if the environment is `local_demo` or mock mode.

---

## Operational Run Requirements

When a promoted agent is used operationally, the same trace principles apply.

Operational run trace metadata should include:

```json
{
  "platform_operational_run_id": "op_run_001",
  "platform_agent_id": "customer-escalation-triage-agent",
  "platform_agent_version": "v1-evidence-triage-graph",
  "platform_promotion_record_id": "promotion-v1-demo",
  "platform_target_id": "customer-escalation-triage-target-v1",
  "platform_eval_contract_id": "customer-escalation-triage-eval-contract-v1",
  "tool_mode": "mock_local",
  "environment": "local_demo"
}
```

If a version is promoted only for demo, the console should warn users during operational runs.

---

## Security and Privacy Notes

Trace data may contain sensitive information.

The platform should avoid copying full trace payloads unless necessary.

Important considerations:

- Do not expose sensitive trace details in customer-facing outputs.
- Do not store secrets in trace metadata.
- Do not attach raw PHI/PII as platform metadata.
- Do not assume all users can access all Langfuse traces.
- Keep customer-safe summaries separate from internal trace evidence.
- Do not log prompt, answer, or rubric content in metrics or OTel span attributes by default (platform constraint).

For the MVP, use mock data to avoid real customer or sensitive data.

---

## Anti-Patterns

### Anti-pattern: Langfuse as source of truth

| Bad | Good |
|---|---|
| Store target, gates, and promotion only in Langfuse metadata | Store target, gates, and promotion in the platform; attach platform IDs to Langfuse traces |

### Anti-pattern: Trace without platform IDs

Bad:

```json
{
  "trace_name": "v1 run"
}
```

Good:

```json
{
  "platform_run_id": "run_v1_001",
  "platform_agent_version": "v1-evidence-triage-graph",
  "platform_eval_contract_id": "customer-escalation-triage-eval-contract-v1"
}
```

### Anti-pattern: Scores with no eval contract

| Bad | Good |
|---|---|
| Trace score: 5 | Score `diagnostic_grounding` = 5 under `customer-escalation-triage-eval-contract-v1` |

### Anti-pattern: Production-looking trace from mock run

| Bad | Good |
|---|---|
| Trace shows successful run, but tool mode is hidden | Trace metadata includes `tool_mode=mock_local` and `environment=local_demo` |

---

## MVP Requirements

The MVP should support at least:

1. `TraceLink` domain object.
2. Trace links in publish payload.
3. Platform metadata fields on trace links.
4. Console display of trace links.
5. Tool mode and environment visible next to traces.
6. Failure packets can reference `TraceLink`s.
7. Comparisons can reference `TraceLink`s.
8. Gate results can reference `TraceLink`s.

Live Langfuse integration is useful but not required for the first proof.

If Langfuse is not running, placeholder trace links are acceptable for the MVP as long as the integration model is preserved.

---

## Acceptance Criteria for This HLD

Implementation is aligned with this HLD when:

1. Langfuse is treated as the trace evidence layer, not the workflow source of truth.
2. `TraceLink` objects exist in the platform model.
3. Every trace link includes platform metadata.
4. Metadata fields use the `platform_*` prefix, not a product codename.
5. Trace links can be associated with runs, scenarios, versions, scores, failure packets, comparisons, and gates.
6. Tool mode and environment are visible in trace metadata.
7. The platform console links from failure packets and comparisons to Langfuse traces.
8. Scores are tied to eval contract metrics, not free-floating trace scores.
9. The system can operate with placeholder trace links if Langfuse is unavailable.
10. Production readiness is not inferred from trace success alone.

---

## Summary

Langfuse gives the EDD stack trace evidence.

The platform gives that evidence meaning.

The intended relationship is:

```text
Platform:
  v0 failed separate_facts_from_hypotheses.
  v1 passed diagnostic_grounding.
  v1 is promoted for demo.
  v1 is blocked for production.

Langfuse:
  Here is the exact v0 model output that overclaimed root cause.
  Here is the v1 graph path showing evidence collection and facts/hypotheses separation.
  Here are the tool calls, latency, cost, tokens, and evaluator scores.
```

The product is strongest when both systems do what they are good at.

Langfuse should make the evidence inspectable.

The platform should make the design decision traceable.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Reference trace fixtures |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Publish `trace_links` |
| `docs/05-platform-integration.md` | edd-agent-lab | Lab must not bypass platform for Langfuse |
| `AGENTS.md` | eval-driven-design-platform | Langfuse client constraint |
