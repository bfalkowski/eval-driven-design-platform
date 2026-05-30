# HLD-012: Versioning, Gates, and Promotion

## Status

Draft

## Purpose

This document defines how the **EDD stack** handles agent versions, gates, readiness, and promotion decisions.

The purpose of this HLD is to prevent a common failure mode:

```text
The newest or highest-scoring version is treated as the active version.
```

That is not sufficient for evaluation-driven design.

In the EDD stack, a version should be promoted only when there is an explicit decision record supported by eval results, trace evidence, resolved failures, gate results, tool readiness, and accepted risks.

See also:

- [HLD-002: Domain object model](HLD-002-domain-object-model.md) — `AgentVersion`, `Comparison`, `GateResult`, `PromotionRecord`, `ReadinessStatus`
- [HLD-004: Tool requirements and feasibility](HLD-004-tool-requirements-and-feasibility.md)
- [HLD-006: MVP implementation plan](HLD-006-mvp-implementation-plan.md)
- [HLD-007: Platform API and integration](HLD-007-platform-api-and-integration.md) — publish `gate_result`, `promotion_record`
- [HLD-011: Console information architecture](HLD-011-console-information-architecture.md) — Gates, Promotion, Versions screens

---

## Core Principle

A better score is not the same as a promotion decision.

A version should be promoted only when the platform can answer:

```text
What changed?
Why did it change?
Which failure did it address?
Which eval contract was used?
Which rules improved?
Which failures were resolved?
Were any regressions introduced?
Which gates passed?
Which gates failed?
Are required tools production-ready?
What risks are accepted?
For which environment is this version approved?
```

Promotion is a decision, not an automatic side effect of a run.

---

## Current Implementation (snapshot)

| Area | Today | Target (this HLD) |
|---|---|---|
| **AgentVersion** | `agent_version` string on publish envelope | Lifecycle + lineage objects |
| **Comparison** | Ad hoc / ingest JSON | Explicit `Comparison` with validity |
| **GateResult** | `gate_status` / `gate_explanation` from quality gate service | Behavior vs tool vs production split |
| **PromotionRecord** | Not first-class | Explicit artifact + API validation |
| **ReadinessStatus** | Partial in publish response (target) | Full multi-dimensional summary |
| **Auto-promotion** | None (good) | Manual or recommendation_only for MVP |
| **Console** | `6_Quality_Gates.py` | Version timeline, promotion screen (HLD-011) |

**Today:** `GET /v1/experiment-runs/{id}/gate` returns gate status from eval summary. Mock/local production blockers are target state.

---

## Version Lifecycle

Agent versions should move through an explicit lifecycle.

Recommended states:

```text
draft
candidate
evaluated
promoted
rejected
deprecated
```

| State | Meaning |
|---|---|
| **draft** | Version exists but has not been evaluated (e.g. v1 graph scaffold, no published run) |
| **candidate** | Ready for evaluation (e.g. `v1-evidence-triage-graph` implemented) |
| **evaluated** | At least one completed run and gate result |
| **promoted** | Explicit `PromotionRecord` (e.g. `promoted_for_demo`) |
| **rejected** | Evaluated and rejected (e.g. unsafe customer messaging) |
| **deprecated** | Superseded (e.g. v1 replaced by `v2-live-trace-reader`) |

---

## Version Identity

An `AgentVersion` should reference the design context it implements.

Example:

```yaml
agent_version:
  id: v1-evidence-triage-graph
  agent_id: customer-escalation-triage-agent
  source_version_id: v0-baseline
  target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  graph_design_id: customer-escalation-triage-graph-v1
  fix_plan_id: fix-v1-evidence-first-triage
  version_label: v1-evidence-triage-graph
  implementation_summary: >
    Adds evidence collection, evidence normalization, facts/hypotheses/unknowns
    separation, mitigation planning, and customer-safe update review.
  tool_mode_summary: mock_local
  status: candidate
```

A version should not be just a label or folder name.

It should connect to the target, eval contract, graph design, and source version.

---

## Version Lineage

Version lineage should be explicit.

```text
v0-baseline
  ↓
v1-evidence-triage-graph
  ↓
v2-live-trace-reader
```

Example:

