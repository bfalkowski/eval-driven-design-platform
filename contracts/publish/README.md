# Publish contract fixtures

Canonical JSON fixtures for `POST /v1/integrations/runs/publish`.

## schema_version `1`

| File | Expected `gate_status` |
|---|---|
| `v1/envelope-pass.json` | `pass` |
| `v1/envelope-fail-failure-packet.json` | `fail` |
| `v1/envelope-insufficient-evidence.json` | `insufficient_evidence` |
| `v1/response-minimal.json` | Response field checklist (not a request body) |

Platform tests: `api/tests/test_publish_contract_fixtures.py`

## schema_version `2`

Structured publish envelope with `producer`, `tool_context`, and HLD object references.

| File | Expected `gate_status` | Expected `overall_status` |
|---|---|---|
| `v2/envelope-pass-demo-not-production.json` | `pass` | `pass_for_demo_not_production` |
| `v2/envelope-fail-failure-packet.json` | `fail` | `fail` |
| `v2/response-minimal.json` | Response + readiness field checklist |

Platform tests: `api/tests/test_publish_contract_fixtures_v2.py`

v1 envelopes remain valid. v2 adds readiness dimensions via `tool_context` without breaking the v1 demo path.

Lab should keep envelope builder output aligned with these fixtures (PR 9b / 11b).

Fixtures omit `eval_spec_id`; tests inject it at runtime after creating an EvalSpec.
