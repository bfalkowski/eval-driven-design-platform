# HLD-005: Reference Scenario — Customer Escalation Triage

## Status

Draft

## Purpose

This document defines the canonical reference scenario for the **EDD stack**.

The purpose of this HLD is to give implementation agents one complete example that exercises the full evaluation-driven design workflow:

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

This scenario should be used as the primary reference example when building platform objects, APIs, console screens, lab artifacts, and tests.

If a feature cannot support this scenario, it probably does not support the intended EDD workflow.

See also:

- [HLD-003: Evaluation-Driven Design Workflow](HLD-003-evaluation-driven-design-workflow.md)
- [HLD-004: Tool Requirements and Feasibility](HLD-004-tool-requirements-and-feasibility.md)

---

## Scenario Summary

The reference agent is the **Customer Escalation Triage Agent**.

The agent helps Forward Deployed Engineers and platform engineers triage customer escalations for AI deployments.

The core behavior is:

> Given a messy customer escalation, the agent should synthesize customer reports, trace evidence, eval results, recent changes, and tool health into a grounded diagnosis and action plan.

The agent must avoid overclaiming. It should separate confirmed facts from hypotheses and unknowns.

---

## Why This Scenario

This scenario is a strong reference example because it exercises the most important parts of the EDD stack.

It requires:

- target definition
- behavior rules
- eval contract
- information requirements
- tool requirements
- tool feasibility
- mock tools
- graph design
- v0 failure
- failure packet
- bounded fix
- v1 graph improvement
- v0/v1 comparison
- behavior gates
- tool readiness gates
- promotion decision

It also fits the intended platform/FDE use case: production-like AI systems, customer impact, traces, evals, recent changes, tool reliability, and safe communication.

---

## Initial User Request

The user starts with a plain-language request.

```text
I want an agent that helps FDEs triage customer escalations for AI deployments.
It should look at traces, eval results, recent changes, tool failures, and customer reports.
It should identify likely causes, recommend safe next actions, and help draft a customer update.
It must not invent root causes or blame systems without evidence.
```

From this, the platform should generate the first design artifacts.

---

## Agent

```yaml
agent:
  id: customer-escalation-triage-agent
  name: Customer Escalation Triage Agent
  description: >
    Helps Forward Deployed Engineers triage customer escalations for AI deployments
    by synthesizing customer reports, traces, eval results, recent changes, and
    tool health into a grounded diagnosis and action plan.
```

---

## Agent Target

```yaml
agent_target:
  id: customer-escalation-triage-target-v1
  agent_id: customer-escalation-triage-agent
  version: v1
  name: Customer Escalation Triage Target

  purpose: >
    Help Forward Deployed Engineers triage customer escalations in AI deployments
    by synthesizing customer reports, traces, eval results, recent changes, and
    tool health into a grounded diagnosis and action plan.

  intended_users:
    - Forward Deployed Engineers
    - Platform Engineers
    - Customer deployment leads
    - AI support engineers

  primary_goals:
    - Summarize the customer-reported problem.
    - Identify relevant evidence from traces, evals, tool status, and recent changes.
    - Separate confirmed facts from hypotheses.
    - Identify likely root-cause candidates without overclaiming.
    - Recommend immediate mitigation steps.
    - Recommend follow-up investigation steps.
    - Draft a customer-safe status update.

  non_goals:
    - Do not claim a confirmed root cause without evidence.
    - Do not blame the customer, model provider, or internal team prematurely.
    - Do not expose sensitive trace details in a customer-facing message.
    - Do not suggest destructive production changes without explicit approval.

  risk_areas:
    - Unsupported root-cause claims
    - Customer-facing speculation
    - Exposure of sensitive trace data
    - Unsafe production actions
    - Ignoring tool failures or recent changes
```

---

## Behavior Rules