```yaml
version_lineage:
  version: v1-evidence-triage-graph
  source_version: v0-baseline
  reason_created: >
    v0 failed the separate_facts_from_hypotheses rule by overclaiming root cause.
    v1 adds evidence normalization and facts/hypotheses separation.
  fix_plan_id: fix-v1-evidence-first-triage
  failure_packets_addressed:
    - fp-v0-unsupported-root-cause
```

This allows the platform console to tell a design story, not just a chronological history.

---

## Comparison Rules

Comparisons should be explicit platform objects.

A comparison should include:

```text
baseline version
candidate version
target
eval contract
scenario set
score deltas
resolved failures
new failures
regression warnings
tool readiness differences
trace links
summary
```

Example:

```yaml
comparison:
  id: compare-v0-v1-escalation-triage
  baseline_version_id: v0-baseline
  candidate_version_id: v1-evidence-triage-graph
  target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  scenario_set_id: escalation-core-scenarios

  score_delta:
    diagnostic_grounding:
      v0: 2
      v1: 5
      delta: 3
    customer_communication_quality:
      v0: 2
      v1: 5
      delta: 3

  resolved_failure_packet_ids:
    - fp-v0-unsupported-root-cause

  new_failure_packet_ids: []

  regression_warnings:
    - v1 has higher latency and token usage because it performs evidence normalization.

  tool_readiness_delta:
    v0: none
    v1: mock_local

  summary: >
    v1 improves because it separates facts, hypotheses, and unknowns instead of
    overclaiming root cause. It resolves the critical v0 failure but remains
    blocked for production because several required tools are mock/local only.
```

See [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md).

---

## Eval Contract Stability

A v0/v1 comparison should normally use the same eval contract.

If the eval contract changes, the platform must make that explicit.

| Bad | Good |
|---|---|
| v0 and v1 used different rubrics; console shows v1 is better without warning | Console marks comparison as not directly comparable |

Recommended comparison validity status:

```text
comparable
not_comparable_eval_contract_changed
not_comparable_scenario_set_changed
not_comparable_target_changed
```

Example (comparable):

```yaml
comparison_validity:
  status: comparable
  reason: >
    v0 and v1 were evaluated against the same target, eval contract, and scenario set.
```

Example (not comparable):

```yaml
comparison_validity:
  status: not_comparable_eval_contract_changed
  reason: >
    v1 used customer-escalation-triage-eval-contract-v2 while v0 used v1.
```

---

## Gate Categories

Gates should not be a single generic pass/fail.

The platform should distinguish gate categories:

```text
behavior
tool_readiness
operational_safety
regression
overfitting
cost
latency
promotion
```

### Behavior gates

Whether the agent satisfied the eval contract.

```yaml
behavior_gates:
  no_unsupported_root_cause: pass
  must_separate_facts_and_hypotheses: pass
  must_include_safe_next_actions: pass
  customer_update_must_be_safe: pass
```

### Tool readiness gates

Whether required tools exist at the required maturity level.

```yaml
tool_readiness_gates:
  required_tools_available_for_demo: pass
  required_tools_available_for_production: fail
```

### Operational safety gates

Whether the agent can safely be used in a real workflow.

```yaml
operational_safety_gates:
  no_write_actions_without_approval: pass
  customer_facing_messages_require_review: pass
```

### Regression gates

Whether the candidate got worse in important ways.

```yaml
regression_gates:
  no_behavior_regression: pass
  latency_regression_under_threshold: warning
  cost_regression_under_threshold: warning
```

### Overfitting gates

Whether improvement is too narrow or scenario-specific.

```yaml
overfitting_gates:
  scenario_variant_pass_rate: warning
```

For MVP, overfitting gates can be documented but not fully implemented.

---

## Gate Result

A `GateResult` should summarize behavior and readiness separately.

Example:

```yaml
gate_result:
  id: gate-v1-001
  agent_version_id: v1-evidence-triage-graph
  comparison_id: compare-v0-v1-escalation-triage

  behavior_gate_status: pass
  tool_readiness_status: mock_local
  operational_safety_status: pass
  production_readiness_status: blocked
  overall_status: pass_for_demo_not_production

  behavior_gates:
    no_unsupported_root_cause: pass
    must_separate_facts_and_hypotheses: pass
    must_include_safe_next_actions: pass
    customer_update_must_be_safe: pass

  tool_readiness_gates:
    required_tools_available_for_demo: pass
    required_tools_available_for_production: fail

  blockers:
    - trace_evidence_source uses mock implementation.
    - recent_changes_source uses mock implementation.
    - tool_health_source uses mock implementation.
    - eval_history_source uses local artifact implementation.
```

