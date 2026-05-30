# HLD-011: Console Information Architecture

## Status

Draft

## Purpose

This document defines the information architecture for the **platform console**.

The purpose of this HLD is to prevent the platform console from becoming a generic dashboard. The console should reflect the evaluation-driven design workflow and make the relationship between intent, rules, tools, runs, failures, fixes, gates, and promotion visible.

The platform console should help users answer:

```text
What is this agent supposed to do?
Which rules define good behavior?
What information does the agent need?
Which tools are required?
Do those tools exist?
How is the graph shaped by the rules and tools?
How did v0 behave?
Where did v0 fail?
What evidence proves the failure?
What changed in v1?
Did v1 improve?
Is v1 safe to promote?
Can v1 be used operationally?
```

The platform console is the control-plane UI for the **EDD stack**.

See also:

- [HLD-003: Evaluation-driven design workflow](HLD-003-evaluation-driven-design-workflow.md)
- [HLD-006: MVP implementation plan](HLD-006-mvp-implementation-plan.md) — Milestone 5
- [HLD-010: Graph design and rule mapping](HLD-010-graph-design-and-rule-mapping.md)
- `docs/11-ideal-console-design.md` (edd-agent-lab) — narrative ideal state; this HLD is the canonical platform spec

---

## Core Principle

The console should follow the design lifecycle.

It should not be organized only around raw technical resources like files, traces, or runs.

The lifecycle is:

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

The console should make this lifecycle understandable.

---

## Current Implementation (snapshot)

Today the platform console is **EvalSpec-centric** (MVP Phases 0–8). Target lifecycle screens are planned.

| Target (HLD-011) | Today (Streamlit) | Notes |
|---|---|---|
| Overview | `1_Overview.py` | Langfuse health, ingest summary |
| Eval Contract | `2_Eval_Specs.py` | Maps to future EvalContract |
| Scenarios | `3_Eval_Cases.py` | Maps to Scenario |
| Runs | `4_Runs.py` | ExperimentRun + ingest JSON |
| Results | `5_Results_Explorer.py` | Scores, Langfuse links |
| Gates | `6_Quality_Gates.py` | Gate status from eval summary |
| Langfuse | `7_Langfuse.py` | Trace import |
| Operations | `8_Operations.py` | Placeholder / early ops |
| Target, Rules, Tool Feasibility, Graph Design, Failures, Promotion | Not yet | M5 / post-MVP |

MVP may use a **single-page Streamlit layout** with expandable sections before full navigation.

---

## Console Modes

The console should be organized into four major modes:

| Mode | Purpose |
|---|---|
| **Design** | Define what the agent should do |
| **Build** | Shape graph, prompts, tools, and versions |
| **Evaluate** | Run versions, inspect evidence, diagnose failures, compare |
| **Operate** | Use promoted agents with readiness and traceability |

Recommended top-level structure:

```text
Overview

Design
  Target
  Rules
  Eval Contract
  Information Requirements
  Tool Requirements
  Tool Feasibility

Build
  Graph Design
  Prompts
  Tool Bindings
  Versions

Evaluate
  Runs
  Traces
  Failure Packets
  Fix Plans
  Compare Versions
  Gates

Operate
  Live Run
  Action Queue
  Run History
  Promotion

Artifacts
Settings
```

For MVP, this can be implemented as a single Streamlit app with sections rather than a full multi-page application.

---

## Global Context Bar

The platform console should always show the current context.

Recommended fields:

```text
Agent
Target
Eval Contract
Agent Version
Tool Mode
Behavior Gate Status
Production Readiness
Promotion Status
Environment
```

Example:

```text
Agent: Customer Escalation Triage Agent
Target: customer-escalation-triage-target-v1
Eval Contract: customer-escalation-triage-eval-contract-v1
Version: v1-evidence-triage-graph
Tool Mode: mock_local
Behavior Gate: PASS
Production Readiness: BLOCKED
Promotion: promoted_for_demo
Environment: local_demo
```

The user should never wonder which target, version, or readiness context they are viewing.

---

## Status Model

The console should distinguish four kinds of status.

| Kind | Question |
|---|---|
| **Behavior readiness** | Did the agent satisfy the eval contract? |
| **Tool readiness** | Are required tools missing, mock, local, live, or action-capable? |
| **Production readiness** | Can this version be used in production? |
| **Promotion status** | What decision has been made about this version? |

