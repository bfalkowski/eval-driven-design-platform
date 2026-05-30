# HLD-003: Evaluation-Driven Design Workflow

## Status

Draft

## Purpose

This document defines the canonical evaluation-driven design workflow for the **EDD stack**.

The purpose of this HLD is to make the intended lifecycle explicit so implementation agents do not accidentally build only an eval dashboard, only a LangGraph runner, or only a trace viewer.

The EDD stack should guide users from an initial agent idea to a validated, traceable, versioned, and eventually operational agent.

The core workflow is:

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
  → failure packets
  → bounded fix
  → v1
  → comparison
  → gates
  → promotion
  → operation
```

Evaluation is not only a final check.

Evaluation should shape the agent design.

See also:

- [HLD-001: Product Intent and System Boundaries](HLD-001-product-intent-and-system-boundaries.md)
- [HLD-002: Domain Object Model](HLD-002-domain-object-model.md)

---

## Core Workflow Principle

The platform should not start by asking:

> How did this agent score?

It should start by asking:

> What is this agent supposed to do?

A weak workflow is:

```text
Build agent → Run evals → Look at score → Change prompt → Run evals again
```

The intended workflow is:

```text
Define target behavior
  → Derive rules
  → Derive eval contract
  → Derive information requirements
  → Derive tool requirements
  → Review tool feasibility
  → Shape graph design
  → Run baseline
  → Diagnose failures
  → Generate bounded fix
  → Verify improvement
  → Promote only with evidence
```

This distinction is central to the product.

---

## Workflow Phases

The lifecycle has seven major phases:

| Phase | Name | Primary outputs |
|---|---|---|
| 1 | **Define** | `Agent`, `AgentTarget` |
| 2 | **Specify** | `BehaviorRule`, `EvalContract`, `Metric`, `Gate`, `Scenario`, `ScenarioSet` |
| 3 | **Feasibility** | `InformationRequirement`, `ToolRequirement`, `ToolImplementation`, `ToolBinding`, `ToolFeasibilityReview` |
| 4 | **Build** | `GraphDesign`, `GraphNode`, `Prompt`, `AgentVersion` (v0), `Artifact` |
| 5 | **Evaluate** | `ExperimentRun`, `TraceLink`, `Score`, `FailurePacket`, `GateResult` |
| 6 | **Improve** | `FixPlan`, `AgentVersion` (v1), `Comparison` |
| 7 | **Promote and Operate** | `GateResult`, `ReadinessStatus`, `PromotionRecord`, `OperationalRun` |

Object definitions are in [HLD-002](HLD-002-domain-object-model.md).

---

## Phase 1: Define

### Goal

Capture what the agent is supposed to do.

The user should be able to start with a plain-language description.

Example:

```text
I want an agent that helps FDEs triage customer escalations for AI deployments.
It should look at traces, eval results, recent changes, tool failures, and
customer reports. It should identify likely causes, recommend safe next actions,
and draft a customer-safe update. It must not invent root causes.
```

### Primary objects

- `Agent`
- `AgentTarget`

### Output

A structured `AgentTarget`.

```yaml
agent_target:
  id: customer-escalation-triage-target-v1
  name: Customer Escalation Triage Agent
  purpose: >
    Help Forward Deployed Engineers triage customer escalations in AI deployments
    by synthesizing customer reports, traces, eval results, recent changes, and
    tool health into a grounded diagnosis and action plan.
  intended_users:
    - Forward Deployed Engineers
    - Platform Engineers
    - Customer deployment leads
  primary_goals:
    - Summarize the customer-reported problem.
    - Identify relevant evidence.
    - Separate confirmed facts from hypotheses.
    - Recommend safe next actions.
    - Draft a customer-safe update.
  non_goals:
    - Do not claim a confirmed root cause without evidence.
    - Do not expose sensitive trace details in customer-facing messages.
    - Do not suggest destructive production changes without approval.
