# HLD-004: Tool Requirements and Feasibility

## Status

Draft

## Purpose

This document defines how the **EDD stack** models tool requirements, tool implementations, tool bindings, and tool feasibility.

The purpose of this HLD is to prevent a common failure mode in agent design: generating a graph that depends on tools that do not actually exist, are not safe to use, or are only available as mocks.

The EDD stack should be honest about the difference between:

- What information the agent needs
- What kind of tool could provide it
- Whether that tool exists
- Which implementation is active
- Whether that implementation is safe for demo, internal, or production use

A suggested tool is not the same as an available production connector.

See also:

- [HLD-002: Domain Object Model](HLD-002-domain-object-model.md) — object definitions
- [HLD-003: Evaluation-Driven Design Workflow](HLD-003-evaluation-driven-design-workflow.md) — Phase 3 (Feasibility)

---

## Core Principle

The system must not assume that recommended tools are real.

The correct flow is:

```text
BehaviorRule
  ↓
InformationRequirement
  ↓
ToolRequirement
  ↓
ToolImplementation
  ↓
ToolBinding
  ↓
ToolFeasibilityReview
  ↓
ReadinessStatus
```

Example:

```text
Rule:
  evidence_first_diagnosis

Information needed:
  recent trace evidence

Tool requirement:
  trace_evidence_source

Suggested tool:
  fetch_trace_summary

Available implementation:
  fetch_trace_summary_mock

Feasibility:
  demo ready, production blocked

Readiness:
  promoted_for_demo only
```

This distinction is central to the product’s credibility.

---

## Key Terms

### InformationRequirement

An `InformationRequirement` describes what information the agent needs.

Example:

```yaml
information_requirement:
  id: trace_evidence
  description: >
    Recent traces, model calls, tool calls, latency, failed spans, and error patterns.
  required_for_rules:
    - evidence_first_diagnosis
    - separate_facts_from_hypotheses
```

It answers: **What does the agent need to know?**

It does not answer:

- Which tool provides it?
- Does that tool exist?
- Is that tool safe?

---

### ToolRequirement

A `ToolRequirement` describes the kind of tool needed to satisfy an information requirement or perform an action.

Example:

```yaml
tool_requirement:
  id: trace_evidence_source
  information_requirement_id: trace_evidence
  suggested_tool_name: fetch_trace_summary
  access_mode: read_only
  required_for_demo: true
  required_for_production: true
```

It answers: **What kind of tool would provide the required information?**

It does not answer:

- Do we have the tool?
- Which implementation is active?
- Is it production ready?

---

### ToolImplementation

A `ToolImplementation` describes a concrete implementation of a tool requirement.

Examples:

- mock JSON fixture
- local artifact reader
- Langfuse API connector
- GitHub API connector
- Jira API connector
- approval-gated Slack message sender

Example:

```yaml
tool_implementation:
  id: fetch_trace_summary_mock
  tool_requirement_id: trace_evidence_source
  mode: mock
  status: available
  backing_source: data/mock/escalations/apex_health/langfuse_trace_summary.json
```

It answers: **What implementation exists?**

It does not answer:

- Should this implementation be used for this run?
- Is it sufficient for production?

---

### ToolBinding

A `ToolBinding` selects which implementation is active for a graph node, version, environment, or run.

Example:

```yaml
tool_binding:
  graph_node: collect_trace_evidence
  requirement_id: trace_evidence_source
  active_implementation: fetch_trace_summary_mock
  environment: local_demo
```

It answers: **For this graph node and environment, which tool implementation is active?**

It does not answer: **Is this tool sufficient for production?**

---

### ToolFeasibilityReview

A `ToolFeasibilityReview` assesses whether a tool requirement and its available implementations are realistic for a particular use level.

Example:

```yaml
tool_feasibility:
  requirement_id: trace_evidence_source
  suggested_tool_name: fetch_trace_summary
  implementation_status: mock_only
  mvp_strategy: mock_json_fixture
  production_strategy: langfuse_api_connector
  feasibility_status: needs_review
  demo_ready: true
  production_ready: false
  risks:
    - API permissions
    - sensitive trace contents
    - trace volume
    - summarization latency
```

It answers: **Can this tool requirement be satisfied for demo, internal, or production use?**

---

## Tool Maturity Levels

The platform should use a clear maturity model.