Recommended status badges:

**Behavior:** `NOT RUN` · `PASS` · `FAIL` · `WARNING`

**Tool readiness:** `MISSING` · `MOCK_ONLY` · `LOCAL_ONLY` · `MOCK_LOCAL` · `READ_ONLY_LIVE` · `APPROVAL_GATED` · `PRODUCTION_READY`

**Production:** `NOT READY` · `BLOCKED` · `READY`

**Promotion:** `DRAFT` · `PROMOTED_FOR_DEMO` · `PROMOTED_FOR_INTERNAL_USE` · `PROMOTED_FOR_PRODUCTION_ASSISTIVE_USE` · `PROMOTED_FOR_CONTROLLED_AUTOMATION` · `REJECTED` · `DEPRECATED`

Important rule:

```text
Behavior PASS does not imply production READY.
```

---

## Overview Screen

### Purpose

Summarize the current state of the agent and tell the main EDD story.

### User questions

- What agent am I looking at?
- What is the active version?
- Did it pass behavior gates?
- Is it production-ready?
- What is the main unresolved blocker?
- What should I inspect next?

### Data shown

Agent summary, active target, active eval contract, active version, latest run, behavior gate status, tool readiness, production readiness, promotion status, main failure or blocker, v0/v1 score comparison.

### Example layout

```text
┌───────────────────────────────┬───────────────────────────────┐
│ Agent Target                  │ Active Version                │
│ Customer Escalation Triage    │ v1-evidence-triage-graph      │
│ Evidence-first triage         │ Adds facts/hypotheses split   │
└───────────────────────────────┴───────────────────────────────┘

┌───────────────┬───────────────┬───────────────┬────────────────┐
│ Behavior Gate │ Tool Mode     │ Prod Status   │ Promotion      │
│ PASS          │ MOCK_LOCAL    │ BLOCKED       │ DEMO           │
└───────────────┴───────────────┴───────────────┴────────────────┘

Main story:
v0 overclaimed root cause. v1 added evidence normalization and
facts/hypotheses separation. v1 passes behavior gates but remains blocked
for production because required tools are mock/local only.
```

### Actions

Open target, comparison, failure packet, gate result, trace, artifacts.

---

## Target Screen

### Purpose

Define what the agent is supposed to do.

### User questions

What is this agent for? Who uses it? What are its goals? What should it avoid? What risks matter?

### Data shown

`AgentTarget` ID, purpose, intended users, primary goals, non-goals, risk areas, expected output style, target version, target status.

### Actions

Create target, edit target, save target version, mark target active, generate rules, view target history.

**MVP:** Target editing can be file-backed or read-only. The key is displaying the target as the start of the workflow.

---

## Rules Screen

### Purpose

Show behavior expectations derived from the target.

### User questions

Which behaviors define success? Which rules are critical? Which rules failed? Which graph nodes support each rule?

### Data shown

`BehaviorRule` ID, name, description, severity, category, status, metrics using the rule, graph nodes supporting the rule, failure packets tied to the rule, latest pass/fail status.

### Example rule card

```text
Rule: separate_facts_from_hypotheses
Severity: Critical
Category: Grounding

Description:
The agent must distinguish confirmed facts from likely causes and unknowns.

Used by: diagnostic_grounding
Supported by: separate_facts_hypotheses_unknowns
Latest result: Failed in v0, passed in v1
```

### Actions

Add rule, edit rule, disable rule, view failures for rule, view graph nodes for rule, view traces for failed rule.

---

## Eval Contract Screen

### Purpose

Show how behavior rules become metrics and gates.

### User questions

How is this agent judged? Which metrics exist? Which gates can block promotion? Are v0 and v1 compared under the same contract?

### Data shown

`EvalContract` ID, version, metrics, scales, rubrics, behavior rules per metric, gates, scenario sets, active status.

### Example metric card

```text
Metric: diagnostic_grounding
Scale: 0-5
Rules: evidence_first_diagnosis, separate_facts_from_hypotheses
Gate: diagnostic_grounding >= 4
```

### Actions

Generate eval contract, edit rubric, preview evaluator prompt, attach scenario set, view score history, view gates.