```

### Acceptance criteria

1. The user can create or select an `Agent`.
2. The user can create an `AgentTarget` from plain language or structured input.
3. The `AgentTarget` includes purpose, users, goals, non-goals, and risk areas.
4. The `AgentTarget` can be saved as draft or marked active.
5. The `AgentTarget` is versioned.

### Anti-patterns

- Do not start with an `AgentVersion` before an `AgentTarget` exists.
- Do not treat a prompt as the only definition of agent intent.
- Do not overwrite an active target without versioning the change.

---

## Phase 2: Specify

### Goal

Turn target intent into evaluable expectations.

The platform derives behavior rules and eval contracts from the active target.

### Primary objects

- `BehaviorRule`
- `EvalContract`
- `Metric`
- `Gate`
- `Scenario`
- `ScenarioSet`

### Step 2.1: Generate behavior rules

Behavior rules define what the agent must do or avoid.

```yaml
behavior_rules:
  - id: evidence_first_diagnosis
    severity: critical
    description: >
      The agent must base diagnosis on available evidence from traces, evals,
      recent changes, customer reports, and tool health.

  - id: separate_facts_from_hypotheses
    severity: critical
    description: >
      The agent must distinguish confirmed facts from likely causes and unknowns.

  - id: recommend_safe_next_actions
    severity: high
    description: >
      The agent must recommend safe, sequenced mitigation and investigation steps.
```

### Step 2.2: Generate eval contract

The eval contract maps behavior rules to metrics and gates.

```yaml
eval_contract:
  id: customer-escalation-triage-eval-contract-v1
  target_id: customer-escalation-triage-target-v1

  metrics:
    - id: diagnostic_grounding
      scale: 0-5
      rules:
        - evidence_first_diagnosis
        - separate_facts_from_hypotheses

    - id: action_plan_quality
      scale: 0-5
      rules:
        - recommend_safe_next_actions

  gates:
    - id: no_unsupported_root_cause
      type: hard
      condition: diagnostic_grounding >= 4

    - id: must_include_safe_next_actions
      type: hard
      condition: action_plan_quality >= 4
```

### Step 2.3: Create or attach scenarios

Scenarios provide concrete situations for evaluating behavior.

```yaml
scenario:
  id: escalation-latency-quality-regression-001
  name: Latency and Quality Regression After Prompt Change
  user_prompt: >
    Customer Apex Health says their AI assistant started giving inconsistent answers
    this week. They say latency is worse and their reviewers are losing confidence.
    We changed the summarization prompt two days ago. Langfuse shows latency is up,
    eval scores dropped for scanned PDF cases, and the eligibility-check tool has
    intermittent timeouts. Help me triage and draft an update.
  expected_behavior:
    - Summarize the customer issue.
    - Identify known facts.
    - Identify hypotheses without claiming certainty.
    - Recommend safe immediate actions.
    - Draft a customer-safe update.
```

### Output

- `BehaviorRule`s
- `EvalContract`
- `ScenarioSet`

### Acceptance criteria

1. `BehaviorRule`s are generated from `AgentTarget`.
2. Rules are user-reviewable and editable.
3. `EvalContract` references `BehaviorRule`s.
4. Metrics and gates are explicit.
5. `ScenarioSet` is attached to the `EvalContract`.
6. The `EvalContract` can be saved as draft or active.
7. Changes to the `EvalContract` are versioned.

### Anti-patterns

- Do not create scores without knowing which rules they evaluate.
- Do not compare v0 and v1 using silently different eval contracts.
- Do not hide gate conditions inside code without exposing them as platform concepts.

---

## Phase 3: Feasibility

### Goal

Identify what information the agent needs, what tools could provide that information, and whether those tools actually exist.

This phase prevents the system from generating unrealistic graphs with imaginary tools.

### Primary objects

- `InformationRequirement`
- `ToolRequirement`
- `ToolImplementation`
- `ToolBinding`
- `ToolFeasibilityReview`

### Step 3.1: Generate information requirements

```yaml
information_requirements:
  - id: trace_evidence
    required_for_rules:
      - evidence_first_diagnosis
      - separate_facts_from_hypotheses
    description: >
      Recent traces, model calls, tool calls, latency, failed spans, and error patterns.

  - id: recent_changes
    required_for_rules:
      - identify_recent_changes
    description: >
      Recent prompt, model, config, deployment, code, or dataset changes.

  - id: tool_health
    required_for_rules:
      - evidence_first_diagnosis
      - recommend_safe_next_actions
    description: >
      Tool failures, timeout rates, latency, and degraded dependencies.