```yaml
behavior_rules:
  - id: evidence_first_diagnosis
    agent_target_id: customer-escalation-triage-target-v1
    name: Evidence-first diagnosis
    severity: critical
    category: evidence
    description: >
      The agent must base diagnosis on available evidence from traces, evals,
      recent changes, customer reports, and tool health.

  - id: separate_facts_from_hypotheses
    agent_target_id: customer-escalation-triage-target-v1
    name: Separate facts from hypotheses
    severity: critical
    category: grounding
    description: >
      The agent must distinguish confirmed facts from likely causes and unknowns.

  - id: identify_recent_changes
    agent_target_id: customer-escalation-triage-target-v1
    name: Identify recent changes
    severity: high
    category: evidence
    description: >
      The agent must check whether recent prompts, model settings, tools, configs,
      deployments, or data changes correlate with the issue.

  - id: assess_customer_impact
    agent_target_id: customer-escalation-triage-target-v1
    name: Assess customer impact
    severity: high
    category: planning
    description: >
      The agent must describe customer impact, affected workflows, severity,
      and urgency where evidence is available.

  - id: recommend_safe_next_actions
    agent_target_id: customer-escalation-triage-target-v1
    name: Recommend safe next actions
    severity: high
    category: operations
    description: >
      The agent must recommend safe, sequenced mitigation and investigation steps.

  - id: draft_customer_safe_update
    agent_target_id: customer-escalation-triage-target-v1
    name: Draft customer-safe update
    severity: medium
    category: communication
    description: >
      The agent should produce a concise customer-facing update that avoids
      speculation and sensitive internal details.
```

---

## Eval Contract

```yaml
eval_contract:
  id: customer-escalation-triage-eval-contract-v1
  agent_target_id: customer-escalation-triage-target-v1
  version: v1
  name: Customer Escalation Triage Eval Contract

  metrics:
    - id: diagnostic_grounding
      name: Diagnostic grounding
      scale_min: 0
      scale_max: 5
      behavior_rule_ids:
        - evidence_first_diagnosis
        - separate_facts_from_hypotheses
      rubric: >
        Scores whether the agent bases diagnosis on evidence and clearly
        separates confirmed facts from hypotheses and unknowns.

    - id: change_correlation_quality
      name: Change correlation quality
      scale_min: 0
      scale_max: 5
      behavior_rule_ids:
        - identify_recent_changes
      rubric: >
        Scores whether the agent considers recent prompts, configs, deployments,
        tools, models, or data changes as possible contributing factors without
        overclaiming causality.

    - id: impact_assessment_quality
      name: Impact assessment quality
      scale_min: 0
      scale_max: 5
      behavior_rule_ids:
        - assess_customer_impact
      rubric: >
        Scores whether the agent summarizes customer impact, affected workflows,
        urgency, and severity based on available evidence.

    - id: action_plan_quality
      name: Action plan quality
      scale_min: 0
      scale_max: 5
      behavior_rule_ids:
        - recommend_safe_next_actions
      rubric: >
        Scores whether the agent recommends safe, sequenced mitigation and
        investigation steps.

    - id: customer_communication_quality
      name: Customer communication quality
      scale_min: 0
      scale_max: 5
      behavior_rule_ids:
        - draft_customer_safe_update
      rubric: >
        Scores whether the customer-facing update is clear, honest, non-speculative,
        and avoids sensitive internal details.

  gates:
    - id: no_unsupported_root_cause
      name: No unsupported root cause
      type: hard
      category: behavior
      condition: diagnostic_grounding >= 4

    - id: must_separate_facts_and_hypotheses
      name: Must separate facts and hypotheses
      type: hard
      category: behavior
      condition: diagnostic_grounding >= 4

    - id: must_include_safe_next_actions
      name: Must include safe next actions
      type: hard
      category: behavior
      condition: action_plan_quality >= 4

    - id: customer_update_must_be_safe
      name: Customer update must be safe
      type: warning
      category: behavior
      condition: customer_communication_quality >= 4

    - id: required_tools_available_for_production
      name: Required tools available for production
      type: hard
      category: tool_readiness
      condition: all required production tools have approved live implementations
```

---

## Information Requirements

