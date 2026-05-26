# AGENTS.md

Clean-room Eval Driven Design Platform. Langfuse is the observability data plane; this repo is the eval-driven development control plane.

## Constraints

- Do not build a Langfuse clone or custom trace browser.
- Do not log prompt, answer, or rubric content in metrics or OTel span attributes by default.
- Keep Langfuse SDK/API calls behind `integrations/langfuse_client.py` only.
- Keep tests deterministic; mock evaluator by default until explicitly requested.
- Do not mention employers, interviews, or proprietary systems in public docs.

## Planning

- Follow `EVAL_DRIVEN_DESIGN_PLAN.md` phase by phase.
- Do not implement later phases while earlier validation is incomplete.
- Optional local-only detail: if `.local/PRODUCT_SPEC_REFERENCE.md` exists, use it for UI wireframes, DDL, example payloads, and phase prompts. Do not commit `.local/` or treat it as canonical over the phased plan.

## Commits

- If `.local/COMMIT_STEERING.md` exists, follow it (no Cursor co-author trailers).
