# EDD API

FastAPI control plane for the Eval Driven Design Platform.

## Phase 0.5 platform spine

- Demo JWT auth (`APP_AUTH_ENABLED`, `RequestContext`)
- Structured JSON logging + request IDs
- OpenTelemetry (console/OTLP/none)
- Prometheus `/metrics`
- Storage factory: in-memory (default) or Postgres health check
- Alembic wired (baseline migration; EDD tables in Phase 1)

Health endpoints:

- `/v1/health`, `/v1/ready` (EDD convention)
- `/health/live`, `/health/ready` (starter-compatible)

## Phase 1 domain API

- `POST/GET/PATCH/DELETE /v1/eval-specs`
- `POST/GET/PATCH/DELETE /v1/eval-cases`
- Tenant from bearer token when auth is enabled, or `tenant_id` query/body when disabled

Example (auth disabled):

```bash
curl -X POST http://localhost:8000/v1/eval-specs \
  -H 'content-type: application/json' \
  -d '{"tenant_id":"tenant-a","name":"Support quality","rubric":"Mention empathy."}'

curl 'http://localhost:8000/v1/eval-specs?tenant_id=tenant-a'
```

## Phase 2 experiment runs

- `POST /v1/experiment-runs` — run mock scaffold + judge for one or more cases
- `GET /v1/experiment-runs/{id}/summary` — pass rate and average score
- `GET /v1/evaluation-results?experiment_run_id=...` — per-case scores

Seed demo data against a running API:

```bash
./scripts/local_e2e.sh
uv run --directory api python ../scripts/seed_demo_data.py --tenant-id tenant-a
```

## Local dev

From repo root:

```bash
./scripts/local_e2e.sh
./scripts/local_e2e.sh --postgres
```

From this directory:

```bash
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8000
uv run pytest -q
```

Demo JWT:

```bash
APP_AUTH_DEMO_SECRET=local-demo-secret \
  uv run python ../scripts/create_demo_jwt.py --tenant-id tenant-a --subject local-user
```
