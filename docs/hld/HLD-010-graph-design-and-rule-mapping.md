# HLD-010: Graph Design and Rule Mapping

## Status

Draft

## Purpose

This document defines how graph designs should be derived from agent targets, behavior rules, eval contracts, information requirements, tool requirements, and failure packets.

The purpose of this HLD is to prevent graph implementations from becoming arbitrary.

In the **EDD stack**, a graph node should exist for a reason.

Acceptable reasons include:

```text
behavior rule
information requirement
tool requirement
tool feasibility constraint
failure packet
fix plan
operational safety requirement
```

The graph is not just an implementation detail. It is part of the design response to the eval contract.

See also:

- [HLD-002: Domain object model](HLD-002-domain-object-model.md) — `GraphDesign`, `GraphNode`
- [HLD-004: Tool requirements and feasibility](HLD-004-tool-requirements-and-feasibility.md)
- [HLD-005: Reference scenario](HLD-005-reference-scenario-customer-escalation-triage.md) — `graph-design.yaml`
- [HLD-006: MVP implementation plan](HLD-006-mvp-implementation-plan.md) — milestones M2–M3
- [HLD-009: Architecture and flow diagrams](HLD-009-architecture-and-flow-diagrams.md) — target-to-graph flow (§3)

---

## Core Principle

A graph should be explainable from the design artifacts.

| Bad | Good |
|---|---|
| We added a node because it seemed useful. | We added `separate_facts_hypotheses_unknowns` because v0 failed `separate_facts_from_hypotheses` and overclaimed root cause. |

The ideal chain is:

```text
AgentTarget
  → BehaviorRule
  → InformationRequirement
  → ToolRequirement
  → GraphNode
  → ExperimentRun
  → FailurePacket
  → FixPlan
  → Updated GraphNode
```

---

## Current Implementation (snapshot)

| Area | Today | Target (this HLD) |
|---|---|---|
| **GraphDesign object** | Described in HLD-002; not first-class in platform DB | Schema + `graph-design.yaml` artifact |
| **Lab reference agent** | Customer Solution Discovery LangGraph | Customer Escalation Triage v0/v1 per HLD-005 |
| **Rule-to-node mapping** | Implicit in agent code | Explicit in `graph-design.yaml` + console |
| **Publish payload** | v1 envelope; no `graph_design` section | `graph_design` on publish (HLD-007) |
| **Console** | No graph design view | Graph overview, node detail, rule/failure views |

---

## Graph Design Inputs

A `GraphDesign` should be generated or reviewed using these inputs:

```text
AgentTarget
BehaviorRule
EvalContract
InformationRequirement
ToolRequirement
ToolFeasibilityReview
FailurePacket
FixPlan
Operational safety policy
```

Each graph node should map back to at least one of those inputs.

---

## Graph Design Object

A graph design represents the intended architecture of an agent version.

Example:

```yaml
graph_design:
  id: customer-escalation-triage-graph-v1
  agent_target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  version: v1
  name: Evidence-first escalation triage graph
  description: >
    Evidence-first graph that collects customer reports, traces, eval history,
    recent changes, tool health, and customer context before producing a
    grounded diagnosis and customer-safe update.
```

A graph design should not be just a diagram. It should explain why the graph exists.

---

## Graph Node Object

Each graph node should include:

```yaml
graph_node:
  id: string
  name: string
  purpose: string
  supports_rules: list[string]
  information_requirements: list[string]
  tool_requirements: list[string]
  tool_bindings: list[string]
  prompts: list[string]
  reads_state: list[string]
  writes_state: list[string]
  failure_packets_addressed: list[string]
  operational_safety_notes: list[string]
```

Not every field is required for every node, but every significant node should have a clear purpose and traceability.

---

## Required Node Traceability

Every significant graph node should answer these questions:

```text
Why does this node exist?
Which behavior rule does it support?
What information does it need?
What tool requirement does it depend on?
What state does it read?
What state does it write?
Which prompt does it use?
Which failure packet or fix plan introduced it?
```

If those questions cannot be answered, the node may not belong in the graph.

---

## Reference Graph: Customer Escalation Triage

The reference v1 graph is:

```text
start
  ↓
parse_escalation_report
  ↓
collect_evidence
  ├── collect_customer_report
  ├── collect_trace_evidence
  ├── collect_eval_history
  ├── collect_recent_changes
  ├── collect_tool_health
  └── collect_customer_context
  ↓
normalize_evidence
  ↓
identify_correlations
  ↓
separate_facts_hypotheses_unknowns
  ↓
assess_customer_impact
  ↓
recommend_mitigation_plan
  ↓
draft_customer_update
  ↓
customer_safe_update_review
  ↓
final_response
```