```

### Step 3.2: Generate tool requirements

```yaml
tool_requirements:
  - id: trace_evidence_source
    information_requirement_id: trace_evidence
    suggested_tool_name: fetch_trace_summary
    access_mode: read_only
    required_for_demo: true
    required_for_production: true

  - id: recent_changes_source
    information_requirement_id: recent_changes
    suggested_tool_name: fetch_recent_changes
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
```

### Step 3.3: Review tool feasibility

```yaml
tool_feasibility:
  - requirement_id: trace_evidence_source
    suggested_tool_name: fetch_trace_summary
    implementation_status: mock_only
    mvp_strategy: mock_json_fixture
    production_strategy: langfuse_api_connector
    feasibility_status: needs_review
    production_ready: false
    risks:
      - API permissions
      - sensitive trace contents
      - trace volume

  - requirement_id: recent_changes_source
    suggested_tool_name: fetch_recent_changes
    implementation_status: not_implemented
    mvp_strategy: mock_changelog_json
    production_strategy: github_or_gitlab_api
    feasibility_status: blocked
    production_ready: false
```

### Step 3.4: Create tool bindings

```yaml
tool_bindings:
  - graph_node: collect_trace_evidence
    requirement_id: trace_evidence_source
    active_implementation: fetch_trace_summary_mock
    environment: local_demo

  - graph_node: collect_recent_changes
    requirement_id: recent_changes_source
    active_implementation: fetch_recent_changes_mock
    environment: local_demo
```

### Output

- `InformationRequirement`s
- `ToolRequirement`s
- `ToolFeasibilityReview`s
- `ToolImplementation`s
- `ToolBinding`s

### Acceptance criteria

1. `InformationRequirement`s are generated before `ToolRequirement`s.
2. `ToolRequirement`s are not treated as implemented tools.
3. `ToolFeasibilityReview` identifies missing, mock-only, local, live, and production-ready tools.
4. `ToolBinding`s specify which implementation is active for each environment.
5. Production readiness is blocked when required tools are mock-only or missing.

### Anti-patterns

- Do not assume suggested tools exist.
- Do not mark a version production-ready when required tools are mock-only.
- Do not collapse information requirements, tool requirements, implementations, and bindings into one object.

---

## Phase 4: Build

### Goal

Create a graph design and agent version that reflect the target, rules, information needs, and tool feasibility.

### Primary objects

- `GraphDesign`
- `GraphNode`
- `Prompt`
- `AgentVersion`
- `Artifact`

**edd-agent-lab** implements runnable graphs; **eval-driven-design-platform** tracks design intent and version registry.

### Step 4.1: Generate graph design

```text
start
  ↓
parse_escalation_report
  ↓
collect_evidence
  ├── fetch_customer_report
  ├── fetch_trace_summary
  ├── fetch_eval_results
  ├── fetch_recent_changes
  ├── fetch_tool_health
  └── fetch_customer_context
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

### Step 4.2: Map rules to nodes

```yaml
graph_node:
  id: separate_facts_hypotheses_unknowns
  purpose: >
    Prevent unsupported diagnosis by separating confirmed facts,
    plausible hypotheses, and unknowns before recommending actions.
  supports_rules:
    - separate_facts_from_hypotheses
    - evidence_first_diagnosis
  reads_state:
    - normalized_evidence
    - trace_summary
    - eval_history
    - recent_changes
    - tool_health
  writes_state:
    - confirmed_facts
    - hypotheses
    - unknowns
```

### Step 4.3: Create v0

v0 should be a baseline implementation. It does not need to be perfect. In many cases, v0 is intentionally simple so the eval process can expose failures.

```yaml
agent_version:
  id: v0-baseline
  implementation_summary: >
    Single-pass prompt agent. No explicit evidence collection. No tool bindings.
    No facts/hypotheses separation. No customer-safe update review.
```

### Output

- `GraphDesign`
- `GraphNode`s
- `Prompt`s
- `AgentVersion` v0
- `Artifact`s