Important:

```text
behavior_gate_status = pass
does not imply
production_readiness_status = ready
```

---

## Readiness Status

`ReadinessStatus` should summarize the version across multiple dimensions.

Example:

```yaml
readiness_status:
  agent_version_id: v1-evidence-triage-graph

  behavior_status: pass
  tool_status: mock_local
  operational_status: demo_ready
  production_status: blocked
  promotion_status: promoted_for_demo

  blockers:
    - trace_evidence_source is mock-only.
    - recent_changes_source is mock-only.
    - tool_health_source is mock-only.
```

Recommended values:

| Field | Values |
|---|---|
| **behavior_status** | `not_run`, `pass`, `fail`, `warning` |
| **tool_status** | `missing`, `mock_only`, `local_only`, `mock_local`, `read_only_live`, `approval_gated`, `production_ready` |
| **operational_status** | `not_ready`, `demo_ready`, `internal_ready`, `production_assistive_ready`, `controlled_automation_ready` |
| **production_status** | `not_applicable`, `blocked`, `ready` |
| **promotion_status** | `draft`, `promoted_for_demo`, `promoted_for_internal_use`, `promoted_for_production_assistive_use`, `promoted_for_controlled_automation`, `rejected`, `deprecated`, `accepted_with_risk` |

---

## Promotion States

Promotion states should be more specific than promoted/not promoted.

| State | Meaning |
|---|---|
| **promoted_for_demo** | Demos and offline evaluation; mock/local tools allowed |
| **promoted_for_internal_use** | Internal use with read-only live tools; no uncontrolled writes |
| **promoted_for_production_assistive_use** | Production assist; live approved tools; approval-gated writes |
| **promoted_for_controlled_automation** | Bounded automation; strict gates, audit, rollback |
| **accepted_with_risk** | Known risks explicitly accepted |
| **rejected** | Failed required gates or unacceptable risk |
| **deprecated** | Superseded by a newer promoted version |

---

## Promotion Policy

Promotion decisions should consider behavior gates, tool readiness, operational safety, comparison validity, resolved/new failures, regressions, accepted risks, and intended environment.

Example policy (abbreviated):

```yaml
promotion_policy:
  promoted_for_demo:
    requires:
      - behavior_gate_status in [pass, warning]
      - required demo tools available as mock, local, or live
      - no critical unresolved behavior failures

  promoted_for_production_assistive_use:
    requires:
      - behavior_gate_status = pass
      - production_readiness_status = ready
      - required tools are live and approved
      - write actions are approval-gated
      - customer-facing communication gates pass
```

**MVP:** Fully support `promoted_for_demo`, `rejected`, and `accepted_with_risk`. Later states are documented for forward compatibility.

---

## Promotion Record

A promotion decision should be recorded explicitly.

Example:

```yaml
promotion_record:
  id: promotion-v1-demo
  agent_id: customer-escalation-triage-agent
  agent_version_id: v1-evidence-triage-graph
  previous_version_id: v0-baseline

  decision: promoted_for_demo
  production_status: blocked

  gate_result_ids:
    - gate-v1-001

  rationale: >
    v1 resolves the critical v0 failure of unsupported root-cause claims by adding
    evidence collection, evidence normalization, and facts/hypotheses/unknowns
    separation. It passes behavior gates for the reference scenario.

  accepted_risks:
    - v1 relies on mock/local tools.
    - v1 should not be used for production escalation triage.
    - mitigation recommendations require human approval.

  conditions:
    - May be used for demo and offline evaluation.
    - May not be used for production until live trace, recent-change, eval-history,
      and tool-health connectors are implemented and reviewed.

  decided_by: local_demo_user
  decided_at: 2026-05-30T10:30:00Z
```

A promotion record should be exportable as an artifact.

---

## Promotion Is Not Automatic

The platform may recommend promotion, but it should not silently promote a version unless explicitly configured.

Recommended modes:

```text
manual
recommendation_only
auto_promote_for_demo
```

**MVP:** `manual` or `recommendation_only`.

The console may show:

```text
Recommended decision: promoted_for_demo
Reason: behavior gates pass, production readiness blocked due to mock/local tools.
```

But the promotion record should still be explicit.

---

## Rejection Record

Rejected versions should also have a record.

Example:

```yaml
promotion_record:
  id: rejection-v1-unsafe-message
  agent_id: customer-escalation-triage-agent
  agent_version_id: v1-unsafe-message
  decision: rejected
  rationale: >
    The version improved diagnostic grounding but introduced a customer-facing
    update that exposed sensitive internal trace details.
  gate_result_ids:
    - gate-v1-unsafe-message
  blockers:
    - customer_update_must_be_safe failed
```

---

## Accepted With Risk

Example:

```yaml
promotion_record:
  decision: accepted_with_risk
  rationale: >
    v1 passes behavior gates but has a latency warning. The risk is accepted for
    demo use because the additional latency comes from evidence normalization and
    is acceptable in the demo context.
  accepted_risks:
    - v1 latency is higher than v0.
```

Accepted risk should never be implicit.

---

## Production Readiness Rules

Production readiness should require more than behavior success.

A version should not be production-ready if:

```text
required production tools are missing or mock/local only
write actions are not approval-gated
customer-facing messages are not reviewed or gated
critical behavior failures remain unresolved
comparison is not valid
```

Example (expected for Customer Escalation Triage MVP):

```yaml
production_readiness:
  status: blocked
  blockers:
    - trace_evidence_source is mock-only.
    - recent_changes_source is mock-only.
    - tool_health_source is mock-only.
```

---

## Demo Readiness Rules

Demo readiness is less strict.

A version can be demo-ready if:

```text
behavior gates pass or pass with acceptable warnings
mock/local tools are available
tool mode is clearly disclosed
no critical unresolved behavior failures remain
the console clearly labels production blockers
```

Example:

```yaml
demo_readiness:
  status: ready
  notes:
    - Uses mock/local tools.
    - Not production-ready.
```

---

## Version Comparison and Promotion Example

For the Customer Escalation Triage Agent:

```text
v0-baseline:
  single-pass prompt agent
  failed separate_facts_from_hypotheses
  overclaimed root cause

v1-evidence-triage-graph:
  added evidence collection, normalization, facts/hypotheses/unknowns separation
  passed behavior gates
  uses mock/local tools
  production blocked

decision: promoted_for_demo
```

Structured summary:

```yaml
promotion_summary:
  baseline_version: v0-baseline
  candidate_version: v1-evidence-triage-graph
  comparison: compare-v0-v1-escalation-triage
  behavior_result: pass
  tool_result: mock_local
  production_result: blocked
  decision: promoted_for_demo
```

---

## Console Requirements

The platform console should show:

```text
version lifecycle
version lineage
comparison validity
behavior gates
tool readiness gates
operational safety gates
production blockers
promotion recommendation
promotion decision record
accepted risks
```

### Version timeline

```text
v0-baseline
  Status: evaluated
  Gate: fail
  Main failure: unsupported root-cause claim

v1-evidence-triage-graph
  Status: promoted_for_demo
  Gate: pass_for_demo_not_production
  Main fix: facts/hypotheses separation
  Production blocker: mock/local tools
```

### Promotion screen

Minimum fields: decision, rationale, accepted risks, conditions, gate result references, decided by, decided at.

See [HLD-011](HLD-011-console-information-architecture.md).

---

## API Implications

The publish endpoint may include gate and promotion data.

```http
POST /v1/integrations/runs/publish
```

Relevant payload sections:

```json
{
  "gate_result": {
    "behavior_gate_status": "pass",
    "tool_readiness_status": "mock_local",
    "production_readiness_status": "blocked",
    "overall_status": "pass_for_demo_not_production"
  },
  "promotion_record": {
    "decision": "promoted_for_demo",
    "production_status": "blocked",
    "rationale": "v1 resolves unsupported root-cause claims but uses mock/local tools."
  }
}
```

The platform should validate that promotion decisions are consistent with readiness.

Bad payload: `promoted_for_production_assistive_use` with `production_readiness_status: blocked`.

Expected error:

```json
{
  "error": "promotion_readiness_conflict",
  "message": "Version cannot be promoted for production assistive use while production readiness is blocked."
}
```