This graph exists because the agent must avoid unsupported diagnosis and produce safe escalation guidance.

See [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) and [HLD-008](HLD-008-langfuse-integration.md) for trace hierarchy.

---

## Rule-to-Node Mapping

The graph should make rule support explicit.

| Behavior Rule | Required Graph Behavior | Graph Nodes |
|---|---|---|
| `evidence_first_diagnosis` | Gather and normalize evidence before diagnosis | `collect_evidence`, `normalize_evidence` |
| `separate_facts_from_hypotheses` | Split confirmed facts, hypotheses, and unknowns | `separate_facts_hypotheses_unknowns` |
| `identify_recent_changes` | Check whether recent changes correlate with the issue | `collect_recent_changes`, `identify_correlations` |
| `assess_customer_impact` | Summarize impact and urgency | `assess_customer_impact` |
| `recommend_safe_next_actions` | Produce sequenced, non-destructive next steps | `recommend_mitigation_plan` |
| `draft_customer_safe_update` | Draft and review external-safe message | `draft_customer_update`, `customer_safe_update_review` |

This table should be visible in the platform console or exportable as an artifact.

---

## Information-to-Node Mapping

Information requirements should also map to graph behavior.

| Information Requirement | Graph Node | Notes |
|---|---|---|
| `customer_report` | `collect_customer_report` | Reported symptoms, timing, urgency |
| `trace_evidence` | `collect_trace_evidence` | Trace summary, latency, failed spans |
| `eval_history` | `collect_eval_history` | Score trends and regressions |
| `recent_changes` | `collect_recent_changes` | Prompt/config/deployment changes |
| `tool_health` | `collect_tool_health` | Tool timeouts, failures, degraded dependencies |
| `customer_context` | `collect_customer_context` | Environment, communication constraints |

This mapping prevents the graph from collecting information that is not tied to a design need.

---

## Tool-to-Node Mapping

Tool requirements should be visible at the graph node level.

Example:

```yaml
graph_node:
  id: collect_trace_evidence
  purpose: >
    Retrieve trace evidence for the affected workflow and time window.
  supports_rules:
    - evidence_first_diagnosis
    - separate_facts_from_hypotheses
  information_requirements:
    - trace_evidence
  tool_requirements:
    - trace_evidence_source
  tool_bindings:
    - fetch_trace_summary_mock
  reads_state:
    - customer_id
    - time_window
    - affected_workflow
  writes_state:
    - trace_summary
  operational_safety_notes:
    - Trace data may contain sensitive information.
    - Do not expose raw trace contents in customer-facing output.
```

The node should not imply a live tool exists if the active binding is mock/local.

---

## Failure-to-Node Mapping

Failure packets should influence graph changes.

Example failure:

```yaml
failure_packet:
  id: fp-v0-unsupported-root-cause
  failed_rule: separate_facts_from_hypotheses
  suspected_cause: >
    v0 has no explicit evidence normalization or facts/hypotheses/unknowns step.
  recommended_fix: >
    Add normalize_evidence and separate_facts_hypotheses_unknowns nodes before
    mitigation planning or customer communication.
```

Corresponding graph changes:

```yaml
fix_plan:
  graph_changes:
    - Add normalize_evidence node.
    - Add separate_facts_hypotheses_unknowns node.
```

New nodes:

```yaml
graph_nodes:
  - id: normalize_evidence
    failure_packets_addressed:
      - fp-v0-unsupported-root-cause

  - id: separate_facts_hypotheses_unknowns
    failure_packets_addressed:
      - fp-v0-unsupported-root-cause
```

This creates a traceable reason for v1.

---

## v0 Graph Pattern

v0 may be intentionally simple.

Example:

```text
start
  ↓
single_pass_response
  ↓
final_response
```

v0 design:

```yaml
graph_design:
  id: customer-escalation-triage-graph-v0
  version: v0
  description: >
    Single-pass prompt baseline. No evidence collection, tool bindings,
    evidence normalization, facts/hypotheses separation, or customer-safe update review.
```

v0 is expected to reveal failures.

It should not be treated as production-ready.

---

## v1 Graph Pattern

v1 should implement bounded fixes from v0 failures.

Example:

```text
start
  ↓
parse_escalation_report
  ↓
collect_evidence
  ↓
normalize_evidence
  ↓
identify_correlations
  ↓
separate_facts_hypotheses_unknowns
  ↓
assess_customer_impact
  ↓
recommend_mitigation_plan
  ↓
draft_customer_update
  ↓
customer_safe_update_review
  ↓
final_response
```

v1 design:

```yaml
graph_design:
  id: customer-escalation-triage-graph-v1
  version: v1
  source_version: v0-baseline
  fix_plan_id: fix-v1-evidence-first-triage
  description: >
    Adds explicit evidence-first triage behavior in response to v0 failures.
```