**MVP:** Display metric-to-rule and gate-to-metric relationships at minimum.

---

## Information Requirements Screen

### Purpose

Show what information the agent needs to satisfy behavior rules.

### Data shown

`InformationRequirement` ID, name, description, required flag, sensitivity, behavior rules requiring it, tool requirements satisfying it.

### Example table

| Information Requirement | Required By Rules | Required | Sensitivity |
|---|---|---:|---|
| Customer report | evidence_first_diagnosis, assess_customer_impact | Yes | Internal |
| Trace evidence | evidence_first_diagnosis, separate_facts_from_hypotheses | Yes | Confidential |
| Recent changes | identify_recent_changes | Yes | Internal |
| Tool health | evidence_first_diagnosis, recommend_safe_next_actions | Yes | Internal |

### Actions

Generate information requirements, edit requirement, mark optional/required, map to tool requirement, view dependent rules.

---

## Tool Requirements Screen

### Purpose

Show what kind of tools are needed to satisfy information requirements.

### Data shown

`ToolRequirement` ID, suggested tool name, information requirement satisfied, purpose, access mode, required for demo/production, current implementation status.

### Example

```text
Tool Requirement: trace_evidence_source
Suggested tool: fetch_trace_summary
Access mode: read_only
Purpose: Retrieve trace-level evidence for the affected customer, workflow, and time period.
Required for demo: Yes
Required for production: Yes
```

### Actions

Generate tool requirements, create mock implementation, bind implementation, open feasibility review, mark production blocker.

---

## Tool Feasibility Screen

### Purpose

Make tool availability and readiness explicit.

### Example table

| Requirement | Suggested Tool | Status | Demo Ready | Production Ready | Blocker |
|---|---|---|---:|---:|---|
| Trace evidence | fetch_trace_summary | mock_only | Yes | No | Needs Langfuse API connector |
| Eval history | fetch_eval_results | local_only | Yes | No | Needs platform DB |
| Recent changes | fetch_recent_changes | mock_only | Yes | No | Needs GitHub/GitLab connector |
| Tool health | fetch_tool_health | mock_only | Yes | No | Needs metrics/logs connector |

### Required warning

If any required production tool is mock/local/missing:

```text
Production readiness is blocked because required tools are not live.
This version may be suitable for demo or offline evaluation only.
```

### Actions

Create connector task, approve demo readiness, mark production blocker, update feasibility, view affected gates.

See [HLD-004](HLD-004-tool-requirements-and-feasibility.md).

---

## Graph Design Screen

### Purpose

Show how rules, information requirements, tools, and failures shape the graph.

### Data shown

`GraphDesign` ID, graph version, source version, fix plan, graph nodes, rule/information/tool/failure mappings, tool mode per node.

### Example graph

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

Purpose, rules supported, information/tool requirements, active tool binding, tool mode, state read/write, prompt used, failures addressed.

### Actions

View node details, rule mapping, failure mapping, compare graph versions, open related fix plan.

See [HLD-010](HLD-010-graph-design-and-rule-mapping.md).

---

## Prompts Screen

### Purpose

Show prompt artifacts and how they map to graph nodes and rules.

### Data shown

Prompt ID, name, graph node, agent version, file path, content hash, purpose, rules supported, failure packets addressed.

### Actions

View prompt, compare prompt versions, open file path, preview prompt with scenario data.

**MVP:** Display and traceability sufficient; editing deferred.

---

## Tool Bindings Screen

### Purpose

Show the active tool implementation for each graph node and environment.

### Example table

| Graph Node | Requirement | Implementation | Mode | Environment |
|---|---|---|---|---|
| collect_trace_evidence | trace_evidence_source | fetch_trace_summary_mock | mock | local_demo |
| collect_eval_history | eval_history_source | fetch_eval_results_local | local | local_demo |
| collect_recent_changes | recent_changes_source | fetch_recent_changes_mock | mock | local_demo |
| collect_tool_health | tool_health_source | fetch_tool_health_mock | mock | local_demo |

### Actions

Switch binding, test tool, view sample output, open feasibility review.

---

## Versions Screen

### Purpose

Show agent evolution.

### Example timeline

