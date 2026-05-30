# Product vision — historical notes + future workload ideas

> **Status (2026):** Superseded for **architecture**, **system boundaries**, and the **canonical reference scenario** by [`docs/hld/`](hld/README.md) (HLD-001 through HLD-005).  
> For **phased delivery**, see [`docs/HLD_TEST_FIRST_IMPLEMENTATION.md`](../HLD_TEST_FIRST_IMPLEMENTATION.md) and [HLD-006](hld/HLD-006-mvp-implementation-plan.md).  
> For **runnable agents**, see the separate **[edd-agent-lab](https://github.com/bfalkowski/edd-agent-lab)** repo.

This document captures early design thinking. It is **not** the implementation spec. Keep it for context and for a possible **second demo workload** (prioritization agent), not as the primary product narrative.

---

## Current product story (canonical)

The **EDD stack** is two repos:

| Repo | Role |
|---|---|
| **eval-driven-design-platform** | Control plane: EvalSpec, EvalCase, ExperimentRun, quality gates, Langfuse adapter, operator console |
| **edd-agent-lab** | Runnable LangGraph agents, local evals, artifacts, optional publish to platform |

Integration: `edd-agent-lab` → `POST /v1/integrations/runs/publish` → platform → Langfuse (optional).

**Reference scenario (target):** [HLD-005](hld/HLD-005-reference-scenario-customer-escalation-triage.md) — Customer Escalation Triage Agent (v0 overclaims root cause → v1 evidence-first graph → promoted for demo, blocked for production).

**Working lab example today:** Customer Solution Discovery agent in edd-agent-lab (`customer-solution`).

**One line:** An eval-driven design control plane on Langfuse — plus a lab that proves the full design loop with trace-backed v0 → v1 improvement.

---

## What remains valid from this doc

- EDD is a **control plane on Langfuse**, not a Langfuse clone.
- The **evaluated workflow** is the product boundary (not a single LLM call).
- **EvalSpec / EvalCase / ExperimentRun / quality gates** are the platform spine (evolving toward richer HLD domain objects).
- **v0 → v1** with frozen baseline and objective eval checks is the proof model.
- **Avoid:** tariff/BOM demos, vibes-only evals, Langfuse clone, logging sensitive content in metrics.

---

## What changed since this doc was written

| Old assumption | Current reality |
|---|---|
| Demo agent lives in **this monorepo** | Agents live in **edd-agent-lab**; platform must not import the lab |
| Primary demo = **prioritization / Day Stack** | Primary reference = **Customer Escalation Triage** (HLD-005) |
| Phase 7 gates = future | **Done** — gate API, console page, CI script, external run ingest |
| Console gets `9_Agent.py` in platform | Lab has `:8502` console; platform console stays operator workflow (`:8501`) |
| EvalSpec-only mental model | HLDs add AgentTarget, BehaviorRule, tool feasibility, failure packets, promotion |

---

## 1. Original goal (still directionally true)

Build two things that reinforce each other:

1. **Eval Driven Design Platform** — control plane for eval-driven AI development on Langfuse.
2. **A demo application that produces real traces** — so the eval loop (v0 → v1, gates, promotion) is demonstrable.

The **first shipped demo application** is in **edd-agent-lab**, not embedded in the platform monorepo. That split matches [HLD-001](hld/HLD-001-product-intent-and-system-boundaries.md).

---

## 2. Platform pieces (built — still valid)

| Built | Role |
|---|---|
| EvalSpec | What “good” means (rubric, threshold); maps toward EvalContract in HLD-002 |
| EvalCase | Reusable scenarios |
| ExperimentRun + ingest | Platform runs + lab publish via `/v1/integrations/runs/publish` |
| Mock scaffold + mock judge | Deterministic CI |
| Langfuse adapter | Health, import, scores, trace create |
| Streamlit console | Observe → Case → Run → Evaluate → Decide (+ Quality Gates) |
| Platform spine | Auth, Postgres, metrics, CI, deploy |

**MVP note:** “No real LLM in MVP” meant don’t block the control plane on LLM keys — not “never add an LLM.” The lab can use live generation; the platform mock path stays for fast CI.

---

## 3. What to avoid (creative + credible)

- **Tariff / BOM / supply-chain card demo** — too close to canonical FDE video content.
- **Pure vibes evals** — “sounds helpful” without structured checks tied to behavior rules.
- **LLM inventing facts** — evidence should come from tools + structured inputs (see HLD-004).
- **Real personal todos in public traces** — use fixtures for portfolio/CI.
- **Langfuse clone** — debug in Langfuse; platform owns workflow, gates, and promotion meaning.
- **Production readiness from mock tools** — see HLD-004 and HLD-005.

---

## 4. Future workload idea — productivity / prioritization agent

> **Not the canonical reference scenario.** Preserved here as a possible **second agent** in edd-agent-lab after escalation triage is fully represented on the platform.

### Problem

Prioritization and multitasking — what to work on in the next N minutes given deadlines, estimates, energy, and calendar constraints.

### Design principle

**Not a todo app.** A **decision support** system:

- Task store holds structured tasks (due, estimate_min, priority, energy, status, tags).
- **Planner tool** applies rules deterministically: `compute_daily_plan(tasks, time_budget, context)`.
- Chat **explains** the plan; it does not invent rankings or durations.

### Example user questions (golden scenarios)

1. “What’s my one thing for the next hour?”
2. “I’m drained — what’s a small win?” (`energy: low`)
3. “What’s overdue and still open?”
4. “I have 90 minutes before standup — what should I work on?”
5. “I have three hard deadlines today — order my afternoon.”

### Tools (MVP: 2–4)

| Tool | Returns |
|------|---------|
| `list_tasks` | Open tasks with structured fields |
| `compute_daily_plan` | Ranked list, total minutes, `rationale_codes[]` |
| `get_time_budget` | Free minutes until next event (mock calendar OK) |
| `complete_task` | Optional — mark done |

### v0 vs v1 (demo story)

| | v0-baseline | v1-improved |
|--|-------------|-------------|
| Behavior | Generic advice; ignores due dates / budget; may skip tools | Always `list_tasks` + `compute_daily_plan` |
| Failure | Fun task wins; overdue missed; overbooks time | — |
| Proof | Experiment run fails gate | Same cases pass |

If implemented, this agent would live in **edd-agent-lab** and publish runs to the platform — same pattern as Customer Solution Discovery today.

---

## 5. Two layers of “rules” (maps to HLD-002)

1. **Product / behavior rules** — hard constraints in code or graph (planner weights, facts/hypotheses separation).
2. **Eval rules** — EvalSpec / EvalContract + scenarios (what you’re willing to ship).

The HLD stack makes both explicit as `BehaviorRule` + `EvalContract` + gates.

---

## 6. Langfuse + EDD loop (updated)

```text
edd-agent-lab (agent + tools + LangGraph)
        │  traces / scores (Langfuse SDK or platform adapter)
        ▼
   Langfuse — observe failures
        │  import trace / link
        ▼
eval-driven-design-platform
   EvalCase → ExperimentRun (or ingest) → Results → Quality gate → promotion readiness
```

**Constraints (from AGENTS.md):**

- Langfuse HTTP/API integration stays in platform `integrations/` only.
- Do not log prompt/answer/rubric in metrics or OTel span attributes by default.
- Tests deterministic; mock evaluator / fixtures in CI.

---

## 7. Alternative lenses (prioritization agent)

Sections 8.1–8.10 from the original doc still apply as **product exploration** for the prioritization workload: decision support, executable policy, clerk/planner/coach roles, attention firewall, simulation, outcome loop, regression harness, MCP maturity stages, multi-context profiles, platform showcase.

Use HLD-003 workflow phases when turning any of these into a real agent.

---

## 8. Roadmap sketch (updated)

| Priority | Work |
|----------|------|
| **Done** | Platform Phases 0–7, external run ingest, quality gates, DEMO_SCRIPT |
| **Now** | HLD-aligned implementation: contract tests, design-intent domain, tool feasibility, reference scenario in lab |
| **Next** | Console lifecycle UX (see edd-agent-lab `docs/11-ideal-console-design.md`) |
| **Later** | Prioritization agent as second edd-agent-lab workload (this doc §4) |
| **Later** | MCP calendar/tasks, operational mode (HLD-003 Phase 7) |

---

## 9. Open decisions

- [ ] Product name for prioritization agent (e.g. Day Stack) — if/when built
- [ ] Migrate lab reference from Customer Solution Discovery to HLD-005 escalation triage
- [ ] Envelope schema v2 (`tool_bindings`, target/contract IDs on publish)
- [ ] Cross-repo CI for `test_platform_publish.sh`

---

## 10. Related documents

| Document | Purpose |
|---|---|
| [`docs/hld/README.md`](hld/README.md) | **Canonical** architecture and reference scenario |
| [`docs/HLD_TEST_FIRST_IMPLEMENTATION.md`](../HLD_TEST_FIRST_IMPLEMENTATION.md) | Platform execution plan (Phases 9–13) |
| [`AGENTS.md`](../AGENTS.md) | Constraints for coding assistants |
| [`README.md`](../README.md) | Quick start and current status |
| [edd-agent-lab](https://github.com/bfalkowski/edd-agent-lab) | Agents, local evals, publish client |
