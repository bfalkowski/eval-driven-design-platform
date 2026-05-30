# HLD-001: Product Intent and System Boundaries

## Status

Draft

## Purpose

This document defines the product intent and system boundaries for the **EDD stack**: **eval-driven-design-platform** and **edd-agent-lab**.

The purpose of this HLD is to keep implementation work aligned with the core product idea. The stack should not drift into being only an eval dashboard, only a LangGraph playground, or only a wrapper around Langfuse.

The EDD stack is an evaluation-driven design system for AI agents.

It connects design intent, evaluation criteria, required information, tool feasibility, graph design, runtime traces, failure diagnosis, bounded fixes, version comparison, gates, promotion, and operational use.

---

## Core Product Thesis

Most AI agent development starts with a prompt or graph implementation. Teams build something, run it, inspect the output, and then adjust based on intuition.

The EDD stack starts earlier.

The product begins with a definition of what the agent is supposed to do. That definition is turned into behavioral rules, eval contracts, information requirements, tool requirements, graph design, trace-backed evidence, failure packets, bounded fixes, and promotion decisions.

The ideal loop is:

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

Evaluation is not a final reporting layer.

Evaluation is part of the design process.

---

## What the EDD Stack Is

The EDD stack is a system for designing, evaluating, improving, and operating AI agents with evidence.

It should help developers answer:

- What is this agent supposed to do?
- What does good behavior mean?
- What information does the agent need?
- What tools would provide that information?
- Do those tools actually exist?
- How should the graph be shaped by the rules and available tools?
- How did the agent behave?
- Where did it fail?
- What evidence proves the failure?
- What should change?
- Did the new version improve?
- Is the version safe to promote?
- Can this version be used operationally?

The EDD stack should make agent development more traceable, repeatable, and disciplined.

---

## What the EDD Stack Is Not

### Not just an eval dashboard

An eval dashboard shows scores. The platform should explain how those scores relate to target behavior, graph design, failure packets, fix plans, gates, and promotion decisions.

### Not just a LangGraph playground

A LangGraph playground lets users build and run graphs. The stack should explain why a graph has certain nodes, which rules those nodes support, which tools they require, and which failures they address.

### Not a Langfuse replacement

Langfuse is the trace and observability layer. The platform should use Langfuse for evidence, but the platform should own the design workflow and meaning of that evidence.

### Not a system that pretends tools exist

When a graph needs information, the platform should distinguish information requirements, suggested tool requirements, actual implementations, active bindings, and feasibility. A suggested tool is not the same as an available production connector.

### Not an automatic production agent deployer

Promotion to demo, internal use, production assistive use, or controlled automation should be explicit and gate-driven. Passing evals with mock tools is not the same as being production-ready.

---

## Product Principles

### 1. Start with intent

The first major artifact should be an agent target.

The user may begin with plain language:

```text
I want an agent that helps FDEs triage customer escalations for AI deployments.
It should look at traces, eval results, recent changes, tool failures, and
customer reports. It should identify likely causes, recommend safe next actions,
and draft a customer-safe update. It must not invent root causes.
```

The system should turn that into a structured target contract.

### 2. Turn intent into rules

The target should generate behavior rules.

Example:

```text
Rule:
  separate_facts_from_hypotheses

Meaning:
  The agent must distinguish confirmed facts from likely causes and unknowns.

Severity:
  critical
```

Rules should be first-class objects. They should connect to eval metrics, graph nodes, failure packets, and gates.

### 3. Turn rules into eval contracts

The eval contract defines how agent behavior is judged.

Example:

```text
Metric:
  diagnostic_grounding

Rules:
  evidence_first_diagnosis
  separate_facts_from_hypotheses

Gate:
  diagnostic_grounding >= 4
```

The eval contract should exist before a version is accepted as good.

### 4. Derive information requirements before tools

Before recommending tools, the system should identify what information the agent needs.

Example:

```text
Information requirement:
  trace_evidence

Needed for rules:
  evidence_first_diagnosis
  separate_facts_from_hypotheses

Description:
  Recent traces, model calls, tool calls, latency, failed spans, and error patterns.
```

