# AISOC Backend

Poetry-managed FastAPI service for the AI Security Operations Platform.

```bash
cd backend
poetry install
poetry run uvicorn aisoc.main:create_app --factory --reload --port 8000
poetry run pytest
poetry run alembic upgrade head
```

Requires Postgres (or sqlite for tests), Redis, and optionally Qdrant. See root README for Compose.