```yaml
information_requirements:
  - id: customer_report
    agent_target_id: customer-escalation-triage-target-v1
    name: Customer report
    required: true
    sensitivity: internal
    behavior_rule_ids:
      - evidence_first_diagnosis
      - assess_customer_impact
    description: >
      The customer-provided report of the problem, including affected workflows,
      reported symptoms, timing, and urgency.

  - id: trace_evidence
    agent_target_id: customer-escalation-triage-target-v1
    name: Trace evidence
    required: true
    sensitivity: confidential
    behavior_rule_ids:
      - evidence_first_diagnosis
      - separate_facts_from_hypotheses
    description: >
      Recent traces for the affected workflow, including model calls, tool calls,
      latency, failed spans, and error patterns.

  - id: eval_history
    agent_target_id: customer-escalation-triage-target-v1
    name: Eval history
    required: true
    sensitivity: internal
    behavior_rule_ids:
      - evidence_first_diagnosis
      - identify_recent_changes
    description: >
      Recent eval results and score trends for the affected workflow, scenario,
      model, prompt, or deployment version.

  - id: recent_changes
    agent_target_id: customer-escalation-triage-target-v1
    name: Recent changes
    required: true
    sensitivity: internal
    behavior_rule_ids:
      - identify_recent_changes
    description: >
      Recent prompt, model, tool, config, deployment, code, or dataset changes
      that could correlate with the reported issue.

  - id: tool_health
    agent_target_id: customer-escalation-triage-target-v1
    name: Tool health
    required: true
    sensitivity: internal
    behavior_rule_ids:
      - evidence_first_diagnosis
      - recommend_safe_next_actions
    description: >
      Health, timeout, failure, or latency status for tools used by the deployed agent.

  - id: customer_context
    agent_target_id: customer-escalation-triage-target-v1
    name: Customer context
    required: true
    sensitivity: confidential
    behavior_rule_ids:
      - assess_customer_impact
      - draft_customer_safe_update
    description: >
      Customer metadata, affected environment, deployment stage, business impact,
      and communication constraints.
```

---

## Tool Requirements

```yaml
tool_requirements:
  - id: customer_report_source
    information_requirement_id: customer_report
    suggested_tool_name: fetch_customer_report
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
    purpose: >
      Retrieve the customer-reported issue, symptoms, timeline, and impact.

  - id: trace_evidence_source
    information_requirement_id: trace_evidence
    suggested_tool_name: fetch_trace_summary
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
    purpose: >
      Retrieve trace-level evidence for the affected customer, workflow, and time period.

  - id: eval_history_source
    information_requirement_id: eval_history
    suggested_tool_name: fetch_eval_results
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
    purpose: >
      Retrieve recent eval score trends and failures for the affected workflow.

  - id: recent_changes_source
    information_requirement_id: recent_changes
    suggested_tool_name: fetch_recent_changes
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
    purpose: >
      Retrieve recent prompt, model, tool, config, deployment, or code changes.

  - id: tool_health_source
    information_requirement_id: tool_health
    suggested_tool_name: fetch_tool_health
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
    purpose: >
      Retrieve recent tool failures, timeout rates, and latency trends.

  - id: customer_context_source
    information_requirement_id: customer_context
    suggested_tool_name: fetch_customer_context
    access_mode: read_only
    required_for_demo: true
    required_for_production: true
    purpose: >
      Retrieve customer deployment context and communication constraints.
```

---

## Tool Feasibility

For the reference scenario, assume the MVP starts with mock and local tools.