### Acceptance criteria

1. `GraphDesign` references `AgentTarget` and `EvalContract`.
2. `GraphNode`s map to rules, information requirements, tool requirements, or fix plans.
3. `AgentVersion` references target, eval contract, graph design, and tool bindings.
4. v0 can be run through **edd-agent-lab**.
5. Generated artifacts are saved or publishable via `POST /v1/integrations/runs/publish`.

### Anti-patterns

- Do not create graph nodes with no design reason.
- Do not treat a prompt-only v0 as production-ready.
- Do not hide tool binding mode from the user.

---

## Phase 5: Evaluate

### Goal

Run an agent version against scenarios, capture traces, score behavior, and generate failure packets.

### Primary objects

- `ExperimentRun`
- `TraceLink`
- `Score`
- `FailurePacket`
- `GateResult`
- `Artifact`

### Step 5.1: Run agent version

A run should always record:

- agent
- agent version
- target
- eval contract
- scenario set
- tool bindings
- environment
- model
- evaluator
- trace destination

```yaml
experiment_run:
  id: run_v0_001
  agent_version_id: v0-baseline
  target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  scenario_set_id: escalation-core-scenarios
  environment: local_demo
  tool_mode_summary: none
```

### Step 5.2: Capture trace evidence

Trace evidence should be linked through `TraceLink`.

Example metadata sent to Langfuse:

```json
{
  "platform_run_id": "run_v0_001",
  "platform_agent_id": "customer-escalation-triage-agent",
  "platform_agent_version": "v0-baseline",
  "platform_target_id": "customer-escalation-triage-target-v1",
  "platform_eval_contract_id": "customer-escalation-triage-eval-contract-v1",
  "scenario_id": "escalation-latency-quality-regression-001",
  "tool_mode": "none",
  "environment": "local_demo"
}
```

### Step 5.3: Score behavior

Scores should reference metrics from the active eval contract.

```yaml
scores:
  diagnostic_grounding: 2
  change_correlation_quality: 3
  impact_assessment_quality: 2
  action_plan_quality: 3
  customer_communication_quality: 2
```

### Step 5.4: Generate failure packets

```yaml
failure_packet:
  id: fp-v0-unsupported-root-cause
  version: v0-baseline
  scenario_id: escalation-latency-quality-regression-001
  failed_rule: separate_facts_from_hypotheses
  severity: critical

  observed_behavior: >
    The agent stated that the summarization prompt change was the likely cause
    and recommended telling the customer the issue had been found.

  expected_behavior: >
    The agent should have separated confirmed facts from hypotheses.

  suspected_cause: >
    v0 has no explicit evidence normalization or facts/hypotheses/unknowns step.

  recommended_fix: >
    Add normalize_evidence and separate_facts_hypotheses_unknowns nodes.
```

### Output

- `ExperimentRun`
- `TraceLink`s
- `Score`s
- `FailurePacket`s
- `GateResult`s
- `Artifact`s

### Acceptance criteria

1. Runs are linked to agent version, target, eval contract, scenario set, and tool mode.
2. Traces include platform metadata.
3. Scores reference `EvalContract` metrics.
4. Failed gates create or reference `FailurePacket`s.
5. `FailurePacket`s identify a concrete design cause where possible.

### Anti-patterns

- Do not produce orphan scores with no metric definition.
- Do not produce failure packets without rule references.
- Do not require users to manually attach trace evidence when the system can link it.

---

## Phase 6: Improve

### Goal

Use failure packets to create bounded fixes and improved agent versions.

### Primary objects

- `FailurePacket`
- `FixPlan`
- `GraphDesign`
- `Prompt`
- `ToolBinding`
- `AgentVersion`
- `Comparison`

### Step 6.1: Generate fix plan

