# Publish contract fixtures

Canonical JSON fixtures for `POST /v1/integrations/runs/publish` (schema_version `1`).

| File | Expected `gate_status` |
|---|---|
| `v1/envelope-pass.json` | `pass` |
| `v1/envelope-fail-failure-packet.json` | `fail` |
| `v1/envelope-insufficient-evidence.json` | `insufficient_evidence` |
| `v1/response-minimal.json` | Response field checklist (not a request body) |

Platform tests: `api/tests/test_publish_contract_fixtures.py`

Lab should keep envelope builder output aligned with these fixtures (PR 9b).

Fixtures omit `eval_spec_id`; tests inject it at runtime after creating an EvalSpec.