This prevents the system from jumping too quickly to fantasy tools.

### 5. Treat tools as requirements until proven available

The platform may suggest a tool such as `fetch_trace_summary`, but that does not mean it exists.

The system must track:

| Concept | Meaning |
|---|---|
| **InformationRequirement** | What information is needed. |
| **ToolRequirement** | What kind of tool could provide that information. |
| **ToolImplementation** | A concrete mock, local, or live implementation. |
| **ToolBinding** | Which implementation is active for a graph node or environment. |
| **ToolFeasibilityReview** | Whether the tool is realistic for demo, internal, or production use. |

### 6. Let rules and tools shape the graph

LangGraph nodes should not be arbitrary.

Every significant node should exist because of at least one of the following:

- behavior rule
- information requirement
- tool requirement
- failure packet
- fix plan
- operational safety requirement

Example:

```text
Rule:
  separate_facts_from_hypotheses

Graph impact:
  add normalize_evidence
  add separate_facts_hypotheses_unknowns
```

### 7. Treat failure packets as design evidence

A failure packet should connect:

- failed rule
- scenario
- observed behavior
- expected behavior
- trace evidence
- suspected cause
- recommended bounded fix

The product should avoid vague feedback like “make the agent better.”

It should produce bounded guidance like:

```text
v0 overclaimed root cause.
This violates separate_facts_from_hypotheses.
Add a facts/hypotheses/unknowns node before mitigation planning.
```

### 8. Distinguish behavior quality from production readiness

An agent can pass behavior gates while still being blocked for production.

Example:

```text
v1 passes evals using mock trace and tool-health data.
Promotion: promoted_for_demo.
Production readiness: blocked.
Reason: trace and recent-change tools are mock-only.
```

This distinction is central to the product’s credibility.

---

## System Roles

The EDD stack should be understood as a three-part system.

```text
eval-driven-design-platform
  owns design intent, workflow state, gates, decisions, and canonical objects

edd-agent-lab
  owns runnable LangGraph implementations, local artifacts, mock tools, and agent versions

Langfuse
  owns trace evidence, spans, generations, scores, cost, latency, and annotations
```

Each system has a distinct responsibility.

---

## eval-driven-design-platform Responsibilities

The platform owns the canonical workflow and product meaning.

It should own:

```text
Agent
AgentTarget
BehaviorRule
EvalContract
Metric
Gate
Scenario
ScenarioSet
InformationRequirement
ToolRequirement
ToolImplementation
ToolBinding
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
OperationalRun
ReadinessStatus
Artifact
```

The platform should answer:

- What is this agent supposed to do?
- Which rules define good behavior?
- Which eval contract is active?
- Which information does the agent need?
- Which tools are missing or mock-only?
- Which version is being evaluated?
- Which gates passed or failed?
- Which failures were resolved?
- Which version was promoted?
- What is the operational readiness status?

The platform should not rely on Langfuse as the source of truth for design intent, gates, or promotion.

---

## edd-agent-lab Responsibilities

The lab owns concrete implementation and local development.

It should own:

```text
LangGraph code
agent prompts
mock tool implementations
local tool bindings
local scenario runners
local eval runners
versioned implementation folders
local run outputs
generated artifacts
side-by-side development views
```

The lab should be able to run independently for local development and demos.

When connected to the platform, the lab should publish runs, artifacts, scores, failure packets, and trace links back to the platform.

The lab should not become the canonical product database.

---

## Langfuse Responsibilities

Langfuse owns runtime evidence.

It should provide:

- traces
- spans
- generations
- model inputs
- model outputs
- tool calls
- latency
- cost
- token usage
- scores
- datasets
- experiments
- annotations

Every Langfuse trace created or linked by the platform should include platform metadata.

Example:

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

Langfuse should support trace inspection, debugging, scores, and evidence.

It should not own promotion decisions, target contracts, or tool feasibility.

---

## Repository Boundaries

### eval-driven-design-platform

The platform repo should contain the canonical product services and UI.

It should include:

- domain model
- API endpoints
- database persistence
- target/rule/eval workflows
- tool feasibility workflows
- run registry
- comparison registry
- gate execution
- promotion records
- console UI
- integration with Langfuse
- integration bridge for edd-agent-lab

The platform is the source of truth for workflow state.

### edd-agent-lab

The lab repo should contain runnable agent examples and local iteration artifacts.

It should include:

- agent implementations
- LangGraph definitions
- mock data
- mock tools
- prompt files
- local run scripts
- local eval scripts
- versioned lab runs
- artifact export/publish logic

The lab is where concrete agents are built and evolved.

### Langfuse

Langfuse is an external observability/evaluation system.

The platform should integrate with Langfuse but should not duplicate all Langfuse capabilities.

---

## Integration Boundary

The primary integration between the lab and the platform should be a publish bridge.

Primary endpoint:

```http
POST /v1/integrations/runs/publish
```

Legacy alias (deprecated):

```http
POST /v1/integrations/lab/publish
```

The lab should send:

- agent id
- target id
- eval contract id
- version id
- scenario set id
- tool binding mode
- run output
- eval summary
- trace links
- failure packets
- artifacts

The platform should return:

- platform_run_id
- gate_result_id
- comparison_id
- readiness_status
- promotion_status
- artifact links

Running both repos locally is not the same as integration.

They are integrated only when lab runs can be registered in the platform, linked to canonical platform objects, and traced through Langfuse evidence.

See `edd-agent-lab/docs/05-platform-integration.md` for the current publish envelope and client modes.

---

## Required Readiness Distinctions

The platform should distinguish at least four kinds of readiness.

### Behavior readiness

Does the agent satisfy the eval contract?

Example:

```text
diagnostic_grounding >= 4
no unsupported root-cause claims
safe customer update generated
```

### Tool readiness

Are required tools available at the needed maturity level?

Example:

```text
trace evidence source: mock only
recent changes source: missing
eval history source: local artifact
```

### Operational readiness

Can the promoted version be used for real workflows?

Example:

```text
promoted_for_demo
promoted_for_internal_use
promoted_for_production_assistive_use
promoted_for_controlled_automation
```

### Promotion readiness

Should this version become the active version for a particular environment?

Example:

```text
v1 passes behavior gates
v1 is blocked for production
v1 may be promoted for demo only
```

These distinctions must not be collapsed.

---

## Promotion States

Recommended promotion states:

```text
draft
promoted_for_demo
promoted_for_internal_use
promoted_for_production_assistive_use
promoted_for_controlled_automation
rejected
deprecated
```

Important rule:

```text
Passing evals with mock tools can justify promoted_for_demo.
It must not justify promoted_for_production_assistive_use.
```

---

## Example Product Story

The canonical reference story is the Customer Escalation Triage Agent.

```text
User defines:
  Help FDEs triage customer AI deployment escalations.

Platform generates:
  target, behavior rules, eval contract, information requirements, tool requirements.

Tool review finds:
  trace evidence, eval history, recent changes, and tool health are needed.
  some tools are mock-only.

Lab creates:
  v0 baseline prompt agent.

v0 fails:
  It guesses the root cause and overclaims that a prompt change caused the issue.

Failure packet says:
  Failed rule: separate_facts_from_hypotheses.
  Suspected cause: no evidence normalization or facts/hypotheses/unknowns step.

Fix plan says:
  Add collect_evidence, normalize_evidence, and separate_facts_hypotheses_unknowns nodes.

Lab creates:
  v1 evidence-first triage graph.

v1 passes:
  Behavior gates.

Platform decides:
  promoted_for_demo.
  production readiness blocked because required tools are mock-only.
```

This story should guide implementation.

---

## Anti-Goals for Coding Agents

Coding agents working on this project should avoid the following mistakes.

### Do not build a generic dashboard first

The console should reflect the EDD lifecycle.

Screens should be organized around target, rules, eval contract, information requirements, tool requirements, graph design, runs, traces, failure packets, fix plans, comparisons, gates, promotion, and operation.

### Do not collapse tool concepts