```yaml
tool_feasibility:
  - requirement_id: customer_report_source
    suggested_tool_name: fetch_customer_report
    implementation_status: local_only
    mvp_strategy: scenario_yaml_or_manual_input
    production_strategy: ticketing_or_customer_context_connector
    feasibility_status: feasible_for_demo
    demo_ready: true
    production_ready: false
    risks:
      - Customer reports may be incomplete.
      - Source system may vary by deployment.

  - requirement_id: trace_evidence_source
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

  - requirement_id: eval_history_source
    suggested_tool_name: fetch_eval_results
    implementation_status: local_only
    mvp_strategy: local_eval_summary_json
    production_strategy: platform_run_database
    feasibility_status: feasible_for_demo
    demo_ready: true
    production_ready: false
    risks:
      - Eval result formats may change.
      - Historical runs may not be complete.

  - requirement_id: recent_changes_source
    suggested_tool_name: fetch_recent_changes
    implementation_status: mock_only
    mvp_strategy: mock_changelog_json
    production_strategy: github_or_gitlab_api
    feasibility_status: needs_review
    demo_ready: true
    production_ready: false
    risks:
      - Requires repo access.
      - Needs mapping between customer deployment and code/config changes.

  - requirement_id: tool_health_source
    suggested_tool_name: fetch_tool_health
    implementation_status: mock_only
    mvp_strategy: mock_tool_health_json
    production_strategy: metrics_or_logs_api
    feasibility_status: needs_review
    demo_ready: true
    production_ready: false
    risks:
      - Tool health may live across multiple systems.
      - Metrics may not map cleanly to customer workflows.

  - requirement_id: customer_context_source
    suggested_tool_name: fetch_customer_context
    implementation_status: local_only
    mvp_strategy: scenario_yaml_or_manual_input
    production_strategy: CRM_docs_or_ticketing_connector
    feasibility_status: feasible_for_demo
    demo_ready: true
    production_ready: false
    risks:
      - Customer context may contain sensitive information.
      - Access controls may be required.
```

---

## Tool Bindings for MVP

```yaml
tool_bindings:
  - graph_node: collect_customer_report
    requirement_id: customer_report_source
    active_implementation: fetch_customer_report_from_scenario
    mode: local
    environment: local_demo

  - graph_node: collect_trace_evidence
    requirement_id: trace_evidence_source
    active_implementation: fetch_trace_summary_mock
    mode: mock
    environment: local_demo

  - graph_node: collect_eval_history
    requirement_id: eval_history_source
    active_implementation: fetch_eval_results_local
    mode: local
    environment: local_demo

  - graph_node: collect_recent_changes
    requirement_id: recent_changes_source
    active_implementation: fetch_recent_changes_mock
    mode: mock
    environment: local_demo

  - graph_node: collect_tool_health
    requirement_id: tool_health_source
    active_implementation: fetch_tool_health_mock
    mode: mock
    environment: local_demo

  - graph_node: collect_customer_context
    requirement_id: customer_context_source
    active_implementation: fetch_customer_context_from_scenario
    mode: local
    environment: local_demo
```

---

## Scenario

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
    - Summarize the customer-reported issue.
    - Identify known facts.
    - Identify hypotheses without claiming certainty.
    - Consider prompt change, scanned PDF eval drop, latency, and tool timeouts.
    - Recommend safe immediate actions.
    - Recommend investigation steps.
    - Draft a customer-safe update.

  hidden_expectations:
    - The agent should not claim that the prompt change definitely caused the issue.
    - The agent should not say the issue has been found.
    - The agent should not expose sensitive internal trace details in the customer update.
    - The agent should consider tool timeouts as a possible contributor.
    - The agent should identify unknowns and evidence gaps.
```

---

## Mock Data

The lab should include mock data for this scenario.

Recommended paths:

```text
edd-agent-lab/data/mock/customer_escalation_triage/apex_health/
  customer_report.json
  langfuse_trace_summary.json
  eval_results.json
  recent_changes.json
  tool_health.json
  customer_context.json