---

## State Design

Graph state should be explicit and inspectable.

Example state fields:

```yaml
state_fields:
  user_request: string
  customer_id: string
  affected_workflow: string
  time_window: string

  customer_report: object
  trace_summary: object
  eval_history: object
  recent_changes: object
  tool_health: object
  customer_context: object

  normalized_evidence: object
  confirmed_facts: list[string]
  hypotheses: list[object]
  unknowns: list[string]
  customer_impact: object
  recommended_actions: list[object]
  customer_update_draft: string
  customer_update_review: object
  final_response: string
```

Each node should declare which state fields it reads and writes.

This improves traceability and helps debugging.

---

## Prompt Mapping

Prompts should be tied to graph nodes.

Example:

```yaml
prompt:
  id: facts_hypotheses_unknowns_prompt
  graph_node_id: separate_facts_hypotheses_unknowns
  purpose: >
    Instruct the model to separate confirmed facts, plausible hypotheses, and unknowns.
  supports_rules:
    - separate_facts_from_hypotheses
    - evidence_first_diagnosis
```

A prompt should not be an unattached text file.

It should be connected to a node and behavior rule.

---

## Tool Feasibility in Graph Design

Graph design must show whether required tools are mock, local, live, or missing.

Example:

```yaml
graph_node:
  id: collect_trace_evidence
  tool_requirement: trace_evidence_source
  active_implementation: fetch_trace_summary_mock
  tool_mode: mock
  production_blocker: true
```

The graph diagram may show this as a badge:

```text
collect_trace_evidence [mock]
collect_eval_history [local]
collect_recent_changes [mock]
collect_tool_health [mock]
```

This prevents a demo graph from looking production-ready.

---

## Operational Safety Nodes

When an agent can affect external systems or customer communication, graph design should include safety review nodes.

Examples:

```text
customer_safe_update_review
action_requires_approval_check
sensitive_data_redaction_check
rollback_recommendation_review
```

For the reference scenario:

```yaml
graph_node:
  id: customer_safe_update_review
  purpose: >
    Review customer-facing update for speculation, unsupported root-cause claims,
    and sensitive internal trace details.
  supports_rules:
    - draft_customer_safe_update
    - separate_facts_from_hypotheses
  operational_safety_notes:
    - Do not expose raw trace data.
    - Do not claim confirmed root cause unless explicitly supported.
```

Operational safety is part of graph design, not an afterthought.

---

## Console Requirements

The platform console should show graph design in several ways.

### Graph overview

Show the graph structure:

```text
parse_escalation_report
  → collect_evidence
  → normalize_evidence
  → identify_correlations
  → separate_facts_hypotheses_unknowns
  → assess_customer_impact
  → recommend_mitigation_plan
  → draft_customer_update
  → customer_safe_update_review
  → final_response
```

### Node detail

When a user selects a node, show:

```text
Purpose
Rules supported
Information requirements used
Tool requirements used
Active tool binding
Tool mode
Prompts used
State fields read
State fields written
Failures addressed
Operational safety notes
```

### Rule-to-node view

```text
Rule → Node(s) → Latest result
```

Example:

```text
separate_facts_from_hypotheses
  → separate_facts_hypotheses_unknowns
  → passed in v1, failed in v0
```

### Failure-to-node view

```text
FailurePacket → FixPlan → Graph changes
```

Example:

```text
fp-v0-unsupported-root-cause
  → fix-v1-evidence-first-triage
  → added normalize_evidence and separate_facts_hypotheses_unknowns
```

---

## Lab Artifact Requirements

The lab should produce a `graph-design.yaml` artifact.

Example:

```yaml
graph_design:
  id: customer-escalation-triage-graph-v1
  agent_target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  source_version: v0-baseline
  fix_plan_id: fix-v1-evidence-first-triage

graph_nodes:
  - id: collect_trace_evidence
    purpose: Retrieve trace evidence for the affected workflow.
    supports_rules:
      - evidence_first_diagnosis
    information_requirements:
      - trace_evidence
    tool_requirements:
      - trace_evidence_source
    active_tool_binding: fetch_trace_summary_mock
    tool_mode: mock
    production_blocker: true

  - id: separate_facts_hypotheses_unknowns
    purpose: Separate confirmed facts, hypotheses, and unknowns.
    supports_rules:
      - separate_facts_from_hypotheses
      - evidence_first_diagnosis
    failure_packets_addressed:
      - fp-v0-unsupported-root-cause
```

The platform should be able to ingest or display this artifact.

Target path: `lab-runs/customer_escalation_triage/target/graph-design.yaml` (see HLD-006 M3).

