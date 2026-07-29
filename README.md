# AI Security Operations Platform (AISOC)

Enterprise-grade agentic SOC platform that unifies Graylog, Elasticsearch, Loki, Splunk, OpenSearch, and Datadog into an autonomous investigation workspace: multi-agent analysis, hybrid RAG, threat intel, human-in-the-loop approvals, and cloud-native ops.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────────────┐
│  React UI   │────▶│  FastAPI API │────▶│ LangGraph agents        │
│  (Vite)     │ SSE │  /api/v1     │     │ connectors · RAG · TI   │
└─────────────┘     └──────┬───────┘     └─────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Postgres           Redis            Qdrant
          │                │
          └────────┬───────┘
                   ▼
            Celery worker · MCP server
                   │
                   ▼
     OTel → Tempo / Loki · Prometheus → Grafana
```

| Layer | Stack |
|-------|--------|
| Frontend | React 19, TypeScript, Vite, Tailwind v4, React Flow, Cytoscape, Recharts |
| API | Python 3.13, FastAPI, SQLAlchemy async, Pydantic v2, Celery |
| Agents | LangGraph (sequential fallback), mock LLM when no keys |
| Data | Postgres, Redis, Qdrant |
| MCP | Separate FastAPI MCP tool server |
| Ops | Docker Compose, Helm, Terraform stubs, GitHub Actions |

## Quickstart (Docker Compose)

```bash
cp .env.example .env
docker compose up -d --build
# or: make up
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| MCP | http://localhost:8100 |
| Grafana | http://localhost:3002 (`admin` / `admin`) |
| Prometheus | http://localhost:9090 |
| Qdrant | http://localhost:6333 |

Health check: `curl http://localhost:8000/health`

## Local development (Poetry + Vite)

```bash
cp .env.example .env
make install

# API
cd backend && poetry run uvicorn aisoc.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Migrations / seed
make migrate
make seed
```

Connector mode defaults to `mock` (deterministic corpus with shared IOCs such as `185.220.101.45`). Set `CONNECTOR_MODE=live` when wiring real platforms.

## Demo credentials

From `.env.example`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@aisoc.local` | `ChangeMeAdmin123!` |
| Analyst | `analyst@aisoc.local` | `ChangeMeAnalyst123!` |

Password login works without OIDC. Optional mock issuer: `docker compose --profile oidc up`.

## API overview

Base path: `/api/v1`

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/login`, `/auth/refresh`, `/auth/logout`, `GET /auth/me`, OIDC helpers |
| Users / Admin | user listing, admin ops |
| Connectors | CRUD + parallel search health |
| Investigations | create, list, detail, agent runs |
| Chat | streaming investigation chat |
| Knowledge | RAG search / documents |
| Threat intel | IOC extract / lookup |
| Approvals | human-in-the-loop gates |
| Reports | export executive / technical |

Also: `GET /health`, `GET /ready`, `GET /metrics`.

OpenAPI: http://localhost:8000/docs

## MCP server

`mcp-server/` exposes SOC tools (search logs, timeline, IOC lookup, knowledge/runbook search, incident summary) authenticated with `MCP_API_TOKEN` against the API. See `mcp-server/README.md`.

## RAG & knowledge

Knowledge corpus lives under `knowledge/` (CVEs, incidents, policies, SOPs). Startup best-effort ingest loads into Qdrant (in-memory fallback when Qdrant is down). Hybrid search combines BM25-ish keyword scores with embeddings.

## Observability

Compose ships Prometheus, Grafana, Tempo, Loki, and the OTel collector. Configs under `observability/`. API emits Prometheus metrics and optional OTLP traces when `OTEL_ENABLED=true`.

## Infrastructure

| Path | Purpose |
|------|---------|
| `infra/helm/aisoc` | Helm chart (api, worker, frontend, mcp, ingress, HPA) |
| `infra/k8s` | Minimal namespace + API reference manifests |
| `infra/terraform` | Local env wiring; optional AWS VPC/RDS (`enable_cloud=false` by default) |
| `.github/workflows` | `ci.yml` (poetry/ruff/pytest, npm lint/build, docker build), `release.yml` (GHCR on `v*` tags) |

```bash
cd infra/terraform/environments/local
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform plan
```

## Testing

```bash
make test
# Backend only
cd backend && poetry run pytest -q
# Frontend e2e smoke
cd frontend && npx playwright install && npm run test:e2e
```

Backend coverage includes unit (security, RBAC, connectors, TI, LLM, RAG, agents), auth integration, and a golden brute-force/C2 investigation eval.

## Makefile targets

`make install` · `make test` · `make lint` · `make up` · `make down` · `make migrate`

## Phases status

All foundation phases **1–12** are marked **DONE** in [`PROGRESS.md`](./PROGRESS.md) (foundation through production deployment scaffolding).

## Future

Multi-tenancy, GraphRAG, Temporal workflows, autonomous remediation, SOAR plugins, multi-region, cost analytics dashboards, plugin SDK.