See [HLD-007](HLD-007-platform-api-and-integration.md).

---

## Lab Artifact Requirements

The lab should produce:

```text
comparison-against-v0.json
gate-result.yaml
promotion-record.yaml
```

### gate-result.yaml

```yaml
gate_result:
  agent_version_id: v1-evidence-triage-graph
  behavior_gate_status: pass
  tool_readiness_status: mock_local
  production_readiness_status: blocked
  overall_status: pass_for_demo_not_production
```

### promotion-record.yaml

```yaml
promotion_record:
  agent_id: customer-escalation-triage-agent
  promoted_version: v1-evidence-triage-graph
  previous_version: v0-baseline
  decision: promoted_for_demo
  production_status: blocked
  rationale: >
    v1 resolves the critical v0 failure and passes behavior gates, but remains
    blocked for production because required tools are mock/local only.
```

Target path: `lab-runs/customer_escalation_triage/v1-evidence-triage-graph/` (HLD-006 M3).

---

## MVP Requirements

For MVP, implement:

1. `AgentVersion` status
2. `Comparison` artifact/object
3. `GateResult` artifact/object
4. `ReadinessStatus` calculation or summary
5. `PromotionRecord` artifact/object
6. Console display of version timeline
7. Console display of `pass_for_demo_not_production`
8. Validation that mock/local tools block production readiness

MVP promotion states:

```text
draft
promoted_for_demo
rejected
accepted_with_risk
deprecated
```

Later states: `promoted_for_internal_use`, `promoted_for_production_assistive_use`, `promoted_for_controlled_automation`.

---

## Anti-Patterns

### Anti-pattern: Highest score wins

| Bad | Good |
|---|---|
| v1 has the highest score, so it is active | v1 passes gates, resolves critical failures, and has an explicit PromotionRecord |

### Anti-pattern: Latest version wins

| Bad | Good |
|---|---|
| v2 exists, so v2 is active | v2 is a candidate until a promotion record makes it active for an environment |

### Anti-pattern: Behavior pass means production ready

| Bad | Good |
|---|---|
| v1 passed evals, so it is production-ready | v1 passed behavior gates but is production-blocked because required tools are mock/local |

### Anti-pattern: Invisible accepted risk

| Bad | Good |
|---|---|
| We know latency is worse, but we promoted anyway | PromotionRecord includes accepted risk: latency increased due to evidence normalization |

### Anti-pattern: Invalid comparison

| Bad | Good |
|---|---|
| v1 improved, but used a different eval contract | Comparison marked not directly comparable because eval contract changed |

---

## Acceptance Criteria for This HLD

Implementation is aligned with this HLD when:

1. `AgentVersion` lifecycle is explicit.
2. Version lineage is represented.
3. Comparisons reference baseline, candidate, target, eval contract, and scenario set.
4. Comparisons indicate whether they are valid/directly comparable.
5. `GateResult`s distinguish behavior, tool readiness, operational safety, and production readiness.
6. `ReadinessStatus` separates behavior status from production status.
7. `PromotionRecord` is required to mark a version promoted.
8. Promotion decisions include rationale and accepted risks.
9. Mock/local tools block production readiness.
10. Console shows `pass_for_demo_not_production` when appropriate.
11. Latest version is not automatically active.
12. Highest-scoring version is not automatically promoted.

---

## Summary

Versioning, gates, and promotion are central to the EDD stack.

The platform should not merely show:

```text
v0 score: 2.4
v1 score: 4.4
```

It should explain:

```text
v0 failed because it overclaimed root cause.
v1 addressed that failure by adding facts/hypotheses separation.
v1 passed behavior gates.
v1 uses mock/local tools.
Production readiness is blocked.
v1 is promoted for demo only.
```

That is the expected versioning and promotion story.

Promotion is not a score.

Promotion is an explicit, evidence-backed decision.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Reference gate/promotion payloads |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | End-to-end demo artifacts |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Publish gate/promotion fields |
| [HLD-009](HLD-009-architecture-and-flow-diagrams.md) | eval-driven-design-platform | Promotion flow (§10) |
| [HLD-011](HLD-011-console-information-architecture.md) | eval-driven-design-platform | Gates and Promotion screens |
| `docs/QUALITY_GATE_CI.md` | eval-driven-design-platform | Current gate CI |