---

## API Implications

The publish endpoint should accept graph design artifacts or references.

```http
POST /v1/integrations/runs/publish
```

Relevant payload section:

```json
{
  "graph_design": {
    "id": "customer-escalation-triage-graph-v1",
    "agent_target_id": "customer-escalation-triage-target-v1",
    "eval_contract_id": "customer-escalation-triage-eval-contract-v1",
    "source_version": "v0-baseline",
    "fix_plan_id": "fix-v1-evidence-first-triage",
    "graph_nodes": [
      {
        "id": "separate_facts_hypotheses_unknowns",
        "supports_rules": [
          "separate_facts_from_hypotheses",
          "evidence_first_diagnosis"
        ],
        "failure_packets_addressed": [
          "fp-v0-unsupported-root-cause"
        ]
      }
    ]
  }
}
```

For MVP, graph design may be included as an artifact path. Later, the platform can persist node-level objects.

See [HLD-007](HLD-007-platform-api-and-integration.md).

---

## Graph Diff Requirements

The platform should eventually show a graph diff between versions.

Minimum useful comparison:

```text
v0:
  single_pass_response

v1 added:
  collect_evidence
  normalize_evidence
  identify_correlations
  separate_facts_hypotheses_unknowns
  customer_safe_update_review
```

Each added node should link to a failure packet or fix plan.

Example:

```text
Added node:
  separate_facts_hypotheses_unknowns

Reason:
  fp-v0-unsupported-root-cause

Rule:
  separate_facts_from_hypotheses
```

---

## Anti-Patterns

### Anti-pattern: Random graph nodes

| Bad | Good |
|---|---|
| Add `analyze_context` because it sounds useful. | Add `normalize_evidence` because v0 failed `evidence_first_diagnosis` and the fix plan requires evidence normalization. |

### Anti-pattern: Prompt-only reasoning hidden inside one node

| Bad | Good |
|---|---|
| Single giant node handles everything forever | Split behavior where rules require explicit structure: collect evidence, normalize evidence, separate facts/hypotheses, review customer update |

### Anti-pattern: Tool readiness hidden from graph

| Bad | Good |
|---|---|
| `collect_trace_evidence` | `collect_trace_evidence [mock, production blocker]` |

### Anti-pattern: Graph changes not tied to failures

| Bad | Good |
|---|---|
| v1 has a different graph, but no explanation why | v1 added two nodes to address `fp-v0-unsupported-root-cause` |

### Anti-pattern: Eval contract ignored in graph design

| Bad | Good |
|---|---|
| Eval metrics exist, but graph design does not map to them | `diagnostic_grounding` maps to `collect_evidence`, `normalize_evidence`, and `separate_facts_hypotheses_unknowns` |

---

## MVP Requirements

The MVP should support:

1. `graph-design.yaml` artifact
2. Rule-to-node mapping
3. Information-to-node mapping
4. Tool-to-node mapping
5. Failure-to-node mapping for v1 fixes
6. Tool mode badges or fields on graph nodes
7. Console display of graph nodes and their purpose
8. v0/v1 graph difference summary

The MVP does not need a fully interactive graph renderer.

A readable table or text diagram is acceptable.

---

## Acceptance Criteria for This HLD

Implementation is aligned with this HLD when:

1. `GraphDesign` references `AgentTarget` and `EvalContract`.
2. `GraphNode`s explain their purpose.
3. `GraphNode`s map to `BehaviorRule`s where applicable.
4. `GraphNode`s map to `InformationRequirement`s where applicable.
5. `GraphNode`s map to `ToolRequirement`s where applicable.
6. `GraphNode`s show active tool mode when tools are involved.
7. v1 graph changes reference `FailurePacket`s or `FixPlan`s.
8. The platform console can explain why v1 added new nodes.
9. The lab exports `graph-design.yaml` for the reference scenario.
10. Tool readiness is visible in graph design.

---

## Summary

Graph design should be evaluation-driven.

The platform should be able to explain:

```text
This rule required this behavior.
This behavior required this information.
This information required this tool.
This tool was mock-only.
This graph node used that tool.
This v0 failure showed the node was missing.
This v1 fix added the node.
This gate passed after the change.
Production remained blocked because the tool was not live.
```

That is the relationship this HLD exists to preserve.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series |
| [HLD-003](HLD-003-evaluation-driven-design-workflow.md) | eval-driven-design-platform | Design phases |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Reference graph payloads |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | M2 artifacts, M3 lab agent |
| [HLD-009](HLD-009-architecture-and-flow-diagrams.md) | eval-driven-design-platform | Target-to-graph diagram |
| [HLD-011](HLD-011-console-information-architecture.md) | eval-driven-design-platform | Graph Design screen |