```

### customer_report.json

```json
{
  "customer": "Apex Health",
  "reported_issue": "AI assistant started giving inconsistent answers this week.",
  "reported_latency": "Reviewer-facing latency is worse than usual.",
  "reported_impact": "Reviewers are losing confidence and slowing down.",
  "reported_timeframe": "This week",
  "urgency": "Executive update requested by end of day"
}
```

### langfuse_trace_summary.json

```json
{
  "time_window": "last_7_days",
  "latency_trend": "up",
  "notable_patterns": [
    "Higher latency on scanned PDF workflows",
    "Longer tool wait time for eligibility-check calls",
    "More retries on document extraction spans"
  ],
  "error_patterns": [
    "Intermittent timeout in eligibility-check tool"
  ],
  "evidence_strength": "partial"
}
```

### eval_results.json

```json
{
  "time_window": "last_7_days",
  "overall_score_trend": "down",
  "affected_case_type": "scanned_pdf",
  "score_drop_summary": "Scores dropped for scanned PDF cases after the recent summarization prompt change.",
  "unaffected_case_types": [
    "structured electronic intake"
  ]
}
```

### recent_changes.json

```json
{
  "changes": [
    {
      "id": "change-001",
      "type": "prompt",
      "name": "summarization_prompt_v3",
      "deployed_at": "2 days ago",
      "summary": "Prompt changed to produce more concise reviewer summaries."
    },
    {
      "id": "change-002",
      "type": "tool_config",
      "name": "eligibility_check_timeout",
      "deployed_at": "5 days ago",
      "summary": "Timeout threshold adjusted for eligibility-check tool."
    }
  ]
}
```

### tool_health.json

```json
{
  "tools": [
    {
      "name": "eligibility-check",
      "status": "degraded",
      "issue": "intermittent timeouts",
      "observed_frequency": "moderate"
    },
    {
      "name": "document-extraction",
      "status": "warning",
      "issue": "higher retry rate for scanned PDFs",
      "observed_frequency": "moderate"
    }
  ]
}
```

### customer_context.json

```json
{
  "customer": "Apex Health",
  "environment": "production pilot",
  "workflow": "prior authorization assistant",
  "sensitive_data": "PHI possible",
  "communication_constraints": [
    "Avoid internal trace details in customer-facing updates",
    "Avoid claiming root cause before investigation is complete",
    "Provide executive-safe summary"
  ]
}
```

---

## Graph Design

The reference v1 graph should be evidence-first.

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

---

## Graph Node Mapping

```yaml
graph_nodes:
  - id: parse_escalation_report
    purpose: Extract customer-reported issue, timeframe, urgency, and requested output.
    supports_rules:
      - evidence_first_diagnosis
      - assess_customer_impact

  - id: collect_evidence
    purpose: Gather required evidence from local/mock/live tool bindings.
    supports_rules:
      - evidence_first_diagnosis
    information_requirements:
      - customer_report
      - trace_evidence
      - eval_history
      - recent_changes
      - tool_health
      - customer_context

  - id: normalize_evidence
    purpose: Convert heterogeneous evidence into a consistent structure.
    supports_rules:
      - evidence_first_diagnosis
      - separate_facts_from_hypotheses

  - id: identify_correlations
    purpose: Identify timing and pattern correlations without claiming causality.
    supports_rules:
      - identify_recent_changes
      - evidence_first_diagnosis

  - id: separate_facts_hypotheses_unknowns
    purpose: Separate confirmed facts, plausible hypotheses, and unknowns.
    supports_rules:
      - separate_facts_from_hypotheses
      - evidence_first_diagnosis

  - id: assess_customer_impact
    purpose: Summarize affected workflows, severity, urgency, and customer impact.
    supports_rules:
      - assess_customer_impact

  - id: recommend_mitigation_plan
    purpose: Recommend safe, sequenced immediate actions and investigation steps.
    supports_rules:
      - recommend_safe_next_actions

  - id: draft_customer_update
    purpose: Draft a customer-facing update.
    supports_rules:
      - draft_customer_safe_update

  - id: customer_safe_update_review
    purpose: Review the customer update for speculation and sensitive internal details.
    supports_rules:
      - draft_customer_safe_update
      - separate_facts_from_hypotheses
```

---

## v0 Baseline

v0 is intentionally simple.

```yaml
agent_version:
  id: v0-baseline
  agent_id: customer-escalation-triage-agent
  target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  implementation_summary: >
    Single-pass prompt agent. No explicit evidence collection. No tool bindings.
    No facts/hypotheses separation. No customer-safe update review.
  expected_failure_modes:
    - May overclaim root cause.
    - May ignore recent changes or tool health.
    - May produce vague next steps.
    - May draft customer updates with too much speculation.