```text
v0-baseline
  Single-pass prompt agent.
  Failed: unsupported root-cause claim.

v1-evidence-triage-graph
  Added evidence normalization and facts/hypotheses separation.
  Passed behavior gates.
  Promoted for demo.
  Production blocked due to mock/local tools.
```

### Actions

Open version, compare with previous, view runs, view graph, view promotion record.

---

## Runs Screen

### Purpose

Show experiment and evaluation runs.

### Data shown

`ExperimentRun` ID, agent version, target, eval contract, scenario set, environment, tool mode, status, timestamps, scores, trace links.

### Actions

Open run, open traces, view scores, view failure packets, publish run, compare run.

**Today:** `4_Runs.py` with ingest provenance columns.

---

## Traces Screen

### Purpose

Link platform objects to Langfuse evidence.

### Data shown

`TraceLink` ID, provider, external trace ID/URL, agent version, scenario, run, tool mode, environment, related failure packets and gate results.

### Actions

Open in Langfuse, attach to failure packet, attach to gate result, compare v0/v1 traces.

See [HLD-008](HLD-008-langfuse-integration.md).

---

## Failure Packets Screen

### Purpose

Turn failed rules into design evidence.

### Example

```text
Failure: Unsupported root-cause claim
Rule: separate_facts_from_hypotheses
Version: v0-baseline

Observed:
The agent stated the summarization prompt change was the likely cause.

Expected:
The agent should separate confirmed facts from hypotheses.

Recommended fix:
Add normalize_evidence and separate_facts_hypotheses_unknowns nodes.
```

### Actions

Create fix plan, mark resolved, accept risk, open trace, open related rule, open related graph node.

---

## Fix Plans Screen

### Purpose

Show bounded change proposals derived from failure packets.

### Data shown

`FixPlan` ID, source/target version, failure packets addressed, rules addressed, graph/prompt/tool changes, non-goals, regression risks, status.

### Actions

Create candidate version, approve fix plan, reject fix plan, open graph diff, open comparison.

---

## Compare Versions Screen

### Purpose

Show whether a candidate improved against the same eval contract.

### Required story

The reference comparison must show:

```text
v0 guessed the root cause.
v1 separated facts, hypotheses, and unknowns.
Diagnostic grounding improved from 2 to 5.
Unsupported root-cause failure was resolved.
Production readiness remains blocked because tools are mock/local.
```

### Actions

Open baseline/candidate traces, open resolved failure, open gate result, promote candidate, request changes.

---

## Gates Screen

### Purpose

Show behavior, tool readiness, operational safety, and production readiness decisions.

### Gate categories

```text
behavior
tool_readiness
operational_safety
regression
overfitting
cost
latency
```

### Example

```text
Behavior gates:
  no_unsupported_root_cause: PASS
  must_separate_facts_and_hypotheses: PASS

Tool readiness gates:
  required_tools_available_for_demo: PASS
  required_tools_available_for_production: FAIL

Overall: pass_for_demo_not_production
```

### Actions

View evidence, open trace, open tool feasibility, create fix plan, promote with warning, block promotion.

**Today:** `6_Quality_Gates.py`.

---

## Promotion Screen

### Purpose

Record explicit version decisions.

### Promotion states

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

### Actions

Promote for demo, promote for internal use, reject, accept with risk, deprecate previous version, export promotion record.

---

## Live Run Screen

### Purpose

Allow a promoted agent to be used operationally while preserving traceability and readiness context.

### Required warning

If the version is demo-only:

```text
This version is promoted for demo only. It uses mock/local tools and is not
production-ready.
```

### Actions

Run agent, save operational run, open trace, create action item, draft message, approve/reject action, run post-hoc eval.

**MVP:** Live operation can be deferred until the core eval loop works.

---

## Action Queue Screen

### Purpose

Manage recommended actions that require human approval.

**MVP:** Can be deferred.

---

## Run History Screen

### Purpose

Show experiment and operational runs over time.

### Actions

Open run, compare runs, open traces, export run record.

---

## Artifacts Screen

### Purpose

Show file-level outputs from the platform or lab.

### Example artifacts

```text
agent-target.yaml
behavior-rules.yaml
eval-contract.yaml
information-requirements.yaml
tool-requirements.yaml
tool-feasibility.yaml
tool-bindings.yaml
graph-design.yaml
eval-summary.json
failure-packets/*.yaml
fix-plan.yaml
comparison.json
gate-result.yaml
promotion-record.yaml
trace-links.json
```