```yaml
fix_plan:
  id: fix-v1-evidence-first-triage
  source_version: v0-baseline
  target_version: v1-evidence-triage-graph

  failed_rules_addressed:
    - evidence_first_diagnosis
    - separate_facts_from_hypotheses
    - recommend_safe_next_actions
    - draft_customer_safe_update

  graph_changes:
    - Add collect_evidence node.
    - Add normalize_evidence node.
    - Add identify_correlations node.
    - Add separate_facts_hypotheses_unknowns node.
    - Add customer_safe_update_review node.

  tool_changes:
    - Add mock trace summary tool.
    - Add mock eval results tool.
    - Add mock recent changes tool.
    - Add mock tool health tool.

  non_goals:
    - Do not automatically roll back production.
    - Do not contact the customer automatically.
    - Do not claim production readiness while tools are mock-only.
```

### Step 6.2: Create v1

```yaml
agent_version:
  id: v1-evidence-triage-graph
  source_version: v0-baseline
  fix_plan_id: fix-v1-evidence-first-triage
  implementation_summary: >
    Adds evidence collection, evidence normalization, correlation review,
    facts/hypotheses/unknowns separation, and customer-safe update review.
```

### Step 6.3: Compare v0 and v1

```yaml
comparison:
  baseline: v0-baseline
  candidate: v1-evidence-triage-graph

  score_delta:
    diagnostic_grounding:
      v0: 2
      v1: 5
      delta: 3

  resolved_failures:
    - no_unsupported_root_cause
    - must_separate_facts_and_hypotheses

  remaining_warnings:
    - Production readiness blocked by mock-only tools.
```

### Output

- `FixPlan`
- `AgentVersion` v1
- `Comparison`
- Updated `GateResult`s

### Acceptance criteria

1. `FixPlan` references `FailurePacket`s.
2. `FixPlan` lists graph, prompt, and tool changes.
3. `FixPlan` includes non-goals.
4. v1 references source version and fix plan.
5. `Comparison` uses the same `EvalContract` unless explicitly versioned.
6. `Comparison` identifies resolved failures, new failures, regressions, and readiness changes.

### Anti-patterns

- Do not make v1 an arbitrary rewrite.
- Do not remove failing scenarios to improve score.
- Do not change the eval contract silently.
- Do not ignore regressions introduced by the fix.

---

## Phase 7: Promote and Operate

### Goal

Apply gates, make a promotion decision, and optionally use the promoted agent operationally.

### Primary objects

- `GateResult`
- `ReadinessStatus`
- `PromotionRecord`
- `OperationalRun`
- `TraceLink`

### Step 7.1: Apply gates

Gates should distinguish behavior readiness from tool and operational readiness.

```yaml
gate_result:
  version: v1-evidence-triage-graph

  behavior_gate_status: pass
  production_readiness_status: blocked
  overall_status: pass_for_demo_not_production

  hard_behavior_gates:
    no_unsupported_root_cause: pass
    must_separate_facts_and_hypotheses: pass
    must_include_safe_next_actions: pass

  tool_readiness_gates:
    required_tools_available_for_demo: pass
    required_tools_available_for_production: fail

  blockers:
    - trace_evidence_source uses mock implementation.
    - recent_changes_source uses mock implementation.
    - tool_health_source uses mock implementation.
```

### Step 7.2: Promote or reject

Promotion states:

```text
draft
promoted_for_demo
promoted_for_internal_use
promoted_for_production_assistive_use
promoted_for_controlled_automation
rejected
deprecated
accepted_with_risk
```

```yaml
promotion_record:
  agent_id: customer-escalation-triage-agent
  promoted_version: v1-evidence-triage-graph
  previous_version: v0-baseline
  decision: promoted_for_demo
  production_status: blocked

  rationale: >
    v1 resolves the critical v0 failure of unsupported root-cause claims by adding
    explicit evidence collection, evidence normalization, and facts/hypotheses/unknowns
    separation. It passes behavior gates for the test scenario.

  conditions:
    - May be used for demo and offline evaluation.
    - May not be used for production escalation triage until live trace, recent-change,
      and tool-health connectors are implemented and reviewed.
```

### Step 7.3: Operate promoted agent

Operational use should preserve traceability.

An operational run should still reference:

- `Agent`
- `AgentVersion`
- `AgentTarget`
- `EvalContract`
- `ToolBinding`s
- `PromotionRecord`
- `TraceLink`s

The console should show tool mode and readiness status during operation.

Example warning:

