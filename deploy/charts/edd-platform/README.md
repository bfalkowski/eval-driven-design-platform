# edd-platform Helm Chart

Deploys the LLM evaluation service, optional background worker, and optional Streamlit
console to Kubernetes.

The chart is intentionally small. It covers the API Deployment, Service, ServiceAccount,
ConfigMap, optional Secret, optional demo Postgres, NetworkPolicy examples, optional
worker workload, optional console workload, and optional Ingress. It can also run
Alembic migrations as a Helm pre-install/pre-upgrade Job.

## Values Files

```text
values.yaml                Safe defaults and shared chart settings
values-local.yaml          Local cluster demo with in-cluster Postgres
values-dev.yaml            Managed-runtime example with external secrets
values-prod-example.yaml   Production-shaped example values
```

## Validate

```bash
helm lint charts/edd-platform

helm template edd-platform \
  charts/edd-platform \
  -f charts/edd-platform/values-local.yaml
```

The chart includes `values.schema.json`, so `helm lint` also validates common value
types and allowed options.

Render all provided values files:

```bash
helm template edd-platform charts/edd-platform \
  -f charts/edd-platform/values-local.yaml

helm template edd-platform charts/edd-platform \
  -f charts/edd-platform/values-dev.yaml

helm template edd-platform charts/edd-platform \
  -f charts/edd-platform/values-prod-example.yaml
```

## Local Install

`values-local.yaml` enables demo Postgres, creates demo Secret values, enables demo JWT
auth, runs migrations as a regular Kubernetes Job, runs the API and worker as separate
Deployments, and enables the companion Streamlit console.

```bash
helm upgrade --install edd-platform \
  charts/edd-platform \
  --namespace llm-evaluation \
  --create-namespace \
  -f charts/edd-platform/values-local.yaml
```

Check rollout:

```bash
kubectl -n llm-evaluation rollout status deployment/edd-platform
kubectl -n llm-evaluation rollout status deployment/edd-platform-worker
kubectl -n llm-evaluation get pods
```

Port-forward:

```bash
kubectl -n llm-evaluation port-forward service/edd-platform 8000:80
kubectl -n llm-evaluation port-forward service/edd-platform-console 8501:80
```

Test:

```bash
curl -s http://localhost:8000/health/ready
```

Expected response:

```json
{"status":"ready"}
```

Create a local demo bearer token from the service repository and use it for evaluation
requests or paste it into the console sidebar:

```bash
APP_AUTH_DEMO_SECRET=local-demo-secret \
python scripts/create_demo_jwt.py --tenant-id demo-tenant --subject local-user
```

Open the console at:

```text
http://localhost:8501
```

For the complete local platform flow, see `docs/local-platform.md` from the repository
root.

## Managed Runtime Install

Managed environments should provide secrets externally and use a managed Postgres
connection string. Do not enable demo Postgres outside local development.
For the full managed Kubernetes flow, see `docs/managed-kubernetes.md` from the
repository root.

Example with a pre-created Kubernetes Secret:

```bash
export APP_DATABASE_URL='<managed-postgres-connection-url>'
export APP_AUTH_DEMO_SECRET='<demo-auth-secret-for-non-production-only>'

kubectl -n llm-evaluation create secret generic edd-platform-secrets \
  --from-literal=APP_DATABASE_URL="$APP_DATABASE_URL" \
  --from-literal=APP_AUTH_DEMO_SECRET="$APP_AUTH_DEMO_SECRET"
```

The demo auth secret is suitable for local and non-production demonstration only.
Production deployments should use OIDC/JWKS or platform auth instead of the demo
shared-secret validator.

Install with the dev values and an immutable image tag:

```bash
helm upgrade --install edd-platform \
  charts/edd-platform \
  --namespace llm-evaluation \
  --create-namespace \
  -f charts/edd-platform/values-dev.yaml \
  --set image.tag=<service-full-commit-sha> \
  --set console.image.tag=<console-full-commit-sha>
```

