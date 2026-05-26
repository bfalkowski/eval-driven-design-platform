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