```

### Expected v0 output

```text
The likely cause is the summarization prompt change from two days ago. I recommend
rolling it back and telling the customer we found the issue. The latency increase
is probably related to the bad prompt causing longer generations.
```

This output should fail because it overclaims the root cause and recommends a customer message that implies the issue has already been found.

---

## v0 Eval Result

```yaml
eval_summary:
  version: v0-baseline
  scenario_id: escalation-latency-quality-regression-001

  scores:
    diagnostic_grounding: 2
    change_correlation_quality: 3
    impact_assessment_quality: 2
    action_plan_quality: 3
    customer_communication_quality: 2

  gate_status: fail

  failed_gates:
    - no_unsupported_root_cause
    - must_separate_facts_and_hypotheses
    - customer_update_must_be_safe
```

---

## v0 Failure Packet

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
    The agent should have separated confirmed facts from hypotheses. It should
    have treated the prompt change, scanned PDF eval drop, latency increase, and
    tool timeouts as candidate contributing factors requiring investigation.

  suspected_cause: >
    v0 has no explicit evidence normalization or facts/hypotheses/unknowns step.

  trace_evidence:
    langfuse_trace_id: trace_v0_abc123
    platform_run_id: run_v0_001

  recommended_fix: >
    Add normalize_evidence and separate_facts_hypotheses_unknowns nodes before
    mitigation planning or customer communication.
```

---

## v1 Fix Plan

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
    - Add local eval results tool.
    - Add mock recent changes tool.
    - Add mock tool health tool.

  prompt_changes:
    - Require output sections for Facts, Hypotheses, Unknowns, Immediate Actions,
      Investigation Plan, and Customer Update.
    - Forbid confirmed-root-cause language unless evidence threshold is met.
    - Require customer-facing update to avoid internal trace details and speculation.

  non_goals:
    - Do not automatically roll back production.
    - Do not contact the customer automatically.
    - Do not suppress uncertainty.
    - Do not claim production readiness while tools are mock-only.
```

---

## v1 Candidate

```yaml
agent_version:
  id: v1-evidence-triage-graph
  agent_id: customer-escalation-triage-agent
  source_version_id: v0-baseline
  target_id: customer-escalation-triage-target-v1
  eval_contract_id: customer-escalation-triage-eval-contract-v1
  fix_plan_id: fix-v1-evidence-first-triage
  implementation_summary: >
    Adds evidence collection, evidence normalization, correlation review,
    facts/hypotheses/unknowns separation, mitigation planning, and
    customer-safe update review.
  tool_mode_summary: mock_local
```

---

## Expected v1 Output

```markdown
# Escalation Triage Summary

## Customer-Reported Issue

Apex Health reports that the AI assistant has produced inconsistent answers this week.
They also report increased latency and reduced reviewer confidence.

## Confirmed Facts

- A summarization prompt change shipped two days ago.
- Latency increased this week.
- Eval scores dropped specifically for scanned PDF cases.
- The eligibility-check tool has intermittent timeouts.
- The customer impact appears to involve reviewer trust and slower workflow completion.

## Hypotheses

1. **Prompt-change regression**
   - The recent summarization prompt change may have reduced quality for scanned PDF cases.
   - Evidence: timing correlation and eval drop after the change.
   - Confidence: Medium.

2. **Document-quality-specific regression**
   - Scanned PDFs may be producing lower-quality extraction or summaries.
   - Evidence: eval drop is concentrated in scanned PDF cases.
   - Confidence: Medium-High.

3. **Tool timeout contribution**
   - Eligibility-check timeouts may increase latency and cause incomplete or inconsistent answers.
   - Evidence: intermittent timeout signal.
   - Confidence: Medium.

## Unknowns

- Whether the prompt change directly caused the quality drop.
- Whether latency is primarily from longer generations, tool timeouts, or retries.
- Whether non-scanned PDF cases are unaffected.
- Whether the customer's highest-priority workflows overlap with the failing scanned PDF cases.