### Actions

View artifact, copy, download, open in repo, compare versions.

---

## Settings Screen

### Purpose

Manage platform configuration: API endpoints, Langfuse, default environment/tool mode, evaluator/model config, thresholds, approval policy.

### Actions

Update setting, test connection, validate configuration.

---

## MVP Console Scope

Required MVP sections:

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

Optional or later: Prompts, Tool Bindings, Traces, Live Run, Action Queue, Run History, Settings.

Single-page Streamlit section order:

```text
1. Overview
2. Design Intent
3. Rules and Eval Contract
4. Information and Tool Requirements
5. Tool Feasibility
6. Graph Design
7. v0 Failure
8. v1 Fix and Comparison
9. Gates and Promotion
10. Artifacts
```

See [HLD-006 Milestone 5](HLD-006-mvp-implementation-plan.md).

---

## Empty States

The console should guide users through missing data.

| Missing | Message |
|---|---|
| No target | No agent target exists yet. Start by describing what this agent should do. |
| No eval contract | No eval contract exists for this target. Generate behavior rules and eval metrics from the active target. |
| No tool feasibility | Tool requirements exist, but feasibility has not been reviewed. Production readiness cannot be determined. |
| No run | No runs have been published for this version. Run the agent in edd-agent-lab and publish the result. |

---

## Console Anti-Patterns

### Anti-pattern: Generic dashboard

| Bad | Good |
|---|---|
| Runs, Scores, Traces, Files | Target, Rules, Eval Contract, Tool Feasibility, Failures, Gates, Promotion |

### Anti-pattern: Hidden tool mode

| Bad | Good |
|---|---|
| v1 passed | v1 passed behavior gates but uses mock/local tools and is blocked for production |

### Anti-pattern: Score-only comparison

| Bad | Good |
|---|---|
| v0: 2.4, v1: 4.4 | v1 resolved fp-v0-unsupported-root-cause by adding facts/hypotheses separation |

### Anti-pattern: Promotion inferred from latest run

| Bad | Good |
|---|---|
| Latest run is active | PromotionRecord explicitly marks v1 as promoted_for_demo |

---

## Acceptance Criteria for This HLD

Implementation is aligned with this HLD when:

1. The console follows the EDD lifecycle, not a generic dashboard structure.
2. The global context bar shows agent, target, eval contract, version, tool mode, and readiness.
3. Behavior readiness and production readiness are displayed separately.
4. The console shows `AgentTarget` before run results.
5. Rules map to metrics, graph nodes, and failures.
6. `InformationRequirement`s and `ToolRequirement`s are visible.
7. `ToolFeasibility` makes mock/local/live status visible.
8. `GraphDesign` explains why nodes exist.
9. `FailurePacket`s connect failed rules to evidence and recommended fixes.
10. Compare Versions explains resolved failures and regressions, not only score deltas.
11. Gates distinguish behavior, tool readiness, and operational safety.
12. Promotion is shown as an explicit decision record.
13. The reference scenario can be understood without reading raw files.

---

## Summary

The platform console is the user-facing expression of the EDD workflow.

It should make this story visible:

```text
The agent had a target.
The target produced rules.
The rules produced an eval contract.
The rules also produced information and tool requirements.
Tool feasibility showed some tools were mock/local.
v0 failed a rule.
The failure packet identified the missing graph behavior.
The fix plan introduced bounded changes.
v1 improved against the same eval contract.
Gates passed for behavior.
Production readiness remained blocked.
The version was promoted for demo only.
```

If the console tells that story clearly, it is aligned with the product intent.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Reference console story |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | M5 console MVP |
| [HLD-009](HLD-009-architecture-and-flow-diagrams.md) | eval-driven-design-platform | Console information flow (§11) |
| [HLD-010](HLD-010-graph-design-and-rule-mapping.md) | eval-driven-design-platform | Graph Design screen |
| [HLD-012](HLD-012-versioning-gates-and-promotion.md) | eval-driven-design-platform | Gates and Promotion screens |
| `docs/11-ideal-console-design.md` | edd-agent-lab | Ideal-state narrative |
| `docs/DEMO_SCRIPT.md` | eval-driven-design-platform | Current operator walkthrough |