| Level | Name | Description |
|---|---|---|
| 0 | **Missing** | Tool requirement exists, but no implementation exists. |
| 1 | **Mock fixture** | Tool returns static local fixture data. |
| 2 | **Local artifact** | Tool reads local run outputs, eval summaries, exported traces, or files. |
| 3 | **Read-only live connector** | Tool connects to a real system but cannot mutate state. |
| 4 | **Approval-gated action** | Tool can perform external actions only after human approval. |
| 5 | **Controlled automation** | Tool can perform bounded automated actions under strict policy and gates. |

### Recommended usage

| Level | Suitable for | Not suitable for |
|---|---|---|
| 0 Missing | Planning only | Running agent |
| 1 Mock fixture | Demo, offline eval | Production claims |
| 2 Local artifact | Local eval, regression | Live operation |
| 3 Read-only live | Internal assistive use | Autonomous mutation |
| 4 Approval-gated action | Human-supervised workflows | Fully autonomous use |
| 5 Controlled automation | Narrow production automation | Broad open-ended actions |

---

## Access Modes

Tool requirements should declare the intended access mode.

| Mode | Meaning |
|---|---|
| `read_only` | The tool only reads information. |
| `approval_gated_write` | The tool can write or act externally, but only after explicit human approval. |
| `controlled_automation` | The tool can take bounded actions automatically under strict gates. |

Initial agents should strongly prefer `read_only`.

Write actions should not be added casually.

---

## Tool Readiness Categories

The platform should distinguish these statuses:

```text
missing           No implementation exists.
mock_only           Only mock fixture implementation exists.
local_only          Implementation reads local artifacts or files.
read_only_live      Live connector exists but cannot mutate state.
approval_gated      Action tool exists but requires human approval.
production_ready    Tool is approved for the intended production use case.
blocked             Cannot be used due to permissions, security, unavailable APIs, or unresolved risks.
```

These statuses should feed into gates and promotion decisions.

---

## Example: Customer Escalation Triage Agent

The Customer Escalation Triage Agent has a rule:

```yaml
behavior_rule:
  id: evidence_first_diagnosis
  description: >
    The agent must base diagnosis on available evidence from traces, evals,
    recent changes, customer reports, and tool health.
```

That rule implies information requirements:

```yaml
information_requirements:
  - id: trace_evidence
    description: Recent traces, model calls, tool calls, latency, failed spans, and errors.

  - id: eval_history
    description: Recent eval results and score trends.

  - id: recent_changes
    description: Recent prompt, model, config, deployment, code, or dataset changes.

  - id: tool_health
    description: Tool failures, timeout rates, latency, and degraded dependencies.
```

Those imply tool requirements:

```yaml
tool_requirements:
  - id: trace_evidence_source
    suggested_tool_name: fetch_trace_summary
    access_mode: read_only

  - id: eval_history_source
    suggested_tool_name: fetch_eval_results
    access_mode: read_only

  - id: recent_changes_source
    suggested_tool_name: fetch_recent_changes
    access_mode: read_only

  - id: tool_health_source
    suggested_tool_name: fetch_tool_health
    access_mode: read_only
```

Tool feasibility may reveal:

```yaml
tool_feasibility:
  - requirement_id: trace_evidence_source
    implementation_status: mock_only
    demo_ready: true
    production_ready: false
    production_strategy: langfuse_api_connector

  - requirement_id: eval_history_source
    implementation_status: local_only
    demo_ready: true
    production_ready: false
    production_strategy: platform_run_database

  - requirement_id: recent_changes_source
    implementation_status: mock_only
    demo_ready: true
    production_ready: false
    production_strategy: github_or_gitlab_api

  - requirement_id: tool_health_source
    implementation_status: mock_only
    demo_ready: true
    production_ready: false
    production_strategy: metrics_or_logs_api
```

The result:

```text
Agent can be evaluated and demonstrated.
Agent cannot be promoted for production use.
```

---

## Relationship to Graph Design

Graph design should depend on tool feasibility.

A graph may include nodes such as:

```text
collect_trace_evidence
collect_eval_history
collect_recent_changes
collect_tool_health
```

But the graph design must also show the binding mode.

Example:

```yaml
graph_node:
  id: collect_trace_evidence
  tool_requirement_id: trace_evidence_source
  active_tool_implementation: fetch_trace_summary_mock
  tool_mode: mock
  production_blocker: true
```

This prevents a graph diagram from implying a live capability that does not exist.

**edd-agent-lab** implements bound tools in LangGraph; **eval-driven-design-platform** records requirements, bindings, and feasibility.

---

## Relationship to Gates

Tool readiness should feed directly into gate results.

Example gates:

```yaml
gates:
  - id: required_tools_available_for_demo
    category: tool_readiness
    type: hard
    condition: all required demo tools have mock, local, or live implementation

  - id: required_tools_available_for_production
    category: tool_readiness
    type: hard
    condition: all required production tools have approved live implementation

  - id: no_write_actions_without_approval
    category: operational_safety
    type: hard
    condition: write tools require approval unless version is promoted for controlled automation
```

Example result:

```yaml
gate_result:
  version: v1-evidence-triage-graph
  behavior_gate_status: pass
  tool_readiness_status: mock_only
  production_readiness_status: blocked
  overall_status: pass_for_demo_not_production
```

The platform should not treat behavior success and production readiness as the same thing.

Today’s quality gate API evaluates behavior against `EvalSpec` threshold or ingest metadata. Tool-readiness gates are **target state** extensions described here.

---

## Relationship to Promotion

Promotion states should depend on tool maturity.

| Promotion state | Minimum tool maturity |
|---|---|
| `promoted_for_demo` | Mock or local tools allowed |
| `promoted_for_internal_use` | Read-only live tools for required evidence |
| `promoted_for_production_assistive_use` | Read-only live tools plus approval-gated actions |
| `promoted_for_controlled_automation` | Approved controlled automation tools and strict gates |

Example:

```yaml
promotion_record:
  decision: promoted_for_demo
  production_status: blocked
  rationale: >
    v1 passes behavior gates, but trace evidence, recent changes, and tool health
    are mock-only. The version may be used for demo and offline evaluation but not
    production escalation triage.
```

---

## Required UI Behavior

The platform console should make tool readiness visible.

The user should see:

- Which information is required
- Which tool requirement satisfies it
- Which implementation is active
- Whether that implementation is mock, local, live, or action-capable
- Whether the version is demo-ready
- Whether the version is production-ready
- What is blocking production readiness

The console should never hide mock-only tool usage.

Example warning:

```text
This version uses mock/local tools. It is suitable for demo and evaluation only.
Production readiness is blocked until live trace, recent-change, and tool-health
connectors are implemented and reviewed.
```

See `edd-agent-lab/docs/11-ideal-console-design.md` — Tool Requirements, Tool Feasibility, Tool Bindings workspaces.

---

## Required Artifact Outputs

The lab and platform should be able to produce these artifacts.

### information-requirements.yaml

```yaml
information_requirements:
  - id: trace_evidence
    required_for_rules:
      - evidence_first_diagnosis
    description: Recent traces and tool-call evidence.
```

### tool-requirements.yaml

```yaml
tool_requirements:
  - id: trace_evidence_source
    information_requirement_id: trace_evidence
    suggested_tool_name: fetch_trace_summary
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
```

### tool-implementations.yaml

```yaml
tool_implementations:
  - id: fetch_trace_summary_mock
    tool_requirement_id: trace_evidence_source
    mode: mock
    status: available
    backing_source: data/mock/escalations/apex_health/langfuse_trace_summary.json
```

### tool-bindings.yaml

```yaml
tool_bindings:
  - graph_node: collect_trace_evidence
    requirement_id: trace_evidence_source
    active_implementation: fetch_trace_summary_mock
    environment: local_demo
```

### tool-feasibility.yaml

```yaml
tool_feasibility:
  - requirement_id: trace_evidence_source
    implementation_status: mock_only
    demo_ready: true
    production_ready: false
    risks:
      - sensitive trace contents
      - API permissions
```

These artifacts may later become database-backed platform records, but the conceptual separation should remain.

**edd-agent-lab** may author artifacts under `lab-runs/`; **eval-driven-design-platform** ingests and registers them via publish.

---

## API Implications

The platform API should preserve the same separation.

Possible endpoints (target state):

```http
POST /v1/agents/{agent_id}/information-requirements
POST /v1/agents/{agent_id}/tool-requirements
POST /v1/tool-implementations
POST /v1/tool-bindings
POST /v1/tool-feasibility-reviews
GET  /v1/agents/{agent_id}/tool-readiness
```

Publishing a run should include tool mode and active bindings.

Primary endpoint:

```http
POST /v1/integrations/runs/publish
```

See [HLD-007: Platform API and integration](HLD-007-platform-api-and-integration.md) for the full publish contract.

Target payload extension:

```json
{
  "agent_id": "customer-escalation-triage-agent",
  "agent_version_id": "v1-evidence-triage-graph",
  "target_id": "customer-escalation-triage-target-v1",
  "eval_contract_id": "customer-escalation-triage-eval-contract-v1",
  "tool_mode_summary": "mock_local",
  "tool_bindings": [
    {
      "graph_node": "collect_trace_evidence",
      "requirement_id": "trace_evidence_source",
      "implementation_id": "fetch_trace_summary_mock",
      "mode": "mock"
    }
  ]
}
```

The platform should return readiness status.

```json
{
  "platform_run_id": "run_v1_001",
  "behavior_status": "pass",
  "tool_status": "mock_only",
  "production_status": "blocked",
  "promotion_status": "promoted_for_demo"
}
```

Current publish envelope supports `tool_mode_summary` indirectly via ingest metadata; structured `tool_bindings` is **target state** for envelope schema v2.

---

## MVP Requirements

The first implementation does not need live tools.

It does need honest tool modeling.

Minimum MVP:

1. Generate `InformationRequirement`s from `BehaviorRule`s.
2. Generate `ToolRequirement`s from `InformationRequirement`s.
3. Represent `ToolImplementation`s separately.
4. Support mock JSON `ToolImplementation`s.
5. Support `ToolBinding`s for graph nodes.
6. Produce `ToolFeasibilityReview`.
7. Feed tool readiness into `GateResult`.
8. Prevent production-ready status when required tools are mock-only.

The MVP can use YAML artifacts before full database persistence.

---

## Anti-Patterns

### Anti-pattern: Suggested tool equals real tool

Bad:

```text
The graph needs fetch_trace_summary, so we assume fetch_trace_summary exists.
```

Good:

```text
The graph needs trace evidence.
The platform creates a ToolRequirement.
The available implementation is mock-only.
Production readiness is blocked.
```

### Anti-pattern: One generic Tool object

Bad:

```yaml
Tool:
  name: fetch_trace_summary
  status: active
```

Good:

```text
ToolRequirement: trace_evidence_source
ToolImplementation: fetch_trace_summary_mock
ToolBinding: collect_trace_evidence uses fetch_trace_summary_mock in local_demo
ToolFeasibilityReview: demo_ready=true, production_ready=false
```

### Anti-pattern: Production readiness from mocks

Bad:

```text
v1 passes evals with mock tools, so v1 is production-ready.
```

Good:

```text
v1 passes behavior gates with mock tools.
v1 is promoted_for_demo.
Production readiness is blocked.
```

### Anti-pattern: Tool feasibility hidden in README text

Tool feasibility should be structured and queryable.

It should influence gates and promotion.

---

## Acceptance Criteria for This HLD

Implementation is aligned with this HLD when:

1. `InformationRequirement` is modeled separately from `ToolRequirement`.
2. `ToolRequirement` is modeled separately from `ToolImplementation`.
3. `ToolImplementation` is modeled separately from `ToolBinding`.
4. `ToolFeasibilityReview` is modeled separately from all of the above.
5. Suggested tools are never treated as automatically available.
6. Mock/local/live/action tool modes are visible in artifacts and UI.
7. Tool readiness contributes to `GateResult`.
8. Promotion distinguishes demo readiness from production readiness.
9. Runs record active tool bindings or tool mode summary.
10. The console warns users when mock-only tools are active.
11. The API payload for run publishing includes tool binding context.
12. Production readiness is blocked when required production tools are missing or mock-only.

---

## Summary

Tool modeling is one of the most important credibility features of the EDD stack.

The platform should not only ask:

> Did the agent produce a good answer?

It should also ask:

- Did the agent have the information required to produce that answer?
- Which tools provided that information?
- Were those tools mock, local, live, or action-capable?
- Can this version be used for demo, internal work, or production?

The correct product behavior is:

```text
v1 passes behavior gates.
v1 uses mock trace and tool-health data.
v1 is promoted_for_demo.
v1 is blocked for production.
```

That honesty is central to the design.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD-001](HLD-001-product-intent-and-system-boundaries.md) | eval-driven-design-platform | System boundaries |
| [HLD-002](HLD-002-domain-object-model.md) | eval-driven-design-platform | Tool-related domain objects |
| [HLD-003](HLD-003-evaluation-driven-design-workflow.md) | eval-driven-design-platform | Phase 3 (Feasibility) |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Canonical reference scenario |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | MVP implementation plan |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Platform API and integration |
| [HLD-008](HLD-008-langfuse-integration.md) | eval-driven-design-platform | Langfuse integration |
| [HLD index](README.md) | eval-driven-design-platform | HLD series overview |
| `docs/11-ideal-console-design.md` | edd-agent-lab | Tool UI workspaces |
