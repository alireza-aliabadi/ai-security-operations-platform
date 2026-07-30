# Contributing to AISOC

## Setup

1. Copy `.env.example` → `.env`
2. `make install` (Poetry backend + npm frontend)
3. `make up` for the app docker-compose stack (`make up-obs` / `make up-all` for monitoring), or run API/frontend locally

## Development

- Backend: `cd backend && poetry run uvicorn aisoc.main:app --reload`
- Frontend: `cd frontend && npm run dev`
- Migrations: `make migrate`
- Seed: `make seed` or rely on API startup seed

## Checks before PR

```bash
make lint
make test
```

Optional: `cd frontend && npx playwright install && npm run test:e2e`

## Style

- Python: Ruff (line length 100), type hints preferred
- Frontend: TypeScript strict, Oxlint
- Prefer small, focused PRs; do not commit secrets or `.env`