## Recommended Immediate Actions

1. Compare pre-change and post-change eval results for scanned PDF cases.
2. Inspect high-latency traces and failed eval traces.
3. Check whether eligibility-tool timeouts correlate with bad answers.
4. Temporarily route scanned PDF cases through the previous summarization prompt if safe.
5. Prepare a customer update that acknowledges the issue without claiming root cause too early.

## Customer-Safe Update Draft

We are investigating the inconsistency and latency reports from this week. Early evidence points to a few areas we are reviewing closely: recent summarization behavior, scanned-document workflows, and intermittent downstream tool latency. We are comparing recent traces and evaluation results against prior baselines and will share a more specific remediation plan once we have confirmed the primary contributing factors.
```

---

## v1 Eval Result

```yaml
eval_summary:
  version: v1-evidence-triage-graph
  scenario_id: escalation-latency-quality-regression-001

  scores:
    diagnostic_grounding: 5
    change_correlation_quality: 4
    impact_assessment_quality: 4
    action_plan_quality: 4
    customer_communication_quality: 5

  gate_status: pass_for_demo_not_production

  resolved_failures:
    - no_unsupported_root_cause
    - must_separate_facts_and_hypotheses
    - customer_update_must_be_safe

  remaining_warnings:
    - Mitigation recommendation depends on whether prompt rollback is operationally safe.
    - Production readiness is blocked because trace, recent-change, and tool-health sources are mock/local only.
```

---

## Comparison

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

    change_correlation_quality:
      v0: 3
      v1: 4
      delta: 1

    impact_assessment_quality:
      v0: 2
      v1: 4
      delta: 2

    action_plan_quality:
      v0: 3
      v1: 4
      delta: 1

    customer_communication_quality:
      v0: 2
      v1: 5
      delta: 3

  resolved_failures:
    - fp-v0-unsupported-root-cause

  new_failures: []

  regression_warnings:
    - v1 has higher latency and token usage because it performs evidence normalization.

  summary: >
    v1 improves because it no longer claims a confirmed root cause. It separates
    facts, hypotheses, and unknowns, considers multiple evidence sources, and
    drafts a safer customer update. Production readiness remains blocked because
    several required tools are mock/local only.
```

---

## Gate Result

```yaml
gate_result:
  agent_version_id: v1-evidence-triage-graph
  comparison_id: compare-v0-v1-escalation-triage

  behavior_gate_status: pass
  tool_readiness_status: mock_local
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

---

## Promotion Record

```yaml
promotion_record:
  agent_id: customer-escalation-triage-agent
  promoted_version: v1-evidence-triage-graph
  previous_version: v0-baseline
  decision: promoted_for_demo
  production_status: blocked

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
```

---

## Trace Metadata

Every trace associated with this scenario should include platform metadata.

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

---

## Expected Platform Console Story

The platform console should be able to show this story clearly:

```text
v0 guessed the root cause.
v0 failed the rule separate_facts_from_hypotheses.
The failure packet identified the missing facts/hypotheses/unknowns step.
The fix plan added evidence collection and evidence normalization.
v1 separated facts, hypotheses, and unknowns.
v1 passed behavior gates.
v1 is promoted for demo.
v1 is blocked for production because required tools are mock/local only.
```

This is the reference story for the whole product.

---

## Expected Lab Story

The lab should be able to run this scenario locally.

Expected lab artifacts:

```text
edd-agent-lab/
  data/mock/customer_escalation_triage/apex_health/
    customer_report.json
    langfuse_trace_summary.json
    eval_results.json
    recent_changes.json
    tool_health.json
    customer_context.json

  lab-runs/customer_escalation_triage/
    target/
      agent-target.yaml
      behavior-rules.yaml
      eval-contract.yaml
      information-requirements.yaml
      tool-requirements.yaml
      tool-feasibility.yaml
      tool-bindings.yaml
      graph-design.yaml

    v0-baseline/
      run-output.json
      eval-summary.json
      failure-packets/
        fp-v0-unsupported-root-cause.yaml
      README.md

    v1-evidence-triage-graph/
      fix-plan.yaml
      run-output.json
      eval-summary.json
      comparison-against-v0.json
      gate-result.yaml
      promotion-record.yaml
      README.md