Do not combine ToolRequirement, ToolImplementation, ToolBinding, and ToolFeasibilityReview into one generic “Tool” concept.

These are different domain concepts.

### Do not make Langfuse the source of truth

Langfuse stores trace evidence.

The platform owns design intent, eval contracts, gates, fix plans, and promotion decisions.

### Do not skip information requirements

The system should identify information needs before suggesting tools.

### Do not promote production readiness with mock tools

Mock tools are acceptable for demos and eval loops.

They are not sufficient for production readiness.

### Do not let v1 be an arbitrary rewrite

v1 should be traceable to v0 failures through failure packets and fix plans.

### Do not change the eval contract silently between v0 and v1

If the eval contract changes, it should be versioned and explicit.

Comparisons should normally use the same eval contract unless the user intentionally changes it.

---

## Acceptance Criteria for This HLD

Implementation work is aligned with this HLD when:

1. The system starts from an AgentTarget, not only from an agent implementation.
2. BehaviorRules and EvalContracts are first-class concepts.
3. InformationRequirements are generated before ToolRequirements.
4. Tool feasibility is represented explicitly.
5. GraphDesign can be traced back to rules, information needs, tools, or failures.
6. Runs are associated with target, eval contract, version, scenario, and tool mode.
7. FailurePackets connect failed rules to trace evidence and recommended fixes.
8. FixPlans produce bounded changes from failure packets.
9. Comparisons explain why one version improved or regressed.
10. GateResults distinguish behavior readiness from tool and production readiness.
11. PromotionRecords preserve the reason a version was promoted, rejected, or accepted with risk.
12. Langfuse is used for evidence, not as the source of product truth.

---

## Summary

The EDD stack is an evaluation-driven design system for AI agents.

Its core value is connecting:

```text
intent
rules
evals
information needs
tools
tool feasibility
graph design
runtime evidence
failures
fixes
versions
gates
promotion
operation
```

The product should make agent improvement explainable.

Not:

```text
We changed the prompt and the score went up.
```

But:

```text
v0 failed the rule separate_facts_from_hypotheses.
The trace showed it overclaimed root cause.
The fix plan added evidence normalization and facts/hypotheses separation.
v1 passed the behavior gate.
Production readiness remains blocked because trace and tool-health connectors are mock-only.
```

That is the design intent all implementation work should preserve.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD index](README.md) | eval-driven-design-platform | HLD series overview |
| [HLD-002](HLD-002-domain-object-model.md) | eval-driven-design-platform | Domain object model |
| [HLD-003](HLD-003-evaluation-driven-design-workflow.md) | eval-driven-design-platform | Canonical EDD workflow |
| [HLD-004](HLD-004-tool-requirements-and-feasibility.md) | eval-driven-design-platform | Tool requirements and feasibility |
| [HLD-005](HLD-005-reference-scenario-customer-escalation-triage.md) | eval-driven-design-platform | Canonical reference scenario |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | MVP implementation plan |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Platform API and integration |
| [HLD-008](HLD-008-langfuse-integration.md) | eval-driven-design-platform | Langfuse integration |
| [HLD-009](HLD-009-architecture-and-flow-diagrams.md) | eval-driven-design-platform | Architecture diagrams |
| [HLD-010](HLD-010-graph-design-and-rule-mapping.md) | eval-driven-design-platform | Graph design and rule mapping |
| [HLD-011](HLD-011-console-information-architecture.md) | eval-driven-design-platform | Console information architecture |
| [HLD-012](HLD-012-versioning-gates-and-promotion.md) | eval-driven-design-platform | Versioning, gates, and promotion |
| `EVAL_DRIVEN_DESIGN_PLAN.md` | eval-driven-design-platform | Phased build plan |
| `docs/PRODUCT_VISION.md` | eval-driven-design-platform | Product vision |
| `docs/10-ideal-developer-experience.md` | edd-agent-lab | Target EDD lifecycle |
| `docs/11-ideal-console-design.md` | edd-agent-lab | Target platform console UX |
| `docs/05-platform-integration.md` | edd-agent-lab | Publish seam and client modes |