## Database Migrations

`values-dev.yaml` and `values-prod-example.yaml` enable the migration Job:

```yaml
migrations:
  enabled: true
```

By default the Job runs as a Helm `pre-install,pre-upgrade` hook:

```text
alembic upgrade head
```

The application config sets:

```yaml
config:
  autoCreateSchema: false
```

That keeps schema changes as an explicit deployment step instead of relying on app
startup to create tables.

`values-local.yaml` runs migrations as a regular Kubernetes Job with Helm hooks disabled
because the demo Postgres Deployment may not be ready before a pre-install hook runs.
For a fresh local namespace, API pods may be ready before the migration Job completes;
wait for the migration Job before submitting evaluations.

## API And Worker Split

The chart can run evaluation processing in the API pods or in a separate worker
Deployment.

```yaml
worker:
  enabled: true
```

When `worker.enabled=true`, API pods run with `APP_PROCESS_ROLE=api` and worker pods run:

```text
python -m app.worker
```

Both workloads use the same service image, ConfigMap, Secret, and database. Keep
`worker.enabled=true` for managed environments where API replicas should stay focused on
request handling and worker replicas should process queued jobs.

## Image Tags

The service repo publishes:

```text
ghcr.io/bfalkowski/edd-platform-starter:latest
ghcr.io/bfalkowski/edd-platform-starter:<full-commit-sha>
```

The console repo publishes:

```text
ghcr.io/bfalkowski/edd-console:latest
ghcr.io/bfalkowski/edd-console:<full-commit-sha>
```

Use `latest` with `image.pullPolicy=Always` for quick local demos so the cluster does
not reuse a stale cached image. Use full commit SHA tags for managed runtime
deployments.

## Important Values

| Value | Purpose |
| --- | --- |
| `image.repository` | Container image repository |
| `image.tag` | Image tag to deploy |
| `replicaCount` | Number of API replicas |
| `service.annotations` | Optional Service annotations, including scrape metadata for `/metrics` |
| `config.environment` | Service environment label |
| `config.processRole` | Default service process role when no separate worker is enabled |
| `config.otelExporter` | `console`, `otlp`, or `none` |
| `config.otelOtlpEndpoint` | OTLP collector endpoint |
| `config.workerStaleJobSeconds` | Age threshold for worker recovery of stale `running` jobs |
| `config.autoCreateSchema` | Whether the app creates tables on startup |
| `config.authEnabled` | Require bearer-token auth for evaluation routes |
| `config.authIssuer` | Expected demo JWT issuer |
| `config.authAudience` | Expected demo JWT audience |
| `worker.enabled` | Render a separate worker Deployment and set API pods to API-only mode |
| `worker.replicaCount` | Number of worker replicas |
| `secrets.create` | Create a Kubernetes Secret from values |
| `secrets.authDemoSecret` | Local/demo HMAC secret for demo JWT auth |
| `secrets.existingSecretName` | Use an externally managed Secret |
| `migrations.enabled` | Render the Alembic migration Job |
| `postgresDemo.enabled` | Enable local demo Postgres |
| `networkPolicy.enabled` | Render NetworkPolicy resources |
| `ingress.enabled` | Render Ingress resource |
| `console.enabled` | Render the Streamlit console Deployment and Service |
| `console.image.tag` | Console image tag to deploy |
| `console.config.apiBaseUrl` | Optional API URL override; defaults to the in-cluster service URL |
| `console.ingress.enabled` | Render console Ingress resource |

## Cleanup

```bash
helm uninstall edd-platform --namespace llm-evaluation
kubectl delete namespace llm-evaluation
```

## Notes

- Secret values in `values-local.yaml` are only for local demos.
- Production deployments should replace demo JWT validation with OIDC/JWKS or platform auth.
- Managed environments should inject secrets through the platform or deployment pipeline.
- NetworkPolicy behavior depends on the cluster CNI.
- The chart does not install an OpenTelemetry Collector; it only configures the service to export to one.