```text
This version is promoted for demo only. It uses mock/local tools and is not
production-ready.
```

### Output

- `GateResult`s
- `ReadinessStatus`
- `PromotionRecord`
- `OperationalRun`
- `TraceLink`s

### Acceptance criteria

1. Behavior readiness and production readiness are evaluated separately.
2. Promotion is explicit and recorded.
3. Promotion rationale includes gate results and accepted risks.
4. Production readiness is blocked when required tools are mock-only or missing.
5. Operational runs reference active version, target, eval contract, and tool bindings.
6. Operational runs can link back to trace evidence.

### Anti-patterns

- Do not treat highest score as automatic promotion.
- Do not promote mock-only agents to production.
- Do not run operational agents without showing active version and tool mode.
- Do not allow write actions without approval unless the version is explicitly promoted for controlled automation.

---

## End-to-End Example

```text
User describes:
  Help FDEs triage customer AI deployment escalations.

Platform creates:
  AgentTarget, BehaviorRules, EvalContract,
  InformationRequirements, ToolRequirements, ToolFeasibilityReviews

Tool review finds:
  trace evidence source = mock only
  recent changes source = mock only
  tool health source = mock only

Lab creates:
  v0-baseline

v0 run shows:
  agent overclaimed root cause

Eval says:
  failed rule: separate_facts_from_hypotheses

FailurePacket says:
  v0 has no facts/hypotheses/unknowns step

FixPlan says:
  add evidence collection
  add evidence normalization
  add facts/hypotheses/unknowns node
  add customer-safe update review

Lab creates:
  v1-evidence-triage-graph

Comparison says:
  diagnostic grounding improved from 2 to 5
  unsupported root-cause failure resolved

Gate says:
  behavior gates pass
  production readiness blocked due to mock-only tools

Promotion says:
  promoted_for_demo
  not production-ready
```

This is the canonical EDD workflow.

---

## Workflow-Level Acceptance Criteria

Implementation is aligned with this HLD when:

1. A new agent can start from an `AgentTarget`, not only from code.
2. `BehaviorRule`s and `EvalContract`s are generated from target intent.
3. `InformationRequirement`s are generated before `ToolRequirement`s.
4. `ToolFeasibilityReview` makes missing or mock-only tools visible.
5. `GraphDesign` maps nodes to rules, information requirements, tools, or failures.
6. v0 can be run and evaluated against the active contract.
7. `FailurePacket`s tie failed rules to trace evidence and recommended fixes.
8. `FixPlan`s create bounded changes.
9. v1 can be compared against v0 using the same contract.
10. `GateResult`s distinguish behavior readiness from production readiness.
11. `PromotionRecord`s explicitly capture decision and rationale.
12. `OperationalRun`s preserve traceability to version, target, contract, tools, and traces.

---

## Summary

The EDD workflow is not just:

```text
run agent → score output → change prompt
```

It is:

```text
define intent
  → derive rules
  → derive evals
  → derive information needs
  → derive tool needs
  → check feasibility
  → shape graph
  → run baseline
  → capture evidence
  → diagnose failures
  → apply bounded fixes
  → compare versions
  → gate promotion
  → operate with traceability
```

Implementation work should preserve this lifecycle.

If a feature does not support this loop, it should be treated as secondary.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD-001](HLD-001-product-intent-and-system-boundaries.md) | eval-driven-design-platform | Product intent and system boundaries |
| [HLD-002](HLD-002-domain-object-model.md) | eval-driven-design-platform | Domain object model |
| [HLD-004](HLD-004-tool-requirements-and-feasibility.md) | eval-driven-design-platform | Tool requirements and feasibility |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Canonical reference scenario |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | MVP implementation plan |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Platform API and integration |
| [HLD index](README.md) | eval-driven-design-platform | HLD series overview |
| `docs/10-ideal-developer-experience.md` | edd-agent-lab | Target EDD lifecycle (narrative) |
| `docs/11-ideal-console-design.md` | edd-agent-lab | Console workspaces per phase |
| `EVAL_DRIVEN_DESIGN_PLAN.md` | eval-driven-design-platform | Phased build plan (current MVP) |