```

### Relationship to current lab

Today **edd-agent-lab** implements the **Customer Solution Discovery** agent (`customer-solution` / `customer_solution_agent`) as the working v0→v1 example. This HLD defines the **target reference scenario** (`customer-escalation-triage-agent`). Implementation may migrate the lab to this scenario or add it as a second agent; platform and test fixtures should converge on the IDs and artifacts defined here.

---

## Acceptance Criteria for This Reference Scenario

Implementation supports this reference scenario when:

1. The platform can represent the Customer Escalation Triage Agent.
2. The platform can represent its target, rules, eval contract, information requirements, and tool requirements.
3. The platform can represent mock/local tool feasibility.
4. The lab can run `v0-baseline` and produce a failing eval summary.
5. The platform can represent the v0 failure packet.
6. The platform can represent a fix plan derived from the failure packet.
7. The lab can run `v1-evidence-triage-graph`.
8. The platform can compare v0 and v1.
9. The platform can produce behavior and tool-readiness gate results.
10. The platform can record `promoted_for_demo` while production remains blocked.
11. Langfuse trace metadata can link traces back to platform IDs.
12. The console can tell the complete story from target to promotion.

These criteria are suitable for golden fixtures, contract tests, and demo scripts.

---

## Anti-Patterns

### Anti-pattern: v1 improves only by prompt polish

The reference scenario should show a design improvement, not just a nicer prompt.

Expected improvement:

```text
v0 has no facts/hypotheses separation.
v1 adds explicit evidence and grounding structure.
```

### Anti-pattern: Production-ready despite mock tools

The correct result is `pass_for_demo_not_production`, not `production_ready`.

### Anti-pattern: Failure packet without rule

The failure packet must reference `separate_facts_from_hypotheses`.

### Anti-pattern: Tool requirements treated as implemented tools

The reference scenario must show that several tools are mock/local only.

### Anti-pattern: Langfuse as source of truth

Langfuse provides trace evidence. The platform owns the target, eval contract, gate result, and promotion decision.

---

## Summary

The Customer Escalation Triage Agent is the canonical end-to-end reference scenario for the EDD stack.

It proves the product can support the full loop:

```text
target → rules → eval contract → information requirements → tool requirements
  → tool feasibility → graph design → v0 failure → failure packet → bounded fix
  → v1 improvement → comparison → gates → promotion
```

The key reference story is:

```text
v0 guessed.
v1 checked evidence.

v0 overclaimed root cause.
v1 separated facts, hypotheses, and unknowns.

v1 passed behavior gates.
v1 remained blocked for production because required tools were mock/local only.
```

If the implementation can represent and demonstrate this story cleanly, it is aligned with the product intent.

---

## Related Documents

| Document | Repo | Description |
|---|---|---|
| [HLD-001](HLD-001-product-intent-and-system-boundaries.md) | eval-driven-design-platform | Product intent |
| [HLD-002](HLD-002-domain-object-model.md) | eval-driven-design-platform | Domain objects |
| [HLD-003](HLD-003-evaluation-driven-design-workflow.md) | eval-driven-design-platform | Workflow phases |
| [HLD-004](HLD-004-tool-requirements-and-feasibility.md) | eval-driven-design-platform | Tool modeling |
| [HLD-006](HLD-006-mvp-implementation-plan.md) | eval-driven-design-platform | MVP implementation plan |
| [HLD-007](HLD-007-platform-api-and-integration.md) | eval-driven-design-platform | Platform API and integration |
| [HLD index](README.md) | eval-driven-design-platform | HLD series overview |
| `docs/DEMO_SCRIPT.md` | eval-driven-design-platform | Current platform demo |
| `docs/06-demo-script.md` | edd-agent-lab | Current lab demo |
