# Deploy

## Docker Compose

```bash
cd deploy
docker compose up --build
```

Postgres is exposed on host port **5433** (not 5432) to reduce conflicts with other local stacks.

### Docker build troubleshooting

If `docker compose up --build` fails with `archive/tar: missed writing` or `unexpected EOF`, Docker is likely choking on a huge build context. Each service directory now has a `.dockerignore` that excludes `.venv/`, test caches, and other dev artifacts.

If builds still fail after pulling latest:

```bash
docker builder prune -f
docker system df
./scripts/build_images.sh
cd deploy && docker compose up -d
```

For day-to-day development without rebuilding images, prefer:

```bash
./scripts/local_e2e.sh --postgres   # Postgres in Docker, API + console on host
```

Optional Langfuse overlay (Phase 4):

```bash
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d
```

Langfuse UI: http://localhost:3001 (demo login `admin@local.dev` / `local-demo-password`).

Host ports exposed by the Langfuse overlay:

| Service | Host port | Notes |
|---------|-----------|-------|
| Langfuse UI | 3001 | Browser + API health from host |
| MinIO | 19090 | Media upload endpoint only |

Langfuse Postgres, Redis, ClickHouse, and worker stay on the internal Docker network only.

When the overlay is active, `edd-api` is preconfigured with demo Langfuse keys and
`GET /v1/integrations/langfuse/health` should report `healthy` once Langfuse finishes booting.

**Important:** stop the host dev stack before using compose URLs, or `localhost:8000` may hit the
in-memory API from `./scripts/local_e2e.sh` (Langfuse shows as disabled):

```bash
./scripts/local_e2e.sh --stop
./scripts/compose_credentials.sh
```

If Langfuse reports `degraded` / invalid API keys after a previous compose run, reset Langfuse
Postgres so headless init can seed the demo keys (requires `LANGFUSE_INIT_ORG_ID` and
`LANGFUSE_INIT_PROJECT_ID`):

```bash
./scripts/compose_up_langfuse.sh
```

Or manually:

```bash
cd deploy
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml stop langfuse-web langfuse-worker langfuse-postgres
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml rm -f langfuse-postgres
docker volume rm deploy_langfuse-postgres-data
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d
docker exec deploy-langfuse-redis-1 redis-cli -a myredissecret FLUSHALL
```

If Docker says `Cannot connect to the Docker daemon`, Colima may be in a stale state
(`colima start` says "already running" but `docker ps` fails). Fix with:

```bash
./scripts/colima_fix.sh
./scripts/compose_up_langfuse.sh
```

Or manually:

```bash
colima stop
colima start
docker context use colima
docker ps
```

## Helm (Phase 0.5 skeleton)

Chart imported from `llm-evaluation-service-deploy` and renamed for the EDD monorepo:

```bash
helm upgrade --install edd-platform ./deploy/charts/edd-platform \
  -f ./deploy/charts/edd-platform/values-local.yaml
```

Image tags and API/console/worker wiring will evolve with Phases 1–8. Treat this as a starting point, not production-ready config.
