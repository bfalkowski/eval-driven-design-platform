# Deploy

## Docker Compose

```bash
cd deploy
docker compose up --build
```

Postgres is exposed on host port **5433** (not 5432) to reduce conflicts with other local stacks.

Optional Langfuse overlay (stub until Phase 4):

```bash
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d
```

## Helm (Phase 0.5 skeleton)

Chart imported from `llm-evaluation-service-deploy` and renamed for the EDD monorepo:

```bash
helm upgrade --install edd-platform ./deploy/charts/edd-platform \
  -f ./deploy/charts/edd-platform/values-local.yaml
```

Image tags and API/console/worker wiring will evolve with Phases 1–8. Treat this as a starting point, not production-ready config.
